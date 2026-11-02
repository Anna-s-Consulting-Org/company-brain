#!/usr/bin/env python3
"""PostToolUse hook: apply the freshness policy to every note Claude writes.

Fires after Write/Edit. Runs the vendored freshness lint (scripts/freshness_lint.py,
from obsidian-second-brain) on the written note and tells Claude about undated claims
about fast-changing facts, aged `as of` stamps, and unmapped typed pointers.
Spec: .company-brain/references/freshness-policy.md. Warns only; the write is not reverted.
Folders skipped by `./brain freshness` (exempt-dirs in .freshness.json) are skipped here too.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"


def find_root(path: Path):
    for cand in path.parents:
        if (cand / "brain.yaml").is_file() and (cand / ".company-brain").is_dir():
            return cand
    return None


def main() -> None:
    sys.path.insert(0, str(SCRIPTS))
    import brain  # inside main so a broken engine is caught by the guard below, not at import
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
    findings = brain.freshness_findings_for(root, path.resolve())
    if not findings:
        return
    rel = path.resolve().relative_to(root.resolve()).as_posix()
    shown = "; ".join(f"{f['rule']} line {f['line']}: {f['text']}" for f in findings[:5])
    more = f" (and {len(findings) - 5} more)" if len(findings) > 5 else ""
    msg = (f"Company Brain freshness check: {rel} has {len(findings)} finding(s): {shown}{more}. "
           "Fix: add `(as of YYYY-MM-DD)` to the claim, turn it into a pointer to where the truth lives, "
           "or move it into a dated note (references/freshness-policy.md).")
    print(json.dumps({"systemMessage": msg,
                      "hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": msg}}))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:  # a check must never break the session
        print(f"freshness_guard: {exc}", file=sys.stderr)
