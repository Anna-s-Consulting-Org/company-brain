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


@pytest.fixture()
def fake_upstream(tmp_path, monkeypatch):
    """A local upstream with two commits, a brain repo to check from, and an upstream.json pointing at both."""
    up = tmp_path / "upstream"
    (up / "commands").mkdir(parents=True)
    git(tmp_path, "init", "-q", "-b", "main", str(up))
    for name in ("save", "old", "skipped"):
        (up / "commands" / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    git(up, "add", "-A"), git(up, "commit", "-q", "-m", "one")
    first = git(up, "rev-parse", "HEAD")
    (up / "commands" / "save.md").write_text("# save\nnew step\n", encoding="utf-8")
    (up / "commands" / "skipped.md").write_text("# skipped\nchanged too\n", encoding="utf-8")
    (up / "commands" / "old.md").unlink()
    (up / "commands" / "fresh.md").write_text("# fresh\n", encoding="utf-8")
    git(up, "add", "-A"), git(up, "commit", "-q", "-m", "two")
    root = tmp_path / "brain"
    git(tmp_path, "init", "-q", str(root))
    conf = tmp_path / "upstream.json"
    conf.write_text(json.dumps({"repo": str(up), "branch": "main", "commit": first, "files": [], "commands": {
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
    assert brain_cli.upstream_check(root)["commands"] == {
        "base": head, "playbook": "references/upstream-sync.md", "new": [], "removed": [], "changed": []}
