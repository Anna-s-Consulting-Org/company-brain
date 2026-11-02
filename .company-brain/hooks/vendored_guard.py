#!/usr/bin/env python3
"""PreToolUse hook: keep files vendored from obsidian-second-brain byte for byte.

Fires before Write/Edit. Files marked `"mode": "copy"` in .company-brain/upstream.json are
copies of upstream code and docs (the freshness lint, its helper, the policy, the AI-first
rules). Editing one here silently forks it, and the next `./brain upstream-check --copy`
would overwrite the edit. This hook denies the write and says what to do instead.

Override on purpose (developing the engine): COMPANY_BRAIN_ALLOW_VENDORED_EDIT=1. The
sha256 check (`./brain upstream-check --verify`, run by the tests and CI) is the backstop
for edits made outside Claude, for example with sed or an editor.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def find_root(path: Path):
    for cand in path.parents:
        if (cand / "brain.yaml").is_file() and (cand / ".company-brain").is_dir():
            return cand
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    ti = payload.get("tool_input") or {}
    raw = ti.get("file_path") or ti.get("filePath") or ""
    if not raw or os.environ.get("COMPANY_BRAIN_ALLOW_VENDORED_EDIT"):
        return
    path = Path(raw).resolve()
    root = find_root(path)
    if not root:
        return
    conf_path = root / ".company-brain" / "upstream.json"
    if not conf_path.is_file():
        return
    for entry in json.loads(conf_path.read_text(encoding="utf-8")).get("files", []):
        if entry.get("mode") == "copy" and (root / entry["local"]).resolve() == path:
            rel = path.relative_to(root.resolve()).as_posix()
            msg = (f"Blocked: {rel} is vendored unchanged from obsidian-second-brain "
                   f"({entry['upstream']}, mode: copy in .company-brain/upstream.json). "
                   "Do not edit it here. To change behaviour, add code beside it (for example in "
                   "scripts/brain.py) or change it upstream; to take a newer upstream version run "
                   "`./brain upstream-check --copy`. If you are deliberately changing the engine, set "
                   "COMPANY_BRAIN_ALLOW_VENDORED_EDIT=1 and mark the file `adapt` in upstream.json.")
            print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                                     "permissionDecision": "deny",
                                                     "permissionDecisionReason": msg}}))
            return


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a guard must never break the session
        print(f"vendored_guard: {exc}", file=sys.stderr)
