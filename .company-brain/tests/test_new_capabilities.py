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
sys.path.insert(0, str(SCRIPTS))
import brain as brain_cli  # noqa: E402  (the module; `brain` is the fixture below)


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
        head = re.match(r'---\nname: (.+)\ndescription: (.+)\n(argument-hint: "[^"\n]+"\n)?---', text)
        assert head and head.group(1) == name and len(head.group(2)) > 40, name


# Project slash commands: Claude Code opened in the brain gets /company-brain:<name> from
# .claude/commands/company-brain/ without the plugin (and in cloud sessions, which load no plugins).
# `./brain commands` generates them from the skills, so they cannot drift.
COMMANDS = BRAIN / ".claude" / "commands" / "company-brain"


def test_slash_commands_are_generated_from_the_skills():
    r = cli(BRAIN, "commands", "--check")
    assert r.returncode == 0, r.stdout + r.stderr
    assert sorted(p.stem for p in COMMANDS.glob("*.md")) == skill_names()
    for path in COMMANDS.glob("*.md"):
        text = path.read_text(encoding="utf-8")
        head = re.match(r'---\ndescription: (".*")\n(?:argument-hint: (".*")\n)?---\n', text)
        assert head, path.name
        assert json.loads(head.group(1)) == brain_cli.skill_meta(ENGINE / "skills" / path.stem / "SKILL.md")["description"]
        assert f".company-brain/skills/{path.stem}/SKILL.md" in text and "$ARGUMENTS" in text, path.name
        # the skill's own "Before you start" says how to run brain; the pointer must not override it
        assert "means `./brain`" not in text and "CLAUDE_SKILL_DIR" not in text, path.name


def test_commands_regenerate_and_prune(brain):
    stale = brain / ".claude" / "commands" / "company-brain" / "retired-skill.md"
    # a command generated for a skill that has since been removed
    stale.write_text(brain_cli.command_wrapper("retired-skill", {"description": "A skill that is gone now."}),
                     encoding="utf-8")
    edited = brain / ".claude" / "commands" / "company-brain" / "daily.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "hand edit\n", encoding="utf-8")
    check = cli(brain, "commands", "--check")
    assert check.returncode == 1 and "retired-skill.md" in check.stdout and "daily.md" in check.stdout
    assert cli(brain, "commands").returncode == 0
    assert not stale.exists() and "hand edit" not in edited.read_text(encoding="utf-8")
    assert cli(brain, "commands", "--check").returncode == 0


def test_hand_written_commands_are_never_replaced_or_removed(brain):
    folder = brain / ".claude" / "commands" / "company-brain"
    mine = folder / "standup.md"
    mine.write_text("---\ndescription: \"my own command\"\n---\nDo my standup.\n", encoding="utf-8")
    assert cli(brain, "commands").returncode == 0 and mine.is_file()  # not pruned
    taken = folder / "daily.md"
    taken.write_text("---\ndescription: \"my own daily\"\n---\nMine.\n", encoding="utf-8")
    r = cli(brain, "commands")
    assert r.returncode == 1 and "daily.md: written by hand" in r.stdout
    assert taken.read_text(encoding="utf-8").endswith("Mine.\n")  # left alone, and the run says so


def test_commands_refuse_a_foreign_engine(brain):
    # the repo's engine run against a copy that ships its own engine: the copy's skills decide
    r = subprocess.run([sys.executable, str(SCRIPTS / "brain.py"), "--root", str(brain), "commands"],
                       capture_output=True, text=True)
    assert r.returncode != 0 and "ships its own engine" in r.stderr


def test_skill_front_matter_must_be_one_line_values(tmp_path):
    def meta(front: str) -> dict:
        path = tmp_path / "SKILL.md"
        path.write_text(f"---\nname: x\n{front}\n---\nbody\n", encoding="utf-8")
        return brain_cli.skill_meta(path)
    assert meta("description: 'It''s quoted'")["description"] == "It's quoted"
    assert meta('description: "Say \\"hi\\""')["description"] == 'Say "hi"'
    assert meta("description: plain: with a colon")["description"] == "plain: with a colon"
    with pytest.raises(SystemExit, match="one line"):
        meta("description: >\n  folded text")
    with pytest.raises(SystemExit, match="not a valid double-quoted"):
        meta('description: "bad \\q escape"')


def test_new_brains_get_the_slash_commands():
    sources = brain_cli.scaffold_system_sources(BRAIN)
    assert all(f".claude/commands/company-brain/{p.name}" in sources for p in COMMANDS.glob("*.md"))


def test_scaffold_carries_only_the_generated_commands(brain):
    (brain / ".claude" / "commands" / "deploy-internal.md").write_text("Our deploy.\n", encoding="utf-8")
    sources = brain_cli.scaffold_system_sources(brain)
    assert ".claude/commands/deploy-internal.md" not in sources
    assert ".claude/commands/upstream-sync.md" not in sources  # the maintainer command stays in this repo
    assert ".claude/commands/company-brain/daily.md" in sources


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
