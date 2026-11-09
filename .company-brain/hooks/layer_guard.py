#!/usr/bin/env python3
"""PostToolUse hook: keep personal content out of shared layers.

Fires after Write/Edit. When the written file is a markdown note in Company/ or
Teams/ of a Company Brain, it flags:
  - wikilinks or embeds that resolve only to notes in Personal/ (a leak: the link
    dangles for everyone else and its title can reveal private content),
  - a `## Private` section (private content belongs in Personal/),
  - `layer: personal` declared in a shared folder.
Spec: .company-brain/references/layers.md. Warns via hook JSON; the write is not reverted.
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import brain  # noqa: E402


def find_root(path: Path):
    for cand in path.parents:
        if (cand / "brain.yaml").is_file() and (cand / ".company-brain").is_dir():
            return cand
    return None


def stems(folder: Path, exclude_top: str = "") -> set:
    out = set()
    if not folder.is_dir():
        return out
    for dirpath, dirnames, filenames in os.walk(folder):
        rel = Path(dirpath).relative_to(folder)
        if rel.parts and (rel.parts[0].startswith(".") or rel.parts[0] in (exclude_top, "Sources", "Exports")):
            dirnames[:] = []
            continue
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        out.update(f[:-3].lower() for f in filenames if f.endswith(".md"))
    return out


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    ti = payload.get("tool_input") or {}
    raw = ti.get("file_path") or ti.get("filePath") or ""
    if not raw.endswith(".md"):
        return
    path = Path(raw)
    if not path.is_file():
        return
    root = find_root(path.resolve())
    if not root:
        return
    rel = path.resolve().relative_to(root).as_posix()
    if not rel.startswith(("Company/", "Teams/")):
        return
    note = brain.Note(root, path.resolve())
    problems = []
    if str(note.fm.get("layer") or "") == "personal":
        problems.append("frontmatter says `layer: personal` but the note is in a shared folder")
    if re.search(r"^## Private\s*$", note.body, re.M):
        problems.append("it contains a `## Private` section; private content must stay in Personal/")
    leaks = brain.stakeholder_leaks(note)
    if leaks:
        problems.append("it is a shared profile carrying stakeholder content (" + ", ".join(leaks)
                        + "); that belongs in Personal/Stakeholders/Stakeholder - " + note.name + ".md")
    personal = stems(root / "Personal")
    shared = stems(root, exclude_top="Personal")
    leaked = sorted({t for t, _, _ in note.links()
                     if t.split("/")[-1].lower() in personal and t.split("/")[-1].lower() not in shared})
    if leaked:
        problems.append("it links to personal notes: " + ", ".join(f"[[{t}]]" for t in leaked)
                        + " (rewrite as plain text, or promote the target with /company-brain:promote)")
    if not problems:
        return
    msg = (f"Company Brain layer guard: {rel} is shared with the team or company, but "
           + "; and ".join(problems) + ". Fix it now. Rule: links point up the stack "
           "(personal to team to company), never down.")
    print(json.dumps({"decision": "block", "reason": msg, "systemMessage": msg,
                      "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a guard must never break the session
        print(f"layer_guard: {exc}", file=sys.stderr)
