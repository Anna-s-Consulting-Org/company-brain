"""Content and system travel separately: content through a shared folder, the system through git.

These cover the settings split (brain.yaml, Company/company.yaml, brain.local.yaml), the git guard
(`brain git ...` and the pre-commit hook it installs), and `brain share`. Spec: references/layers.md,
"Two channels". Each test builds a throwaway brain from this repository's system files, the way a
fresh clone would get it, so it runs the same with or without a local Company/ folder.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]
BRAIN = ENGINE.parent
LOCAL_ONLY = {".git", "Company", "Teams", "Personal", "Sources", "Exports", "index.md", "log.md",
              "brain.local.yaml", ".share-backup", ".checkin.json", ".pytest_cache"}
GIT_ENV = {"GIT_AUTHOR_NAME": "Test", "GIT_AUTHOR_EMAIL": "test@example.com",
           "GIT_COMMITTER_NAME": "Test", "GIT_COMMITTER_EMAIL": "test@example.com"}

pytestmark = pytest.mark.skipif(shutil.which("git") is None, reason="needs git")


def _ignore_local(src, names):
    # only at the brain root: .company-brain/scaffold/company/Company must be copied
    if Path(src).resolve() == BRAIN.resolve():
        return [n for n in names if n in LOCAL_ONLY]
    return [n for n in names if n in ("__pycache__",) or n.endswith(".png")]


def cli(root: Path, *args: str, check: bool = False):
    r = subprocess.run([sys.executable, str(root / ".company-brain" / "scripts" / "brain.py"), "--root", str(root),
                        *args], capture_output=True, text=True)
    if check:
        assert r.returncode == 0, r.stdout + r.stderr
    return r


def git(root: Path, *args: str, check: bool = True):
    env = dict(os.environ, **GIT_ENV)
    r = subprocess.run(["git", "-C", str(root), "-c", "commit.gpgsign=false", *args],
                       capture_output=True, text=True, env=env)
    if check:
        assert r.returncode == 0, r.stdout + r.stderr
    return r


def note(path: Path, ntype: str, body: str = "Body.", layer: str = "company") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\ndate: 2000-01-01\ntype: {ntype}\ntags: [{ntype}]\nai-first: true\nlayer: {layer}\n---\n\n"
                    f"# {path.stem}\n\n## For future agent\nTest note.\n\n{body}\n", encoding="utf-8")
    return path


@pytest.fixture()
def fresh(tmp_path):
    """A brain as a fresh clone of the system, after `brain init` (no git)."""
    dst = tmp_path / "brain"
    shutil.copytree(BRAIN, dst, ignore=_ignore_local)
    cli(dst, "init", "--company", "Acme Labs", "--me", "Dana Smith", "--team", "Platform", check=True)
    return dst


@pytest.fixture()
def repo(tmp_path):
    """The same brain in a git repository whose first commit holds the system only."""
    dst = tmp_path / "brain"
    shutil.copytree(BRAIN, dst, ignore=_ignore_local)
    git(dst, "init", "-q")
    cli(dst, "git", "stage", check=True)  # the product as cloned: system only, committed before any content
    git(dst, "commit", "-q", "-m", "system")
    cli(dst, "init", "--company", "Acme Labs", "--me", "Dana Smith", "--team", "Platform", check=True)
    assert not git(dst, "status", "--porcelain").stdout.strip()  # init's content is all ignored
    return dst


# --- settings: brain.yaml is system, company settings travel with the content ---------------------

def test_brain_yaml_ships_system_settings_only():
    text = (BRAIN / "brain.yaml").read_text(encoding="utf-8")
    assert "company:" not in text and "sharing:" not in text and "sources:" not in text
    assert (ENGINE / "scaffold" / "brain.yaml").read_text(encoding="utf-8") == text


def test_init_writes_company_settings_to_company_yaml(fresh):
    assert "Acme Labs" in (fresh / "Company" / "company.yaml").read_text(encoding="utf-8")
    assert "Acme Labs" not in (fresh / "brain.yaml").read_text(encoding="utf-8")
    who = json.loads(cli(fresh, "whoami", check=True).stdout)
    assert who["company"] == "Acme Labs" and who["sharing"] == "local"


def test_init_refuses_git_as_a_content_sharing_model(fresh):
    r = cli(fresh, "init", "--sharing", "git")
    assert r.returncode != 0 and "system only" in r.stderr


def test_init_moves_legacy_settings_out_of_brain_yaml(fresh):
    (fresh / "Company" / "company.yaml").unlink()
    (fresh / "brain.local.yaml").unlink()
    (fresh / "brain.yaml").write_text(
        "brain:\n  name: Old Brain\n  version: 0.1.0\n\ncompany:\n  name: \"Globex\"\n  fiscal_year_start: 4\n"
        "  timezone: Europe/Paris\n\nsharing:\n  model: git\n  remote: \"\"\n\nsources:\n"
        "  - name: GTM\n    desktop: GTM folder\n", encoding="utf-8")
    assert any("brain.yaml" in i["path"] for i in json.loads(cli(fresh, "--json", "check").stdout)
               if i["severity"] == "warn")
    res = json.loads(cli(fresh, "--json", "init", check=True).stdout)
    assert res["migrated"]
    company = (fresh / "Company" / "company.yaml").read_text(encoding="utf-8")
    assert "Globex" in company and "Europe/Paris" in company and "GTM" in company
    assert "model: local" in (fresh / "brain.local.yaml").read_text(encoding="utf-8")
    system = (fresh / "brain.yaml").read_text(encoding="utf-8")
    assert "Globex" not in system and "sharing:" not in system and "Old Brain" in system
    who = json.loads(cli(fresh, "whoami", check=True).stdout)
    assert who["company"] == "Globex"


def test_a_new_company_yaml_keeps_the_legacy_settings(fresh, tmp_path):
    (fresh / "Company" / "company.yaml").unlink()
    (fresh / "brain.yaml").write_text("brain:\n  name: Company Brain\n\ncompany:\n  name: \"Globex\"\n"
                                      "  fiscal_year_start: 4\n\nsources:\n  - name: GTM\n    desktop: GTM\n",
                                      encoding="utf-8")
    before = json.loads(cli(fresh, "whoami", check=True).stdout)
    folder = tmp_path / "Docs"
    folder.mkdir()
    cli(fresh, "connect", str(folder), "--name", "Docs", "--shared", check=True)  # creates Company/company.yaml
    after = json.loads(cli(fresh, "whoami", check=True).stdout)
    assert after["company"] == "Globex" and after["period"]["quarter"] == before["period"]["quarter"]
    text = (fresh / "Company" / "company.yaml").read_text(encoding="utf-8")
    assert "GTM" in text and "Docs" in text


def test_shared_sources_are_recorded_with_the_content(fresh, tmp_path):
    folder = tmp_path / "Strategy docs"
    folder.mkdir()
    cli(fresh, "connect", str(folder), "--name", "Strategy", "--shared", check=True)
    assert "Strategy" in (fresh / "Company" / "company.yaml").read_text(encoding="utf-8")
    assert "Strategy" not in (fresh / "brain.yaml").read_text(encoding="utf-8")


# --- git carries the system only -------------------------------------------------------------------

def test_gitignore_keeps_every_content_path_out(repo):
    for p in ("Company", "Teams", "Personal", "brain.local.yaml", "index.md", "Sources"):
        assert git(repo, "check-ignore", "-q", p, check=False).returncode == 0, p
    assert not cli(repo, "git", "check", "--tracked").returncode
    tracked = git(repo, "ls-files").stdout.splitlines()
    assert tracked and not [t for t in tracked if t.split("/")[0] in ("Company", "Teams", "Personal")]


def test_init_installs_the_pre_commit_guard(repo):
    hook = Path(git(repo, "rev-parse", "--git-path", "hooks").stdout.strip())
    hook = (hook if hook.is_absolute() else repo / hook) / "pre-commit"
    assert hook.is_file() and os.access(hook, os.X_OK)
    assert "git check --staged" in hook.read_text(encoding="utf-8")


def test_the_hook_refuses_force_added_content(repo):
    note(repo / "Company" / "Meetings" / "2000-01-01 - Board.md", "meeting")
    git(repo, "add", "-f", "Company/Meetings/2000-01-01 - Board.md")
    r = git(repo, "commit", "-m", "notes", check=False)
    assert r.returncode != 0 and "never content" in r.stderr and "Company/Meetings" in r.stderr


def test_the_hook_refuses_a_person_or_company_name_in_a_system_file(repo):
    skill = repo / ".company-brain" / "skills" / "daily" / "SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\n- Ask Dana Smith before writing.\n", encoding="utf-8")
    git(repo, "add", str(skill.relative_to(repo)))
    r = git(repo, "commit", "-m", "skill", check=False)
    assert r.returncode != 0 and "Dana Smith" in r.stderr
    git(repo, "restore", "--staged", str(skill.relative_to(repo)))
    skill.write_text(skill.read_text(encoding="utf-8").replace("Dana Smith", "Acme Labs"), encoding="utf-8")
    git(repo, "add", str(skill.relative_to(repo)))
    r = git(repo, "commit", "-m", "skill", check=False)
    assert r.returncode != 0 and "company name" in r.stderr


def test_the_hook_refuses_links_and_paths_to_company_content(repo):
    note(repo / "Company" / "OKRs" / "2000-Q1 - Company - O1 - Win the enterprise segment.md", "objective")
    tpl = repo / "Templates" / "Meeting Template.md"
    tpl.write_text(tpl.read_text(encoding="utf-8") + "\nSee [[2000-Q1 - Company - O1 - Win the enterprise segment]]"
                   " and Teams/Platform/Platform Board.md\n", encoding="utf-8")
    r = cli(repo, "--json", "git", "stage")
    assert r.returncode == 1
    found = " ".join(p["problem"] for p in json.loads(r.stdout)["problems"])
    assert "Win the enterprise segment]]" in found and "team 'Platform'" in found


def test_generic_examples_and_scaffold_hubs_pass(repo):
    doc = repo / "System" / "Skills.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\nExample: [[Company OKRs]], [[My Board]], "
                   "`Teams/<Team>/Weekly/`, [[OKR Tree - 2000-Q1]].\n", encoding="utf-8")
    res = json.loads(cli(repo, "--json", "git", "stage", check=True).stdout)
    assert res["staged"] == ["System/Skills.md"] and not res["problems"]


def test_an_edited_line_keeps_its_example_but_a_new_use_is_checked(repo):
    spec = repo / ".company-brain" / "references" / "schemas.md"
    lines = spec.read_text(encoding="utf-8").split("\n")
    i = next(n for n, l in enumerate(lines) if "[[Platform]]" in l)  # a shipped example matching the test team
    lines[i] += " (example)"
    spec.write_text("\n".join(lines), encoding="utf-8")
    assert not json.loads(cli(repo, "--json", "git", "stage", check=True).stdout)["problems"]
    spec.write_text(spec.read_text(encoding="utf-8") + "\nAnother use: [[Platform]].\n", encoding="utf-8")
    problems = json.loads(cli(repo, "--json", "git", "stage").stdout)["problems"]
    assert any("[[Platform]]" in p["problem"] for p in problems)


@pytest.mark.parametrize("setting", ["diff.noprefix", "diff.mnemonicPrefix"])
def test_user_diff_settings_cannot_hide_a_file_from_the_scan(repo, setting):
    git(repo, "config", setting, "true")
    doc = repo / "System" / "Skills.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\nAsk Dana Smith.\n", encoding="utf-8")
    git(repo, "add", "System/Skills.md")
    r = cli(repo, "git", "check", "--staged")
    assert r.returncode == 1 and "Dana Smith" in r.stderr


def test_team_paths_need_a_boundary(repo):
    doc = repo / "System" / "Skills.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\nExample: `Teams/Platformers/`.\n", encoding="utf-8")
    assert not json.loads(cli(repo, "--json", "git", "stage", check=True).stdout)["problems"]
    doc.write_text(doc.read_text(encoding="utf-8") + "\nSee `Teams/Platform/`.\n", encoding="utf-8")
    problems = json.loads(cli(repo, "--json", "git", "stage").stdout)["problems"]
    assert any("team 'Platform'" in p["problem"] for p in problems)


def test_an_added_line_that_looks_like_a_diff_header_does_not_stop_the_scan(repo):
    doc = repo / "System" / "Skills.md"
    doc.write_text(doc.read_text(encoding="utf-8") + "\n++ heading\nAsk Dana Smith for numbers.\n", encoding="utf-8")
    git(repo, "add", "System/Skills.md")
    r = cli(repo, "git", "check", "--staged")
    assert r.returncode == 1 and "Dana Smith" in r.stderr


def test_the_hook_refuses_a_content_note_in_a_system_folder(repo):
    note(repo / "System" / "Leadership sync.md", "meeting")
    git(repo, "add", "System/Leadership sync.md")
    r = git(repo, "commit", "-m", "doc", check=False)
    assert r.returncode != 0 and "type: meeting" in r.stderr


def test_a_generic_system_change_commits(repo):
    skill = repo / ".company-brain" / "skills" / "daily" / "SKILL.md"
    skill.write_text(skill.read_text(encoding="utf-8") + "\n- Link [[Company OKRs]] and `Teams/<Team>/` hubs.\n",
                     encoding="utf-8")
    res = json.loads(cli(repo, "--json", "git", "stage", check=True).stdout)
    assert res["staged"] == [".company-brain/skills/daily/SKILL.md"] and not res["problems"]
    git(repo, "commit", "-q", "-m", "skill")


def test_stage_adds_system_files_and_leaves_everything_else(repo):
    (repo / "Templates" / "New Template.md").write_text("---\ntype: knowledge\n---\n<% tp.file.title %>\n",
                                                        encoding="utf-8")
    note(repo / "Company" / "Knowledge" / "Pricing.md", "knowledge")
    (repo / "scratch.md").write_text("draft\n", encoding="utf-8")
    res = json.loads(cli(repo, "--json", "git", "stage", check=True).stdout)
    staged = git(repo, "diff", "--cached", "--name-only").stdout.splitlines()
    assert staged == ["Templates/New Template.md"] and "scratch.md" in res["left_out"]
    st = json.loads(cli(repo, "--json", "git", "status", check=True).stdout)
    assert [i["path"] for i in st["other"]] == ["scratch.md"]


def test_git_allow_adds_system_paths_but_never_content(repo):
    (repo / "docs").mkdir()
    (repo / "docs" / "guide.md").write_text("A guide.\n", encoding="utf-8")
    git(repo, "add", "docs/guide.md")
    assert git(repo, "commit", "-m", "docs", check=False).returncode != 0
    text = (repo / "brain.yaml").read_text(encoding="utf-8").replace("allow: [README.md", "allow: [docs, Company, README.md")
    (repo / "brain.yaml").write_text(text, encoding="utf-8")
    git(repo, "add", "brain.yaml")
    git(repo, "commit", "-q", "-m", "docs")
    note(repo / "Company" / "Knowledge" / "Secret.md", "knowledge")
    git(repo, "add", "-f", "Company/Knowledge/Secret.md")
    assert git(repo, "commit", "-m", "content", check=False).returncode != 0


def test_untrack_takes_content_out_of_git_and_keeps_the_files(repo):
    meeting = note(repo / "Teams" / "Platform" / "Meetings" / "2000-01-01 - Sync.md", "meeting", layer="team")
    git(repo, "add", "-f", str(meeting.relative_to(repo)))
    git(repo, "commit", "-q", "--no-verify", "-m", "an older brain committed notes")
    assert cli(repo, "git", "check", "--tracked").returncode == 1
    errors = [i for i in json.loads(cli(repo, "--json", "check").stdout) if i["severity"] == "error"]
    assert any(i["path"] == "Teams" for i in errors)
    assert "would stop tracking" in cli(repo, "git", "untrack", check=True).stdout
    cli(repo, "git", "untrack", "--yes", check=True)
    git(repo, "commit", "-q", "-m", "content leaves git")  # a removal passes the hook
    assert cli(repo, "git", "check", "--tracked").returncode == 0 and meeting.is_file()


def test_untrack_does_not_accept_a_trailing_slash_ignore_line(repo):
    ignore = repo / ".gitignore"
    ignore.write_text(ignore.read_text(encoding="utf-8").replace("/Company\n", "/Company/\n"), encoding="utf-8")
    assert "/Company" in json.loads(cli(repo, "--json", "git", "untrack", check=True).stdout)["gitignore_missing"]


# --- content travels through a shared folder ----------------------------------------------------------

def test_share_dry_run_changes_nothing(fresh, tmp_path):
    r = cli(fresh, "share", "--to", str(tmp_path / "shared"), check=True)
    assert "Dry run" in r.stdout and not (fresh / "Company").is_symlink() and not (tmp_path / "shared").exists()


def test_share_moves_company_and_teams_and_keeps_personal_local(fresh, tmp_path):
    shared = tmp_path / "shared"
    cli(fresh, "share", "--to", str(shared), "--yes", check=True)
    for name in ("Company", "Teams"):
        assert (fresh / name).is_symlink() and (shared / name).is_dir()
    assert (shared / "Company" / "company.yaml").is_file() and (shared / "Teams" / "Platform").is_dir()
    assert not (fresh / "Personal").is_symlink() and not (shared / "Personal").exists()
    who = json.loads(cli(fresh, "whoami", check=True).stdout)
    assert who["sharing"] == "folder" and who["sharing_location"] == str(shared.resolve())
    assert who["company"] == "Acme Labs" and "Platform" in who["all_teams"]
    assert not [i for i in json.loads(cli(fresh, "--json", "check").stdout) if i["severity"] == "error"]


def test_a_teammate_gets_the_shared_copy_and_a_backup_of_their_own(fresh, tmp_path):
    shared = tmp_path / "shared"
    cli(fresh, "share", "--to", str(shared), "--yes", check=True)
    mate = tmp_path / "mate"
    shutil.copytree(BRAIN, mate, ignore=_ignore_local)
    cli(mate, "init", "--company", "Placeholder", "--me", "Lee Park", check=True)
    plan = json.loads(cli(mate, "--json", "share", "--to", str(shared), check=True).stdout)
    assert {s["action"] for s in plan["steps"]} == {"backup"}
    cli(mate, "share", "--to", str(shared), "--yes", check=True)
    assert json.loads(cli(mate, "whoami", check=True).stdout)["company"] == "Acme Labs"
    backups = list((mate / ".share-backup").iterdir())
    assert backups and any((b / "company.yaml").is_file() for b in backups)


def test_share_moves_nothing_when_links_cannot_be_made(fresh, tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(fresh / ".company-brain" / "scripts"))
    import brain
    shared = tmp_path / "shared"
    plan = brain.share_plan(fresh, str(shared))

    def refuse(self, *args, **kwargs):
        raise OSError("symbolic links are not available")
    monkeypatch.setattr(Path, "symlink_to", refuse)
    with pytest.raises(SystemExit, match="Nothing was moved"):
        brain.share_apply(fresh, plan)
    assert (fresh / "Company").is_dir() and not (fresh / "Company").is_symlink()
    assert not (shared / "Company").exists() and not list(fresh.glob(".share-link-test-*"))


def test_share_refuses_a_folder_that_contains_the_brain(fresh, tmp_path):
    r = cli(fresh, "share", "--to", str(tmp_path))
    assert r.returncode != 0 and "Personal/ would sync" in r.stderr
    r = cli(fresh, "share", "--to", str(fresh / "inside"))
    assert r.returncode != 0 and "inside the brain" in r.stderr


def test_check_errors_when_personal_sits_in_the_shared_folder(fresh, tmp_path):
    shared = tmp_path / "shared"
    cli(fresh, "share", "--to", str(shared), "--yes", check=True)
    shutil.move(str(fresh / "Personal"), str(shared / "Personal"))
    (fresh / "Personal").symlink_to(shared / "Personal", target_is_directory=True)
    errors = [i for i in json.loads(cli(fresh, "--json", "check").stdout) if i["severity"] == "error"]
    assert any(i["path"] == "Personal" for i in errors)
