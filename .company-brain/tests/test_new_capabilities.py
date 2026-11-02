"""The capabilities brought in from obsidian-second-brain, run the way a brain uses them.

The vendored upstream tests cover the scripts on their own. These cover what is ours: the skills that
drive them, the layers and privacy rules around them, and the places where this layout differs from
upstream's (see conftest.py for the upstream tests that are skipped on purpose).
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
SCRIPTS = ENGINE / "scripts"


@pytest.fixture()
def brain(tmp_path):
    dst = tmp_path / "brain"
    shutil.copytree(BRAIN, dst, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.png", ".pytest_cache"))
    return dst


def cli(root: Path, *args: str, env: dict | None = None):
    engine = root / ".company-brain" / "scripts" / "brain.py"
    return subprocess.run([sys.executable, str(engine), "--root", str(root), *args],
                          capture_output=True, text=True, env={**os.environ, **(env or {})})


def script(root: Path, name: str, *args: str, stdin: str | None = None, env: dict | None = None):
    return subprocess.run([sys.executable, str(root / ".company-brain" / "scripts" / name), *args],
                          input=stdin, capture_output=True, text=True, env={**os.environ, **(env or {})})


def gitignore_lines() -> list:
    return (BRAIN / ".gitignore").read_text(encoding="utf-8").splitlines()


def write_note(path: Path, body: str = "Test.", **fm) -> Path:
    fields = {"date": dt.date.today().isoformat(), "type": "knowledge", "tags": "[knowledge]",
              "ai-first": "true", "layer": "personal", **fm}
    head = "\n".join(f"{k}: {v}" for k, v in fields.items())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{head}\n---\n\n# {path.stem}\n\n## For future agent\n{body}\n", encoding="utf-8")
    return path


# --- skills, catalog and the scripts they name ------------------------------------------------------

def skill_names() -> list:
    return sorted(p.name for p in (ENGINE / "skills").iterdir() if (p / "SKILL.md").is_file())


def test_skill_list_catalog_and_folders_agree():
    manual = (BRAIN / "CLAUDE.md").read_text(encoding="utf-8")
    listed = re.search(r"## 4\. Skills.*?\n\n([a-z, -]+)\.\n", manual, re.S).group(1)
    in_manual = sorted(n.strip() for n in listed.split(","))
    catalog = (BRAIN / "System" / "Skills.md").read_text(encoding="utf-8")
    in_catalog = sorted(re.findall(r"^\| `/company-brain:([a-z-]+)`", catalog, re.M))
    assert skill_names() == in_manual == in_catalog


def test_every_skill_has_matching_front_matter():
    for name in skill_names():
        text = (ENGINE / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        head = re.match(r"---\nname: (.+)\ndescription: (.+)\n---", text)
        assert head and head.group(1) == name and len(head.group(2)) > 40, name


def test_scripts_named_in_skills_exist():
    missing = []
    for name in skill_names():
        text = (ENGINE / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
        for script_name in set(re.findall(r"scripts/([a-z_]+\.py)", text)):
            if not (SCRIPTS / script_name).is_file():
                missing.append(f"{name}: {script_name}")
    assert not missing, missing


# --- check-in ---------------------------------------------------------------------------------------

def old_project(root: Path, title: str = "Onboarding revamp", **fm) -> str:
    path = write_note(root / "Teams" / "Platform" / "Projects" / f"{title}.md", "A project.", type="project",
                      tags="[project]", layer="team", team='"[[Platform]]"', status="active", **fm)
    path.write_text(path.read_text(encoding="utf-8").replace(dt.date.today().isoformat(), "2000-01-15", 1), encoding="utf-8")
    return path.relative_to(root).as_posix()


def test_checkin_round_trip_stamps_the_note_and_keeps_state_private(brain):
    rel = old_project(brain)
    c = lambda *a: script(brain, "checkin.py", "--path", str(brain), *a)  # noqa: E731
    picked = json.loads(c("pick", "--types", "person,project,team").stdout)
    assert [p["note"] for p in picked] == [rel]
    assert c("ask", "--note", rel, "--fact", "Status is active").returncode == 0
    assert "Onboarding revamp" in c("message").stdout
    assert c("done", "--number", "1", "--outcome", "same").returncode == 0
    assert f"last-checked: {dt.date.today().isoformat()}" in (brain / rel).read_text(encoding="utf-8")
    assert json.loads(c("pick", "--types", "person,project,team").stdout) == []  # quiet for 14 days
    assert "/.checkin.json" in gitignore_lines() and (brain / ".checkin.json").is_file()


def test_checkin_never_asks_about_the_engine_or_mounted_sources(brain):
    old = {"type": "project", "tags": "[project]", "layer": "company"}
    for rel in (".company-brain/references/old-project.md", "Sources/Drive/old-project.md"):
        path = write_note(brain / rel, **old)
        path.write_text(path.read_text(encoding="utf-8").replace(dt.date.today().isoformat(), "2000-01-15", 1), encoding="utf-8")
    out = script(brain, "checkin.py", "--path", str(brain), "pick", "--types", "project")
    assert json.loads(out.stdout) == []


def test_checkin_skill_limits_scope_and_keeps_facts_work_only():
    text = (ENGINE / "skills" / "checkin" / "SKILL.md").read_text(encoding="utf-8")
    assert "`owner:` is me" in text and "health, compensation" in text and "gitignored" in text


# --- check_notes in a brain -------------------------------------------------------------------------

def test_check_notes_fails_then_fixes_prose_in_a_brain(brain):
    write_note(brain / "Personal" / "Notes" / "Dashy.md", "A note — with a dash.")
    failed = script(brain, "check_notes.py", "--path", str(brain), "Personal/Notes/Dashy.md")
    assert failed.returncode == 1 and "em-dash" in failed.stdout
    fixed = script(brain, "check_notes.py", "--path", str(brain), "--fix", "Personal/Notes/Dashy.md")
    assert fixed.returncode == 0 and "—" not in (brain / "Personal/Notes/Dashy.md").read_text(encoding="utf-8")


# --- reconcile --------------------------------------------------------------------------------------

def test_quote_checker_rejects_a_claim_it_cannot_find(brain):
    write_note(brain / "Company" / "Knowledge" / "Claim.md", "We serve enterprise customers only.")
    good = {"path": "Company/Knowledge/Claim.md", "line": 8, "quote": "We serve enterprise customers only."}
    bad = {**good, "quote": "We serve every kind of customer."}
    assert script(brain, "verify_quotes.py", "--path", str(brain), stdin=json.dumps([good])).returncode == 0
    r = script(brain, "verify_quotes.py", "--path", str(brain), stdin=json.dumps([good, bad]))
    assert r.returncode == 1 and json.loads(r.stdout)[1]["ok"] is False


def test_reconcile_skill_proves_before_acting_and_protects_approved_text():
    text = (ENGINE / "skills" / "reconcile" / "SKILL.md").read_text(encoding="utf-8")
    assert "verify_quotes.py" in text and "Dropped as unproven" in text
    assert "never auto-resolve" in text and "brain new decision" in text


# --- crew -------------------------------------------------------------------------------------------

def test_crew_writes_into_personal_and_never_into_the_shared_vault(brain):
    folder = brain / "Personal" / "Crew"
    env = {"COMPANY_BRAIN_PATH": str(brain)}
    env.pop("CREW_DIR", None)
    r = script(brain, "crew.py", "--dir", str(folder), "add", "--agent", "claude", "--area", "side",
               "--did", "Wrote 2 tests", "--where", "tests/x.py", env=env)
    assert r.returncode == 0, r.stderr
    assert list(folder.glob("*.md")) and not (brain / "wiki").exists()
    assert "/Personal/" in gitignore_lines()  # the whole personal layer, Crew included, stays out of git


def test_crew_skill_always_passes_dir_and_asks_before_touching_outside_config():
    text = (ENGINE / "skills" / "crew" / "SKILL.md").read_text(encoding="utf-8")
    assert '--dir "<brain>/Personal/Crew"' in text
    assert "outside this repository" in text and "explicit yes" in text


# --- folder ingestion -------------------------------------------------------------------------------

def test_folder_ingestion_resolves_the_mount_and_resumes(brain, tmp_path):
    pytest.importorskip("yaml")
    real = tmp_path / "drive" / "docs"
    real.mkdir(parents=True)
    (real / "a.md").write_text("# Plan\nWe ship in Q3.\n", encoding="utf-8")
    (real / "b.txt").write_text("hello\n", encoding="utf-8")
    (brain / "Sources").mkdir(exist_ok=True)
    (brain / "Sources" / "Docs").symlink_to(real, target_is_directory=True)
    ib = lambda *a, **k: script(brain, "ingest_batch.py", "--vault", str(brain), "--raw-root", "Personal/Notes", *a, **k)  # noqa: E731

    refused = ib("discover", str(brain / "Sources" / "Docs"))
    assert refused.returncode == 1 and "Linked paths are not supported" in refused.stderr

    folder = str(real.resolve())
    plan = json.loads(ib("plan", folder, "--allow", folder).stdout)
    names = [Path(b["source_path"]).name for b in plan["batch"]]
    assert names == ["a.md", "b.txt"]
    first = plan["batch"][0]

    made = cli(brain, "new", "knowledge", "--layer", "personal", "--title", "Plan doc", "--set", "type=source",
               "--set", f"source_path={first['source_path']}", "--set", f"source_file_hash={first['source_file_hash']}")
    assert made.returncode == 0, made.stderr
    receipt = json.dumps({"source_path": first["source_path"], "source_file_hash": first["source_file_hash"],
                          "raw_path": "Personal/Notes/Plan doc.md"})
    assert ib("complete", stdin=receipt).returncode == 0
    assert "ingest-complete" in (brain / "log.md").read_text(encoding="utf-8")
    assert "/log.md" in gitignore_lines()  # receipts stay local

    again = json.loads(ib("plan", folder, "--allow", folder).stdout)
    assert [Path(s["source_path"]).name for s in again["skipped"]] == ["a.md"]
    assert [Path(b["source_path"]).name for b in again["batch"]] == ["b.txt"]

    (real / "a.md").write_text("# Plan\nWe ship in Q4.\n", encoding="utf-8")  # the source changed
    changed = json.loads(ib("plan", folder, "--allow", folder).stdout)
    assert "a.md" in [Path(b["source_path"]).name for b in changed["batch"]]


def test_source_notes_pass_brain_check(brain):
    made = cli(brain, "new", "knowledge", "--layer", "personal", "--title", "Captured file", "--set", "type=source",
               "--set", "source_path=/somewhere/file.md", "--set", f"source_file_hash={'a' * 64}")
    assert made.returncode == 0, made.stderr
    assert cli(brain, "check", "--severity", "error").returncode == 0


def test_ingest_skill_documents_the_symlink_and_capture_rules():
    text = (ENGINE / "skills" / "ingest" / "SKILL.md").read_text(encoding="utf-8")
    assert "readlink -f" in text and "type: source" in text and "document_to_pdf.py" in text


# --- search -----------------------------------------------------------------------------------------

def test_brain_search_prints_json_without_an_agent(brain):
    r = cli(brain, "search", "mission", "--limit", "2", "--lexical")
    assert r.returncode == 0, r.stderr
    results = json.loads(r.stdout)
    assert isinstance(results, list) and results and "path" in results[0]
