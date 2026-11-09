"""People: shared profiles, personal stakeholder notes, and who works on what.

Profiles carry the person sections obsidian-second-brain's person template had (what they care about,
how to work together), split by layer: what the person stated goes on the shared profile, my view of
them goes in a personal stakeholder note. Work is recorded from notes and, through
`brain person works-on`, from connected systems when the match is confident.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
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
ONB_URL = "https://linear.app/acme/project/onb"


def cli(root: Path, *args: str):
    return subprocess.run([sys.executable, str(root / ".company-brain" / "scripts" / "brain.py"), "--root", str(root), *args],
                          capture_output=True, text=True, env=os.environ.copy())


def ok(root: Path, *args: str) -> str:
    r = cli(root, *args)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


def fm(path: Path) -> dict:
    return engine.split_frontmatter(path.read_text(encoding="utf-8"))[0]


def block(path: Path, key: str = "works-on") -> str:
    text = path.read_text(encoding="utf-8")
    return text.split(f"<!-- brain:auto:start {key} -->", 1)[1].split(f"<!-- brain:auto:end {key} -->", 1)[0]


@pytest.fixture()
def brain(tmp_path):
    dst = tmp_path / "brain"
    shutil.copytree(BRAIN, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.png", ".pytest_cache"))
    ok(dst, "init", "--company", "Acme", "--me", "Ana Lopez", "--role", "PM", "--team", "Platform", "--sharing", "git")
    ok(dst, "person", "add", "Sam Lee", "--role", "VP Product", "--team", "Platform",
       "--email", "sam@acme.com", "--handle", "github:samlee", "--alias", "Sammy")
    ok(dst, "new", "project", "--layer", "team", "--team", "Platform", "--title", "Onboarding revamp",
       "--set", "owner=[[Ana Lopez]]", "--set", 'refs=["linear:ONB"]')
    return dst


SAM = Path("Company/Org/People/Sam Lee.md")
ANA = Path("Company/Org/People/Ana Lopez.md")
ONB = Path("Teams/Platform/Projects/Onboarding revamp.md")


def works_on(root: Path, person: str, project: str, *extra: str, role: str = "contributor",
             source: str = f"Linear project ONB, {ONB_URL}", confidence: str = "high"):
    args = ["person", "works-on", person, "--project", project, "--source", source, "--confidence", confidence]
    if role:
        args += ["--role", role]
    return cli(root, *args, *extra)


# --- what a profile records ------------------------------------------------------------------------

def test_profile_template_carries_the_upstream_person_sections_split_by_layer():
    person = (BRAIN / "Templates" / "Person Template.md").read_text(encoding="utf-8")
    for heading in ("## What they care about", "## How to work with them", "## Works on", "## Shared meetings",
                    "## My notes on them"):
        assert heading in person
    for key in ("email:", "aliases:", "handles:", "works_on: []"):
        assert re.search(rf"^{re.escape(key)}", person, re.M), key
    assert "<!-- brain:auto:start works-on -->" in person
    assert "## Private" not in person  # a shared note never has one
    stake = (BRAIN / "Templates" / "Stakeholder Template.md").read_text(encoding="utf-8")
    for heading in ("## What they care about", "## How we can help each other", "## How to work with them",
                    "## Open asks", "## Interactions", "## Private"):
        assert heading in stake
    for key in ("relationship", "influence", "interest", "last_interaction", "follow_up"):
        assert re.search(rf"^{key}: TBD$", stake, re.M), key


def test_person_add_records_the_identifiers_matching_relies_on(brain):
    meta = fm(brain / SAM)
    assert meta["email"] == "sam@acme.com" and meta["handles"] == ["github:samlee"] and meta["aliases"] == ["Sammy"]
    assert meta["works_on"] == []


def test_stakeholder_notes_are_personal_and_point_up_to_the_profile(brain):
    ok(brain, "new", "stakeholder", "--title", "Sam Lee", "--layer", "company")  # the layer cannot be overridden
    note = brain / "Personal" / "Stakeholders" / "Stakeholder - Sam Lee.md"
    meta = fm(note)
    assert meta["layer"] == "personal" and meta["type"] == "stakeholder" and meta["person"] == "[[Sam Lee]]"
    ok(brain, "new", "stakeholder", "--title", "Carla Customer")  # no profile: the plain name, no dangling link
    assert fm(brain / "Personal" / "Stakeholders" / "Stakeholder - Carla Customer.md")["person"] == "Carla Customer"
    assert (brain / "Personal" / "Stakeholders" / "My Stakeholders.md").is_file()  # the map ships with init
    r = cli(brain, "promote", "Personal/Stakeholders/Stakeholder - Sam Lee.md", "--to", "company")
    assert r.returncode != 0 and "stakeholder notes" in (r.stdout + r.stderr)


# --- who works on what -----------------------------------------------------------------------------

def test_works_on_matches_by_email_and_project_ref_and_renders_everywhere(brain):
    r = works_on(brain, "sam@acme.com", "linear:ONB", role="reviewer")
    assert r.returncode == 0, r.stderr
    entry = fm(brain / SAM)["works_on"][0]
    assert entry["project"] == "[[Onboarding revamp]]" and entry["role"] == "reviewer"
    assert entry["confidence"] == "high" and entry["until"] == "present" and entry["learned"] == TODAY
    assert ONB_URL in entry["source"]
    ok(brain, "refresh")
    assert "[[Onboarding revamp]] - reviewer (high confidence; Linear project ONB" in block(brain / SAM)
    assert "[[Onboarding revamp]] - owner (project note" in block(brain / ANA)
    work_map = block(brain / "Company" / "Org" / "Organization.md", "work-map")
    assert "- [[Onboarding revamp]]: [[Ana Lopez]] (owner), [[Sam Lee]] (reviewer)" in work_map


def test_work_with_no_project_note_is_still_registered(brain):
    assert works_on(brain, "github:samlee", "Billing migration", role="lead",
                    source="GitHub repo acme/billing, https://github.com/acme/billing").returncode == 0
    assert fm(brain / SAM)["works_on"][0]["project"] == "Billing migration"  # plain text, not a dangling link
    ok(brain, "refresh")
    assert "- Billing migration - lead (" in block(brain / SAM) and "no project note yet" in block(brain / SAM)
    assert "Billing migration: [[Sam Lee]] (lead)" in block(brain / "Company" / "Org" / "Organization.md", "work-map")
    # once a project note answers to that name, the same entry links to it
    ok(brain, "new", "project", "--layer", "team", "--team", "Platform", "--title", "Billing",
       "--set", "owner=[[Sam Lee]]", "--set", 'aliases=["Billing migration"]')
    ok(brain, "refresh")
    assert "[[Billing]] - lead" in block(brain / SAM) and "no project note yet" not in block(brain / SAM)


def test_below_the_confidence_threshold_nothing_is_written(brain):
    before = (brain / SAM).read_text(encoding="utf-8")
    r = works_on(brain, "Sam Lee", "Data lake", confidence="medium", source="Slack #data")
    assert r.returncode == 5 and "below this brain's threshold (high" in r.stdout
    assert (brain / SAM).read_text(encoding="utf-8") == before
    cfg = brain / "brain.yaml"
    cfg.write_text(cfg.read_text(encoding="utf-8").replace("works_on_min_confidence: high", "works_on_min_confidence: medium"),
                   encoding="utf-8")
    assert works_on(brain, "Sam Lee", "Data lake", confidence="medium", source="Slack #data").returncode == 0
    assert works_on(brain, "Sam Lee", "Data lake", confidence="low", source="Slack #data").returncode == 5


def test_works_on_history_is_append_only(brain):
    works_on(brain, "Sam Lee", "Onboarding revamp", role="contributor")
    assert works_on(brain, "Sammy", "Onboarding revamp", role="contributor").returncode == 0  # re-confirmed
    assert len(fm(brain / SAM)["works_on"]) == 1
    assert works_on(brain, "Sam Lee", "Onboarding revamp", role="lead").returncode == 0  # stronger role
    entries = fm(brain / SAM)["works_on"]
    assert [(e["role"], e["until"]) for e in entries] == [("contributor", TODAY), ("lead", "present")]
    before = (brain / SAM).read_text(encoding="utf-8")
    r = works_on(brain, "Sam Lee", "Onboarding revamp", role="reviewer")  # weaker signal: kept, not downgraded
    assert r.returncode == 0 and r.stdout.startswith("kept:") and (brain / SAM).read_text(encoding="utf-8") == before
    assert works_on(brain, "Sam Lee", "Onboarding revamp", "--replace", role="reviewer").returncode == 0
    assert works_on(brain, "Sam Lee", "Onboarding revamp", "--ended", role="", source="Linear project ONB archived").returncode == 0
    entries = fm(brain / SAM)["works_on"]
    assert len(entries) == 3 and all(e["until"] == TODAY for e in entries)  # all history kept, all closed
    ok(brain, "refresh")
    assert "### Past" in block(brain / SAM) and "### Current" not in block(brain / SAM)


def test_works_on_refuses_guesses_about_identity_and_private_sources(brain):
    one_on_one = brain / "Personal" / "1-1s" / "1-1 - Sam Lee.md"
    ok(brain, "new", "one-on-one", "--title", "Sam Lee", "--set", "person=[[Sam Lee]]")
    assert one_on_one.is_file()
    r = works_on(brain, "Sam Lee", "Onboarding revamp", source="said in [[1-1 - Sam Lee]]")
    assert r.returncode != 0 and "personal note" in r.stderr
    r = works_on(brain, "S. Lee", "Onboarding revamp")
    assert r.returncode != 0 and "no profile matches" in r.stderr
    assert not (brain / "Company" / "Org" / "People" / "S. Lee.md").exists()
    assert works_on(brain, "dana@acme.com", "X", "--create").returncode != 0  # --create needs a full name
    assert works_on(brain, "Dana Wu", "Onboarding revamp", "--create").returncode == 0
    assert fm(brain / "Company" / "Org" / "People" / "Dana Wu.md")["works_on"][0]["project"] == "[[Onboarding revamp]]"
    r = works_on(brain, "Sam Lee", "Onboarding revamp", role="boss")
    assert r.returncode != 0


def test_shared_profiles_never_reflect_personal_projects(brain):
    ok(brain, "new", "project", "--layer", "personal", "--title", "Side quest", "--set", "owner=[[Sam Lee]]")
    assert works_on(brain, "Sam Lee", "Side quest").returncode == 0
    assert fm(brain / SAM)["works_on"][0]["project"] == "Side quest"  # not linked to the Personal note
    ok(brain, "refresh")
    assert "[[Side quest]]" not in (brain / SAM).read_text(encoding="utf-8")
    assert cli(brain, "check", "--severity", "error").returncode == 0


def test_project_people_tables_and_okr_owners_feed_profiles(brain):
    onb = brain / ONB
    onb.write_text(onb.read_text(encoding="utf-8").replace("| Contributors | TBD |", "| Contributors | [[Sam Lee]] |"),
                   encoding="utf-8")
    period = engine.whoami(brain)["period"]["quarter"]
    obj = brain / "Teams" / "Platform" / "OKRs" / f"{period} - Platform - O1 - Faster onboarding.md"
    obj.parent.mkdir(parents=True, exist_ok=True)
    obj.write_text(f"---\ndate: {TODAY}\ntype: objective\ntags: [objective]\nai-first: true\nlayer: team\nteam: \"[[Platform]]\"\n"
                   f"level: team\nperiod: {period}\nowner: \"[[Ana Lopez]]\"\nstatus: on-track\n---\n\n# x\n\n## For future agent\nTest.\n\n"
                   "## Key results\n- **KR1** Time to first board [progress:: 0.4] [owner:: [[Sam Lee]]] ^kr1\n", encoding="utf-8")
    done = brain / "Company" / "Projects" / "Legacy import.md"
    ok(brain, "new", "project", "--title", "Legacy import", "--set", "owner=[[Sam Lee]]", "--set", "status=completed")
    assert done.is_file()
    ok(brain, "refresh")
    sam = block(brain / SAM)
    assert "[[Onboarding revamp]] - contributor (project note" in sam
    assert f"[[{obj.stem}#^kr1]] - key result owner (KR1, {period})" in sam
    assert sam.index("### Past") < sam.index("[[Legacy import]] - owner (project note, completed")
    assert f"[[{obj.stem}]] - objective owner" in block(brain / ANA)


def test_refresh_migrates_legacy_profiles_and_is_idempotent(brain):
    legacy = brain / "Company" / "Org" / "People" / "Old Timer.md"
    legacy.write_text(f"---\ndate: {TODAY}\ntype: person\ntags: [person]\nai-first: true\nlayer: company\nrole: Engineer\n"
                      "team: \"[[Platform]]\"\nmanager: \"[[Sam Lee]]\"\n---\n\n# Old Timer\n\n## For future agent\nOld.\n\n"
                      "## Works on\n```dataview\nLIST FROM \"Company\" OR \"Teams\"\nWHERE (type = \"project\" AND "
                      "contains(string(owner), this.file.name)) OR (type = \"objective\" AND contains(string(owner), "
                      "this.file.name))\n```\nHand-written note kept.\n\n## Reports\n- none\n", encoding="utf-8")
    ok(brain, "refresh")
    text = legacy.read_text(encoding="utf-8")
    assert "contains(string(owner), this.file.name)" not in text and "Hand-written note kept." in text
    assert engine.LIVE_WORKS_ON in text  # the legacy query became the live, link-matched one
    assert text.index("## Works on") < text.index("<!-- brain:auto:start works-on -->") < text.index("## Reports")
    assert "Old Timer.md" not in ok(brain, "refresh")  # second run changes nothing


def test_upgrade_adds_what_profiles_lack_and_only_on_yes(brain):
    legacy = brain / "Company" / "Org" / "People" / "Old Timer.md"
    legacy.write_text(f"---\ndate: {TODAY}\ntype: person\ntags: [person]\nai-first: true\nlayer: company\nrole: Engineer\n---\n\n"
                      "# Old Timer\n\n## For future agent\nOld.\n\n## Role and responsibilities\n- Builds things\n", encoding="utf-8")
    before = legacy.read_text(encoding="utf-8")
    out = ok(brain, "person", "upgrade", "Old Timer")
    assert "Would upgrade 1 of 1" in out and "## What they care about" in out
    assert legacy.read_text(encoding="utf-8") == before
    ok(brain, "person", "upgrade", "--yes")
    text = legacy.read_text(encoding="utf-8")
    assert "- Builds things" in text and "role: Engineer" in text
    assert text.index("## Role and responsibilities") < text.index("## What they care about") < text.index("## Works on")
    assert fm(legacy)["works_on"] == [] and fm(legacy)["email"] == "TBD"
    assert "Would upgrade 0" in ok(brain, "person", "upgrade")  # idempotent


def test_check_flags_personal_types_in_shared_folders_and_weak_entries(brain):
    leaked = brain / "Company" / "Knowledge" / "Stakeholder - Sam Lee.md"
    leaked.write_text(f"---\ndate: {TODAY}\ntype: stakeholder\ntags: [stakeholder]\nai-first: true\nlayer: company\n---\n\n"
                      "# x\n\n## For future agent\nWrong place.\n", encoding="utf-8")
    sam = brain / SAM
    sam.write_text(sam.read_text(encoding="utf-8").replace("works_on: []", "works_on:\n  - project: Guess\n    role: lead\n"
                                                           "    confidence: medium"), encoding="utf-8")
    issues = json.loads(cli(brain, "--json", "check").stdout)
    msgs = {(i["severity"], i["path"], i["message"].split(" ")[0]) for i in issues}
    assert ("error", "Company/Knowledge/Stakeholder - Sam Lee.md", "`type:") in msgs
    sam_msgs = [i["message"] for i in issues if i["path"] == SAM.as_posix()]
    assert any("has no `source:`" in m for m in sam_msgs) and any("below this brain's threshold" in m for m in sam_msgs)


def test_generated_people_views_pass_freshness_and_layer_checks(brain):
    works_on(brain, "Sam Lee", "linear:XYZ", source="Linear project XYZ linear:XYZ")  # id-shaped names and sources
    ok(brain, "refresh")
    assert "`linear:XYZ`" in block(brain / SAM)  # ids render as code, which the freshness lint skips
    report = engine.freshness_report(brain)
    assert report["errors"] == 0, report["findings"]
    assert cli(brain, "check", "--severity", "error").returncode == 0


# --- the rules are written down where agents read them --------------------------------------------

def test_kinds_in_the_manual_match_the_cli():
    manual = (BRAIN / "CLAUDE.md").read_text(encoding="utf-8")
    listed = re.search(r"Kinds for `new`: ([a-z, -]+)\.", manual).group(1)
    assert sorted(k.strip() for k in listed.split(",")) == sorted(engine.KINDS)


def test_org_skill_spells_out_detection_confidence_and_privacy():
    text = (ENGINE / "skills" / "org" / "SKILL.md").read_text(encoding="utf-8")
    for needle in ("brain person works-on", "works_on_min_confidence", "exits 5", "--create", "a DM, an email",
                   "brain new stakeholder", "brain person upgrade", "refs:"):
        assert needle in text, needle
    for skill in ("meeting", "weekly", "ingest"):
        assert "works-on rules" in (ENGINE / "skills" / skill / "SKILL.md").read_text(encoding="utf-8"), skill


# --- review fixes: each case below was a bug once --------------------------------------------------

def test_dry_run_writes_nothing_even_with_create(brain):
    before = (brain / SAM).read_text(encoding="utf-8")
    out = ok(brain, "person", "works-on", "Sam Lee", "--project", "Onboarding revamp", "--role", "lead",
             "--source", "Linear project ONB", "--confidence", "high", "--dry-run")
    assert out.startswith("would record") and (brain / SAM).read_text(encoding="utf-8") == before
    out = ok(brain, "person", "works-on", "Dana Wu", "--project", "X", "--role", "owner", "--source", "Linear X",
             "--confidence", "high", "--create", "--dry-run")
    assert "created the profile" in out and not (brain / "Company" / "Org" / "People" / "Dana Wu.md").exists()


def test_create_refuses_a_name_another_note_already_has(brain):
    other = brain / "Company" / "Knowledge" / "Eve Park.md"
    other.write_text(f"---\ndate: {TODAY}\ntype: knowledge\ntags: [knowledge]\nai-first: true\nlayer: company\n---\n\n"
                     "# Eve Park\n\n## For future agent\nNot a profile.\n", encoding="utf-8")
    r = works_on(brain, "Eve Park", "Onboarding revamp", "--create")
    assert r.returncode == 1 and "Company/Knowledge/Eve Park.md already has that name" in r.stderr
    assert "Traceback" not in r.stderr


def test_sources_with_backslashes_stay_valid_yaml(brain):
    yaml = pytest.importorskip("yaml")
    source = 'Drive C:\\new\\folder "Q4" end\\'
    assert works_on(brain, "Sam Lee", "Onboarding revamp", source=source).returncode == 0
    head = (brain / SAM).read_text(encoding="utf-8").split("---\n")[1]
    stored = yaml.safe_load(head)["works_on"][0]["source"]
    assert stored == source.replace('"', "'") == fm(brain / SAM)["works_on"][0]["source"]


def test_ending_a_role_that_is_not_open_ends_nothing(brain):
    works_on(brain, "Sam Lee", "Onboarding revamp", "--since", "2026-09-01", role="lead")
    r = works_on(brain, "Sam Lee", "Onboarding revamp", "--ended", role="reviewer")
    assert r.returncode == 3 and "no open reviewer works_on entry" in r.stdout
    assert fm(brain / SAM)["works_on"][0]["until"] == "present"
    assert works_on(brain, "Sam Lee", "Onboarding revamp", "--ended", "--until", "2026-10-31", role="lead").returncode == 0
    entry = fm(brain / SAM)["works_on"][0]
    assert (entry["from"], entry["until"]) == ("2026-09-01", "2026-10-31")


def test_stakeholder_note_by_alias_is_named_after_the_person(brain):
    assert "Stakeholder - Sam Lee.md" in ok(brain, "new", "stakeholder", "--title", "Sammy")
    r = cli(brain, "new", "stakeholder", "--title", "Sam Lee")
    assert r.returncode == 3 and "exists" in r.stdout  # one note per person, whatever name is used


def test_every_co_owner_gets_the_work(brain):
    ok(brain, "new", "project", "--title", "Shared thing", "--set", 'owner=["[[Ana Lopez]]", "[[Sam Lee]]"]')
    note = brain / "Company" / "Projects" / "Shared thing.md"
    note.write_text(re.sub(r"\| Owner \|.*\|", "| Owner | TBD |", note.read_text(encoding="utf-8")), encoding="utf-8")
    ok(brain, "refresh")
    assert "[[Shared thing]] - owner" in block(brain / SAM) and "[[Shared thing]] - owner" in block(brain / ANA)


def test_an_ambiguous_old_entry_does_not_block_new_recordings(brain):
    works_on(brain, "Sam Lee", "Onboarding")  # no note yet: kept as plain text
    for team_project in ("Onboarding web", "Onboarding app"):
        ok(brain, "new", "project", "--title", team_project, "--set", "owner=[[Ana Lopez]]", "--set", 'aliases=["Onboarding"]')
    assert works_on(brain, "Sam Lee", "Onboarding revamp", role="lead").returncode == 0


def test_brains_with_older_templates_still_work(brain):
    (brain / "Templates" / "Stakeholder Template.md").unlink()  # set up before the template existed
    ok(brain, "new", "stakeholder", "--title", "Sam Lee")  # falls back to the engine's copy
    old = brain / "Templates" / "Person Template.md"
    old.write_text(old.read_text(encoding="utf-8").split("## What they care about")[0], encoding="utf-8")
    assert "warning: Templates/Person Template.md lacks the engine's sections" in ok(brain, "person", "upgrade")


def test_the_shared_hub_names_nobody_for_having_no_work(brain):
    ok(brain, "refresh")
    assert "Sam Lee" not in block(brain / "Company" / "Org" / "Organization.md", "work-map")
    issues = json.loads(cli(brain, "--json", "check").stdout)
    assert any(i["path"] == SAM.as_posix() and i["severity"] == "info" and "no current work recorded" in i["message"]
               for i in issues)


def test_upgrade_keeps_the_profile_spacing(brain):
    legacy = brain / "Company" / "Org" / "People" / "Old Timer.md"
    legacy.write_text(f"---\ndate: {TODAY}\ntype: person\ntags: [person]\nai-first: true\nlayer: company\n---\n\n"
                      "# Old Timer\n\n## For future agent\nOld.\n\n## Role and responsibilities\n```\na\n\n\n\nb\n```\n",
                      encoding="utf-8")
    ok(brain, "person", "upgrade", "--yes")
    assert "```\na\n\n\n\nb\n```" in legacy.read_text(encoding="utf-8")
