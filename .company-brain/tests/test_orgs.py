"""Organisations we work with: org pages, contact cards, the People Directory, People.base.

Upstream obsidian-second-brain keeps company entities next to people and an overview of everyone with
their company (references/bases/people.base.template). Here our own people stay profiles in
Company/Org/People (org chart, teams, works-on); customers, partners and vendors get org pages and their
people contact cards, and People.base is built from upstream's vendored template plus our overlay, so
upstream changes flow in on `brain upstream-check --copy` and `brain refresh`.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]
BRAIN = ENGINE.parent
sys.path.insert(0, str(ENGINE / "scripts"))

import brain as engine  # noqa: E402

TODAY = dt.date.today().isoformat()
DIRECTORY = Path("Company/Org/People Directory.md")
BASE = Path("Company/Org/People.base")


def cli(root: Path, *args: str):
    return subprocess.run([sys.executable, str(root / ".company-brain" / "scripts" / "brain.py"), "--root", str(root), *args],
                          capture_output=True, text=True, env=os.environ.copy())


def ok(root: Path, *args: str) -> str:
    r = cli(root, *args)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def block(path: Path, key: str) -> str:
    text = path.read_text(encoding="utf-8")
    return text.split(f"<!-- brain:auto:start {key} -->", 1)[1].split(f"<!-- brain:auto:end {key} -->", 1)[0]


@pytest.fixture()
def brain(tmp_path):
    dst = tmp_path / "brain"
    shutil.copytree(BRAIN, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.png", ".pytest_cache"))
    ok(dst, "init", "--company", "Acme", "--me", "Ana Lopez", "--role", "PM", "--team", "Platform")
    ok(dst, "person", "add", "Sam Lee", "--role", "VP Product", "--team", "Platform")
    ok(dst, "person", "add", "Jane Smith", "--role", "VP Engineering", "--company", "Globex", "--kind", "customer",
       "--owner", "Ana Lopez")
    ok(dst, "new", "company", "--title", "Initech", "--set", "kind=partner", "--set", "owner=[[Sam Lee]]")
    ok(dst, "person", "add", "Lena Wu", "--role", "Alliances", "--company", "[[Initech]]")
    ok(dst, "refresh")
    return dst


def test_contacts_and_org_pages_land_in_their_own_folders(brain):
    jane = engine.Note(brain, brain / "Company/Org/Contacts/Jane Smith.md")
    assert jane.type == "person" and jane.get("company") == "[[Globex]]" and jane.get("owner") == "[[Ana Lopez]]"
    globex = engine.Note(brain, brain / "Company/Org/Companies/Globex.md")
    assert globex.type == "company" and globex.get("kind") == "customer" and globex.layer == "company"
    assert not (brain / "Company/Org/People/Jane Smith.md").exists()
    ok(brain, "person", "add", "Tom Ops", "--role", "Ops", "--company", "Acme")  # our own company: a profile
    assert (brain / "Company/Org/People/Tom Ops.md").is_file()


def test_people_directory_lists_everyone_by_organisation(brain):
    text = block(brain / DIRECTORY, "people-directory")
    ours, customers, partners = text.index("### Acme ([[Organization]])"), text.index("### Customers"), text.index("### Partners")
    assert ours < customers < partners
    assert "- [[Sam Lee]] - VP Product, [[Platform]]" in text[ours:customers]
    assert "- [[Globex]]\n  - [[Jane Smith]] - VP Engineering" in text[customers:partners]
    assert "- [[Initech]] (owner on our side [[Sam Lee]])\n  - [[Lena Wu]] - Alliances" in text[partners:]
    people = block(brain / "Company/Org/Companies/Globex.md", "org-people")
    assert "- [[Jane Smith]] - VP Engineering (relationship owner [[Ana Lopez]])" in people


def test_contacts_never_reach_the_org_chart_teams_or_works_on(brain):
    chart = (brain / "Company/Org/Org Chart.md").read_text(encoding="utf-8")
    assert "Jane Smith" not in chart and "Lena Wu" not in chart
    assert [p.name for p in engine.profiles(engine.scan(brain))] == ["Ana Lopez", "Sam Lee"]
    r = cli(brain, "person", "works-on", "Jane Smith", "--project", "X", "--role", "owner", "--source", "Linear X",
            "--confidence", "high")
    assert r.returncode != 0 and "no profile matches" in r.stderr
    assert "Jane Smith" not in block(brain / "Company/Org/Organization.md", "work-map")


def test_people_base_is_upstreams_template_with_our_overlay(brain):
    text = (brain / BASE).read_text(encoding="utf-8")
    base = engine.parse_yaml(text)
    assert base["filters"]["and"][0] == {"or": ['file.inFolder("Company/Org/People")', 'file.inFolder("Company/Org/Contacts")']}
    assert base["formulas"]["days_since_update"].startswith("if(updated")  # upstream's formula, kept
    assert base["formulas"]["organization"] == 'if(company, company, "Acme")'
    order = base["views"][0]["order"]
    assert order[:4] == ["file.basename", "role", "formula.organization", "team"] and "company" not in order
    assert "Acme" not in (ENGINE / "references/bases/people.base.template").read_text(encoding="utf-8")


def test_an_upstream_change_flows_in_and_the_overlay_stays(brain):
    vendored = brain / ".company-brain/references/bases/people.base.template"
    newer = vendored.read_text(encoding="utf-8").replace("      - tags\n", "      - tags\n      - email\n")
    vendored.write_text(newer, encoding="utf-8")  # what `brain upstream-check --copy` would bring in
    ok(brain, "refresh")
    order = engine.parse_yaml((brain / BASE).read_text(encoding="utf-8"))["views"][0]["order"]
    assert "email" in order and "formula.organization" in order


def test_an_edit_made_in_obsidian_is_kept(brain):
    base = brain / BASE
    base.write_text(base.read_text(encoding="utf-8").replace("role: 150", "role: 240"), encoding="utf-8")
    assert "People.base" in ok(brain, "refresh") and "role: 240" in base.read_text(encoding="utf-8")
    base.unlink()
    ok(brain, "refresh")
    assert "role: 150" in base.read_text(encoding="utf-8")  # deleting it regenerates


def test_a_reshaped_upstream_template_falls_back_and_says_so(brain):
    (brain / ".company-brain/references/bases/people.base.template").write_text("views: []\n", encoding="utf-8")
    (brain / BASE).unlink()
    ok(brain, "refresh")
    base = engine.parse_yaml((brain / BASE).read_text(encoding="utf-8"))
    assert base["filters"]["and"][0]["or"]  # still a working base
    issues = json.loads(cli(brain, "--json", "check").stdout)
    assert any(i["severity"] == "warn" and "people.base.template" in i["message"] for i in issues)


def test_guards_cover_contacts_but_not_org_pages(brain):
    jane = brain / "Company/Org/Contacts/Jane Smith.md"
    jane.write_text(jane.read_text(encoding="utf-8") + "\n## What she cares about\n- Uptime\n", encoding="utf-8")
    initech = brain / "Company/Org/Companies/Initech.md"
    initech.write_text(initech.read_text(encoding="utf-8") + "\n## How we can help each other\n- Joint launches\n",
                       encoding="utf-8")
    errors = {i["path"] for i in json.loads(cli(brain, "--json", "check").stdout) if i["severity"] == "error"}
    assert "Company/Org/Contacts/Jane Smith.md" in errors  # a person: stakeholder content stays personal
    assert "Company/Org/Companies/Initech.md" not in errors  # an organisation: mutual value is a business fact


def test_check_warns_when_an_outsider_becomes_a_profile(brain):
    sam = brain / "Company/Org/People/Sam Lee.md"
    sam.write_text(sam.read_text(encoding="utf-8").replace("role: VP Product", 'role: VP Product\ncompany: "[[Globex]]"'),
                   encoding="utf-8")
    issues = json.loads(cli(brain, "--json", "check").stdout)
    assert any(i["path"] == "Company/Org/People/Sam Lee.md" and i["severity"] == "warn" and "contact card" in i["message"]
               for i in issues)


def test_stakeholder_note_for_a_contact_links_the_contact_card(brain):
    ok(brain, "new", "stakeholder", "--title", "Jane Smith")
    note = engine.Note(brain, brain / "Personal/Stakeholders/Stakeholder - Jane Smith.md")
    assert note.get("person") == "[[Jane Smith]]"


def test_the_brain_stays_clean_and_the_shipped_files_agree():
    assert engine.vendored_integrity(BRAIN) == []
    attrs = (BRAIN / ".gitattributes").read_text(encoding="utf-8")
    assert ".company-brain/references/bases/people.base.template -text" in attrs
    for kind in ("company", "contact"):
        assert (BRAIN / "Templates" / engine.KINDS[kind][0]).is_file()


def test_refresh_output_is_freshness_and_layer_clean(brain):
    assert engine.freshness_report(brain)["errors"] == 0
    assert cli(brain, "check", "--severity", "error").returncode == 0
    again = ok(brain, "refresh")  # idempotent: the second run rewrites nothing
    assert "unchanged Company/Org/People Directory.md" in again and "unchanged Company/Org/People.base" in again
