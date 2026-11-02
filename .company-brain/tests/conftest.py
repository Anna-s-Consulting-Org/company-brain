"""Skips for vendored upstream tests that assume obsidian-second-brain's own layout.

The vendored tests are byte-for-byte copies (see .company-brain/upstream.json), so they cannot be
edited. A few of them assume things that are different here on purpose. Each is skipped by name with
the reason below, and test_new_capabilities.py holds the equivalent test for this layout.
"""
from __future__ import annotations

import pytest

UPSTREAM_LAYOUT = {
    "test_checkin.py::test_check_notes_fails_then_fix_rewrites_prose_only":
        "runs the hook in a folder with no brain.yaml; our hook finds the brain by brain.yaml",
    "test_checkin.py::test_check_notes_reports_what_it_cannot_fix":
        "runs the hook in a folder with no brain.yaml; our hook finds the brain by brain.yaml",
    "test_crew.py::test_unconfigured_defaults":
        "default folder comes from OBSIDIAN_VAULT_PATH; osb_env here reads COMPANY_BRAIN_PATH",
    "test_crew.py::test_built_crew_runs_from_an_unrelated_folder":
        "needs upstream's build output (build.sh adapters), which this repo does not have",
    "test_verify_quotes.py::test_reconcile_proves_contradictions_with_the_checker":
        "reads upstream's commands/obsidian-reconcile.md; ours is skills/reconcile/SKILL.md",
}


def pytest_collection_modifyitems(config, items):
    for item in items:
        for needle, reason in UPSTREAM_LAYOUT.items():
            if needle in item.nodeid:
                item.add_marker(pytest.mark.skip(reason=f"upstream layout: {reason}"))
