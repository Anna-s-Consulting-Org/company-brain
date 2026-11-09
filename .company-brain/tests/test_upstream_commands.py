"""Upstream commands are triaged in upstream.json, and upstream-check reports what changed since.

obsidian-second-brain keeps adding commands. Each one gets a decision in upstream.json "commands.map"
(adapted, covered, deferred or declined), so upstream-check can report new commands nobody has looked
at, removed ones, and changes to the commands a skill here came from. The playbook for acting on that
report is references/upstream-sync.md.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE / "scripts"))
import brain as brain_cli  # noqa: E402

DECISIONS = {"adapted", "covered", "deferred", "declined"}


def git(cwd: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(cwd), "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
                          check=True, capture_output=True, text=True).stdout.strip()


def test_every_triaged_command_has_a_valid_decision():
    cmds = json.loads((ENGINE / "upstream.json").read_text(encoding="utf-8"))["commands"]
    assert (ENGINE.parent / cmds["playbook"]).is_file()
    for name, entry in cmds["map"].items():
        assert entry["decision"] in DECISIONS, name
        if entry["decision"] in brain_cli.TRACKED_DECISIONS:
            assert (ENGINE / "skills" / entry["skill"] / "SKILL.md").is_file(), f"{name}: no skill {entry['skill']}"
        else:
            assert len(entry.get("reason", "")) > 20, f"{name}: say why it was {entry['decision']}"


# An upstream command in upstream's own shape: front matter with triggers, the standard intro, the
# personal-vault folders, tools and scripts, and the closing rules the skill sections replace.
FRESH = """---
description: Refresh the ideas list from the vault \u2014 quickly
category: vault
argument-hint: "[topic]"
triggers_en: ["refresh ideas", "update my ideas"]
triggers_zh: ["\u66f4\u65b0"]
---

Use the obsidian-second-brain skill. Execute `/obsidian-fresh $ARGUMENTS`:

1. Read `_CLAUDE.md` first if it exists in the vault root
2. Search the ideas folder (resolved per `references/folder-map.md`) with `obsidian_search`, then run `/save`.
3. Run `uv run --directory "SKILL_ROOT" scripts/checkin.py --path <vault> pick` and `uv run --directory "SKILL_ROOT" scripts/nope.py`.
4. Ask `/obsidian-unknown` for help, then read `scripts/crew.py` and the agenda folder (resolved per `references/folder-map.md` - wiki-style `wiki/agenda/`).

---

**AI-first rule:** Every note created by this command MUST follow the rules.

**Anti-fabrication:** Search exhaustively.
"""


@pytest.fixture()
def fake_upstream(tmp_path, monkeypatch):
    """A local upstream with two commits, a brain repo to check from, and an upstream.json pointing at both."""
    up = tmp_path / "upstream"
    (up / "commands").mkdir(parents=True)
    git(tmp_path, "init", "-q", "-b", "main", str(up))
    for name in ("save", "old", "skipped"):
        (up / "commands" / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    (up / "scripts").mkdir()
    (up / "scripts" / "tool.py").write_text("print('one')\n", encoding="utf-8")
    git(up, "add", "-A"), git(up, "commit", "-q", "-m", "one")
    first = git(up, "rev-parse", "HEAD")
    (up / "commands" / "save.md").write_text("# save\nnew step\n", encoding="utf-8")
    (up / "commands" / "skipped.md").write_text("# skipped\nchanged too\n", encoding="utf-8")
    (up / "commands" / "old.md").unlink()
    (up / "commands" / "fresh.md").write_text(FRESH, encoding="utf-8")
    (up / "scripts" / "tool.py").write_text("print('two')\n", encoding="utf-8")
    git(up, "add", "-A"), git(up, "commit", "-q", "-m", "two")
    root = tmp_path / "brain"
    git(tmp_path, "init", "-q", str(root))
    (root / "tool.py").write_text("print('one')\n", encoding="utf-8")
    conf = tmp_path / "upstream.json"
    files = [{"upstream": "scripts/tool.py", "local": "tool.py", "mode": "copy", "sha256": "x"}]
    conf.write_text(json.dumps({"repo": str(up), "branch": "main", "commit": first, "files": files, "commands": {
        "dir": "commands", "commit": first, "playbook": "references/upstream-sync.md", "map": {
            "save": {"decision": "adapted", "skill": "save"},
            "old": {"decision": "covered", "skill": "daily"},
            "skipped": {"decision": "declined", "reason": "not for a company brain"}}}}), encoding="utf-8")
    monkeypatch.setattr(brain_cli, "UPSTREAM_CONF", conf)
    return root, conf, git(up, "rev-parse", "HEAD")


def test_upstream_check_reports_new_removed_and_changed_commands(fake_upstream):
    root, _, _ = fake_upstream
    tri = brain_cli.upstream_check(root)["commands"]
    assert tri["new"] == ["fresh"] and tri["removed"] == ["old"]
    # only adapted and covered commands are followed; a declined one may change freely
    assert [(c["name"], c["skill"]) for c in tri["changed"]] == [("save", "save")]
    assert "new step" in brain_cli.upstream_check(root, diff=True)["diff"]


def test_mark_waits_until_every_command_is_triaged(fake_upstream):
    root, conf, head = fake_upstream
    with pytest.raises(SystemExit, match="new: fresh.*removed upstream: old"):
        brain_cli.upstream_check(root, mark=True)
    data = json.loads(conf.read_text(encoding="utf-8"))
    assert data["commands"]["commit"] != head  # nothing recorded
    data["commands"]["map"]["fresh"] = {"decision": "declined", "reason": "test"}
    del data["commands"]["map"]["old"]
    conf.write_text(json.dumps(data), encoding="utf-8")
    assert brain_cli.upstream_check(root, mark=True)["marked"] == head
    data = json.loads(conf.read_text(encoding="utf-8"))
    assert data["commit"] == head and data["commands"]["commit"] == head
    tri = brain_cli.upstream_check(root)["commands"]
    assert (tri["new"], tri["removed"], tri["changed"], tri["missing_dir"]) == ([], [], [], False)


def test_a_refused_mark_copies_nothing(fake_upstream):
    root, conf, _ = fake_upstream
    before = conf.read_text(encoding="utf-8")
    with pytest.raises(SystemExit, match="triage the upstream commands first"):
        brain_cli.upstream_check(root, copy=True, mark=True)
    assert (root / "tool.py").read_text(encoding="utf-8") == "print('one')\n"
    assert conf.read_text(encoding="utf-8") == before


def test_moved_commands_folder_is_reported_not_fatal(fake_upstream):
    root, conf, _ = fake_upstream
    data = json.loads(conf.read_text(encoding="utf-8"))
    data["commands"]["dir"] = "skills"  # upstream has no skills/ folder
    conf.write_text(json.dumps(data), encoding="utf-8")
    res = brain_cli.upstream_check(root)
    assert res["commands"]["missing_dir"] and [f["local"] for f in res["changed"]] == ["tool.py"]
    with pytest.raises(SystemExit, match="no skills/ folder"):
        brain_cli.upstream_check(root, mark=True)


def test_draft_does_the_mechanical_part_and_marks_the_rest(fake_upstream, tmp_path):
    root, conf, _ = fake_upstream
    data = json.loads(conf.read_text(encoding="utf-8"))
    ref = brain_cli.fetch_upstream(root, data)
    skills = tmp_path / "skills"
    res = brain_cli.draft_skill(root, data, ref, "fresh", skills_dir=skills)
    text = (skills / "fresh" / "SKILL.md").read_text(encoding="utf-8")
    assert res["skill"] == "fresh" and text.isascii()
    assert text.startswith('---\nname: fresh\ndescription: Refresh the ideas list from the brain - quickly. '
                           'Use for "refresh ideas", "update my ideas".\nargument-hint: "[topic]"\n---\n')
    # the standard sections come from the existing skills; upstream's intro and closing rules are gone
    assert "## Before you start" in text and "## Always" in text and "## Adaptation checklist" in text
    assert "Use the obsidian-second-brain skill" not in text and "**AI-first rule:**" not in text
    assert "_CLAUDE.md" not in text and "Read `CLAUDE.md` first" not in text
    # mapped: folders, search, adapted commands, vendored scripts
    assert "the `Personal/Notes/` folder" in text and "`brain search`" in text and "/company-brain:save" in text
    assert 'python3 "<engine>/scripts/checkin.py" --path <brain> pick' in text
    # a path is not a command, and what cannot be mapped is marked, not guessed
    assert "`scripts/crew.py`" in text
    for todo in ("scripts/nope.py is not vendored here", "/obsidian-unknown has no skill here",
                 "no 'agenda' folder here"):
        assert f"{brain_cli.DRAFT_MARKER}: {todo}" in text, todo
    assert res["todos"] == text.count(brain_cli.DRAFT_MARKER) >= 7
    with pytest.raises(SystemExit, match="exists; pass --as"):
        brain_cli.draft_skill(root, data, ref, "fresh", skills_dir=skills)
    assert brain_cli.draft_skill(root, data, ref, "fresh", "fresh-ideas", skills_dir=skills)["skill"] == "fresh-ideas"


def test_no_skill_ships_with_draft_markers():
    left = [p.parent.name for p in sorted((ENGINE / "skills").glob("*/SKILL.md"))
            if brain_cli.DRAFT_MARKER in p.read_text(encoding="utf-8")]
    assert not left, f"finish these drafts with references/upstream-sync.md: {left}"
