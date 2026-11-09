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
description: "Refresh the ideas list from the vault \u2014 quickly, issue #1 style, like /obsidian-gone"
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
5. Read `_CLAUDE.md` first, then load `CRITICAL_FACTS.md` for the timezone.
6. Mark each one \u2713 when done, then run:
   ```bash
   uv run --directory "SKILL_ROOT" scripts/nope2.py --path <vault>
   ```

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
    meta = brain_cli.parse_front_matter(text)[0]
    assert res["skill"] == "fresh"
    # the ' #' would start a YAML comment, so the description is quoted and reads back whole
    assert meta["description"] == ('Refresh the ideas list from the brain - quickly, issue #1 style, like '
                                   '/obsidian-gone. Use for "refresh ideas", "update my ideas".')
    assert text.splitlines()[2].startswith('description: "') and meta["argument-hint"] == "[topic]"
    # a draft never starts on its own, and the dead command in the description is on the checklist
    assert meta["disable-model-invocation"] == "true"
    assert f"{brain_cli.DRAFT_MARKER}: in the description, /obsidian-gone has no skill here." in text
    # the standard sections come from the existing skills; upstream's intro and closing rules are gone
    assert "## Before you start" in text and "## Always" in text and "## Adaptation checklist" in text
    assert "Use the obsidian-second-brain skill" not in text and "**AI-first rule:**" not in text
    assert "_CLAUDE.md" not in text and "Read `CLAUDE.md` first if it exists" not in text
    # mapped: folders, search, adapted commands, vendored scripts
    assert "the `Personal/Notes/` folder" in text and "`brain search`" in text and "/company-brain:save" in text
    assert 'python3 "<engine>/scripts/checkin.py" --path <brain> pick' in text
    # a path is not a command, and what cannot be mapped is marked, not guessed
    assert "`scripts/crew.py`" in text
    for todo in ("scripts/nope.py is not vendored here", "/obsidian-unknown has no skill here",
                 "no 'agenda' folder here", "non-ASCII text: rewrite it in ASCII"):
        assert f"{brain_cli.DRAFT_MARKER}: {todo}" in text, todo
    # a step that says more than "read CLAUDE.md first" keeps its other instruction
    assert "Read `CLAUDE.md` first, then load `CRITICAL_FACTS.md` for the timezone." in text
    # inside a code block the line stays runnable; its markers wait under the closing fence
    lines = text.splitlines()
    code = next(i for i, l in enumerate(lines) if "scripts/nope2.py" in l)
    assert brain_cli.DRAFT_MARKER not in lines[code] and lines[code + 1].strip() == "```"
    assert lines[code + 2] == f"   {brain_cli.DRAFT_MARKER}: scripts/nope2.py is not vendored here (in the code block above)."
    assert res["todos"] == text.count(brain_cli.DRAFT_MARKER) >= 7
    with pytest.raises(SystemExit, match="exists; pass --as"):
        brain_cli.draft_skill(root, data, ref, "fresh", skills_dir=skills)
    assert brain_cli.draft_skill(root, data, ref, "fresh", "fresh-ideas", skills_dir=skills)["skill"] == "fresh-ideas"


def test_no_skill_ships_with_draft_markers():
    left = [p.parent.name for p in sorted((ENGINE / "skills").glob("*/SKILL.md"))
            if brain_cli.DRAFT_MARKER in p.read_text(encoding="utf-8")]
    assert not left, f"finish these drafts with references/upstream-sync.md: {left}"


def test_draft_runs_on_its_own(tmp_path):
    for flag in ("--mark", "--copy", "--diff"):
        r = subprocess.run([sys.executable, str(ENGINE / "scripts" / "brain.py"), "--root", str(ENGINE.parent),
                            "upstream-check", "--draft", "obsidian-merge", flag], capture_output=True, text=True)
        assert r.returncode != 0 and "--draft runs on its own" in r.stderr, flag


def test_a_template_upstream_remote_is_never_used(fake_upstream, tmp_path):
    root, _, head = fake_upstream
    # in a fork of the template, `upstream` usually names the template repository
    other = tmp_path / "template"
    git(tmp_path, "init", "-q", "-b", "main", str(other))
    (other / "README.md").write_text("template\n", encoding="utf-8")
    git(other, "add", "-A"), git(other, "commit", "-q", "-m", "template")
    git(root, "remote", "add", "upstream", str(other))
    res = brain_cli.upstream_check(root)
    assert res["head"] == head and res["ref"] == f"{brain_cli.UPSTREAM_REMOTE}/main"
    assert git(root, "remote", "get-url", "upstream") == str(other)  # left as it was


def test_drafts_get_no_command_and_stay_off_mcp(tmp_path, monkeypatch):
    sys.path.insert(0, str(ENGINE / "mcp" / "vault"))
    import vault_ops
    skills = tmp_path / "skills"
    (skills / "half").mkdir(parents=True)
    (skills / "half" / "SKILL.md").write_text(
        f"---\nname: half\ndescription: A draft.\n---\n\n{brain_cli.DRAFT_MARKER}: finish me.\n", encoding="utf-8")
    monkeypatch.setattr(vault_ops, "_commands_dir", lambda: skills)
    assert vault_ops.list_skills() == [] and "unfinished draft" in vault_ops.get_skill("half")["error"]
    monkeypatch.setattr(brain_cli, "ENGINE", tmp_path)
    root = tmp_path / "brain"
    root.mkdir()
    assert brain_cli.commands_sync(root)["added"] == []


def test_the_mcp_server_reads_skill_front_matter_like_the_cli():
    sys.path.insert(0, str(ENGINE / "mcp" / "vault"))
    import vault_ops
    for md in sorted((ENGINE / "skills").glob("*/SKILL.md")):
        mine, theirs = brain_cli.skill_meta(md), vault_ops._parse_command(md)[0]
        assert {k: theirs.get(k) for k in mine} == mine, md.parent.name
