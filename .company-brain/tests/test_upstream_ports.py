"""Fixes ported by hand from obsidian-second-brain into the adapted files.

validate-ai-first.sh and mcp/vault/vault_ops.py are adapted, not copied, so upstream-check cannot
update them for us. These tests pin the behaviour we ported so a later sync cannot undo it.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE / "mcp" / "vault"))
sys.path.insert(0, str(ENGINE / "scripts"))

import vault_ops  # noqa: E402


@pytest.fixture()
def vault(tmp_path, monkeypatch):
    (tmp_path / "brain.yaml").write_text("brain:\n  name: Test\n", encoding="utf-8")
    monkeypatch.setenv("COMPANY_BRAIN_PATH", str(tmp_path))
    return tmp_path


def note(root: Path, rel: str, body: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\ndate: 2000-01-01\ntype: knowledge\ntags: [knowledge]\nai-first: true\nlayer: company\n---\n"
                    f"# T\n\n## For future agent\nTest.\n\n{body}\n", encoding="utf-8")
    return path


# --- validate-ai-first.sh: a dash inside a wikilink target is a filename, not prose ---------------

def run_hook(path: Path) -> str:
    event = json.dumps({"tool_input": {"file_path": str(path)}})
    r = subprocess.run([str(ENGINE / "hooks" / "validate-ai-first.sh")], input=event, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return r.stdout


def test_hook_ignores_a_dash_inside_a_wikilink_target(vault):
    (vault / ".company-brain").mkdir()
    path = note(vault, "Company/Knowledge/Linked.md", "See [[Plan – Q4]] and [[Plan – Q4|the plan]].")
    assert "en-dash" not in run_hook(path)


def test_hook_still_flags_a_dash_in_prose(vault):
    (vault / ".company-brain").mkdir()
    path = note(vault, "Company/Knowledge/Prose.md", "This sentence – has a dash.")
    assert "en-dash" in run_hook(path)


# --- vault_ops.py ---------------------------------------------------------------------------------

def test_move_note_copies_byte_for_byte_and_removes_the_source(vault):
    src = note(vault, "Company/Knowledge/A.md", "body one")
    original = src.read_bytes()
    result = vault_ops.move_note("Company/Knowledge/A.md", "Company/Knowledge/B.md")
    assert "error" not in result, result
    assert not src.exists()
    assert (vault / "Company/Knowledge/B.md").read_bytes() == original


def test_move_note_never_overwrites_an_existing_destination(vault):
    note(vault, "Company/Knowledge/A.md", "a")
    existing = note(vault, "Company/Knowledge/B.md", "b")
    before = existing.read_bytes()
    result = vault_ops.move_note("Company/Knowledge/A.md", "Company/Knowledge/B.md")
    assert "already exists" in result["error"]
    assert existing.read_bytes() == before and (vault / "Company/Knowledge/A.md").exists()


def test_move_note_reports_an_unusable_destination_folder_instead_of_raising(vault):
    note(vault, "Company/Knowledge/A.md", "a")
    (vault / "blocker").write_text("a file, not a folder", encoding="utf-8")
    result = vault_ops.move_note("Company/Knowledge/A.md", "blocker/B.md")
    assert "error" in result and (vault / "Company/Knowledge/A.md").exists()


def test_wikilink_target_drops_the_table_escape_backslash():
    assert vault_ops._wikilinks("| [[Some Note\\|alias]] |") == ["Some Note"]


def test_entry_point_notes_are_not_reported_as_orphans(vault):
    (vault / "CLAUDE.md").write_text("# Manual\n", encoding="utf-8")
    (vault / "Home.md").write_text("# Home\n", encoding="utf-8")
    note(vault, "Company/Knowledge/Real.md", "no links to or from here")
    orphans = vault_ops.vault_health()["orphans"]
    assert "CLAUDE.md" not in orphans and "Home.md" not in orphans
