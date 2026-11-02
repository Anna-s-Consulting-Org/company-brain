# Third-party notices

Company Brain vendors and adapts parts of **obsidian-second-brain**
(https://github.com/eugeniughelbur/obsidian-second-brain), used under the MIT License below.
The upstream commit these files are synced with is recorded in `.company-brain/upstream.json`;
`./brain upstream-check` lists what changed upstream since.

| Company Brain file | Origin | Changes |
|---|---|---|
| `.company-brain/references/ai-first-rules.md` | `references/ai-first-rules.md` | none |
| `.company-brain/references/freshness-policy.md` | `references/freshness-policy.md` | none |
| `.company-brain/references/propagation.md` | `references/write-rules.md` | rewritten for layers |
| `.company-brain/hooks/validate-ai-first.sh` | `hooks/validate-ai-first.sh` | brain found by `brain.yaml` marker, Company Brain config dir, kanban and engine folders skipped |
| `.company-brain/mcp/vault/server.py`, `vault_ops.py` | `integrations/obsidian-mcp-server/` | tools renamed `brain_*`, `COMPANY_BRAIN_PATH`, captures in `Personal/Inbox`, skills from `skills/`, two new tools, orphan check also exempts `CLAUDE.md` |
| `.company-brain/scripts/osb_env.py` | `scripts/osb_env.py` | config dir and variable names |
| `.company-brain/scripts/freshness_lint.py` | `scripts/freshness_lint.py` | none (wired in by `brain.py`, `hooks/freshness_guard.py`) |
| `.company-brain/scripts/vault_scan.py` | `scripts/vault_scan.py` | none (imported by the freshness lint) |
| `.company-brain/tests/test_freshness_lint.py` | `tests/test_freshness_lint.py` | none |
| `.company-brain/scripts/checkin.py` | `scripts/checkin.py` | none (driven by the `checkin` skill) |
| `.company-brain/scripts/check_notes.py` | `scripts/check_notes.py` | none (runs our adapted `validate-ai-first.sh`) |
| `.company-brain/scripts/verify_quotes.py` | `scripts/verify_quotes.py` | none (used by the `reconcile` skill) |
| `.company-brain/scripts/ingest_batch.py` | `scripts/ingest_batch.py` | none (needs PyYAML; used by `ingest` for folders) |
| `.company-brain/scripts/document_to_pdf.py` | `scripts/document_to_pdf.py` | none (used by `ingest` for Word and OpenDocument text) |
| `.company-brain/scripts/crew.py` | `scripts/crew.py` | none (the `crew` skill always passes `--dir`) |
| `.company-brain/scripts/vault_health.py`, `note_io.py`, `sweep_non_ascii.py` | `scripts/` of the same names | none (imported by the scripts above) |
| `brain search` in `.company-brain/scripts/brain.py` | `scripts/vault_search.py` | ported as a `brain` subcommand against our `vault_ops` |
| `.company-brain/tests/test_{checkin,verify_quotes,crew,document_to_pdf,ingest_batch,vault_health_precision,vault_health_unicode,user_excludes}.py`, `_bash.py` | `tests/` of the same names | none (a few cases that assume upstream's layout are skipped by name in `conftest.py`) |
| `.company-brain/skills/{checkin,reconcile,crew}/SKILL.md`, the directory and Word sections of `skills/ingest` | `commands/obsidian-checkin.md`, `obsidian-reconcile.md`, `crew.md`, `obsidian-ingest.md` | rewritten for layers, owners and privacy; these are our own text, not copies |

Files with no changes are protected against drift: `.company-brain/upstream.json` records their sha256, `hooks/vendored_guard.py` blocks edits, and the tests and CI (`./brain upstream-check --verify`) fail if one differs.

Patterns adopted (not code): the propagation rule, bi-temporal timelines, sentinel-marked generated blocks, the kanban exception, search before create.

```
MIT License

Copyright (c) 2026 Eugeniu Ghelbur

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Obsidian community plugins (Dataview, Kanban, Templater, Calendar) are not redistributed in
this repository; each user installs them from Obsidian's community plugin directory.

Framework notes in `System/Frameworks/` are original descriptions with citations; the frameworks
and their names belong to their authors (Osterwalder and Pigneur / Strategyzer, Teresa Torres,
Richard Rumelt, A.G. Lafley and Roger Martin, Janna Bastow, Intercom, John Doerr and Andy Grove).
