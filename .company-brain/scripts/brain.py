#!/usr/bin/env python3
"""brain - the Company Brain command line.

Deterministic work for the Company Brain skills: scaffolding, note creation with
the right name and folder, generated views (OKR tree, opportunity solution trees,
effort-impact matrix, org chart, index), layer-leak and AI-first checks, source
mounts, and the Claude Project export pack.

Stdlib only and Python 3.9 compatible, so `python3 brain.py` works on a stock Mac.
Run `brain.py --help` for commands. Specs: ../references/layers.md, schemas.md.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import hashlib
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
SCAFFOLD = ENGINE / "scaffold"
TODAY = dt.date.today()

SKIP_DIRS = {".company-brain", ".obsidian", ".git", ".trash", ".claude", ".claude-plugin",
             "Templates", "Sources", "Exports", "node_modules", "__pycache__"}
EXEMPT_FILES = {"Home.md", "CLAUDE.md", "README.md", "index.md", "log.md",
                "THIRD_PARTY_NOTICES.md"}
DONE_STATUSES = {"shipped", "dropped", "done", "completed", "archived", "retired",
                 "solved", "rejected", "superseded"}
AUTO_START = "<!-- brain:auto:start {key} -->"
AUTO_END = "<!-- brain:auto:end {key} -->"


# ---------------------------------------------------------------------------
# Minimal YAML (the subset frontmatter and brain.yaml use)
# ---------------------------------------------------------------------------

def _strip_comment(s: str) -> str:
    quote = None
    for i, ch in enumerate(s):
        if quote:
            if ch == quote:
                quote = None
        elif ch in ("'", '"'):
            quote = ch
        elif ch == "#" and (i == 0 or s[i - 1] in " \t"):
            return s[:i].rstrip()
    return s.rstrip()


def _split_inline(s: str) -> list:
    items, buf, depth, quote = [], "", 0, None
    for ch in s:
        if quote:
            buf += ch
            if ch == quote:
                quote = None
            continue
        if ch in ("'", '"'):
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == "," and depth == 0:
            items.append(buf.strip())
            buf = ""
            continue
        buf += ch
    if buf.strip():
        items.append(buf.strip())
    return items


def _scalar(v: str):
    v = v.strip()
    if v == "":
        return None
    if v[0] == '"' and v.endswith('"') and len(v) >= 2:
        return v[1:-1].replace('\\"', '"')
    if v[0] == "'" and v.endswith("'") and len(v) >= 2:
        return v[1:-1].replace("''", "'")
    if v.startswith("[[") and v.endswith("]]"):
        return v
    if v.startswith("[") and v.endswith("]"):
        return [_scalar(x) for x in _split_inline(v[1:-1])]
    if v == "{}":
        return {}
    low = v.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "~"):
        return None
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v


def parse_yaml(text: str):
    toks = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        content = _strip_comment(raw)
        if not content.strip():
            continue
        toks.append((len(content) - len(content.lstrip(" ")), content.strip()))
    if not toks:
        return {}
    val, _ = _parse_block(toks, 0, toks[0][0])
    return val


def _parse_block(toks, i, indent):
    if toks[i][1] == "-" or toks[i][1].startswith("- "):
        out = []
        while i < len(toks) and toks[i][0] == indent and (toks[i][1] == "-" or toks[i][1].startswith("- ")):
            item = toks[i][1][1:].strip()
            i += 1
            if item == "":
                if i < len(toks) and toks[i][0] > indent:
                    v, i = _parse_block(toks, i, toks[i][0])
                    out.append(v)
                else:
                    out.append(None)
            elif re.match(r"^[A-Za-z_][\w\- ]*:(\s|$)", item) and not item.startswith(("[", '"', "'")):
                # a map item: first key on the dash line, the rest indented below it
                sub = [(indent + 2, item)]
                while i < len(toks) and toks[i][0] > indent:
                    sub.append(toks[i])
                    i += 1
                v, _ = _parse_block(sub, 0, indent + 2)
                out.append(v)
            else:
                out.append(_scalar(item))
        return out, i
    out = {}
    while i < len(toks) and toks[i][0] == indent:
        line = toks[i][1]
        if ":" not in line:
            i += 1
            continue
        key, _, rest = line.partition(":")
        key = key.strip().strip('"').strip("'")
        rest = rest.strip()
        i += 1
        if rest == "":
            if i < len(toks) and (toks[i][0] > indent or (toks[i][0] == indent and toks[i][1].startswith("- "))):
                v, i = _parse_block(toks, i, toks[i][0])
                out[key] = v
            else:
                out[key] = None
        else:
            out[key] = _scalar(rest)
    return out, i


def yaml_value(v) -> str:
    """Render a scalar or flat list for a frontmatter line."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return ""
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(yaml_value(x) for x in v) + "]"
    s = str(v)
    if re.fullmatch(r"[A-Za-z0-9_./ -]+", s) and not re.fullmatch(r"(true|false|yes|no|null|-?\d+(\.\d+)?)", s.lower()) and not s.startswith(("-", " ")):
        return s
    return '"' + s.replace('"', '\\"') + '"'


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------

FM_RE = re.compile(r"\A---\n(.*?)\n---\n?", re.S)
LINK_RE = re.compile(r"(!?)\[\[([^\]\|#\n]+)(#[^\]\|\n]*)?(\|[^\]\n]*)?\]\]")
CODE_RE = re.compile(r"```.*?```|`[^`\n]*`", re.S)


def split_frontmatter(text: str):
    text = text.lstrip("﻿").replace("\r\n", "\n")
    m = FM_RE.match(text)
    if not m:
        return {}, text
    try:
        fm = parse_yaml(m.group(1))
    except Exception:
        fm = {}
    return (fm if isinstance(fm, dict) else {}), text[m.end():]


def strip_code(text: str) -> str:
    return CODE_RE.sub("", text)


def link_target(s) -> str:
    """'[[A#^kr1|x]]' -> 'A'. Plain strings are returned unchanged."""
    if not isinstance(s, str):
        return ""
    m = LINK_RE.search(s)
    return (m.group(2) if m else s).strip().split("/")[-1]


def link_anchor(s) -> str:
    if not isinstance(s, str):
        return ""
    m = LINK_RE.search(s)
    return (m.group(3) or "").lstrip("#") if m else ""


def as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


class Note:
    def __init__(self, root: Path, path: Path):
        self.path = path
        self.rel = path.relative_to(root).as_posix()
        self.name = path.stem
        self.text = path.read_text(encoding="utf-8", errors="replace")
        self.fm, self.body = split_frontmatter(self.text)
        parts = self.rel.split("/")
        self.folder_layer = {"Company": "company", "Teams": "team", "Personal": "personal",
                             "System": "system"}.get(parts[0])
        self.team = parts[1] if parts[0] == "Teams" and len(parts) > 2 else None

    @property
    def type(self) -> str:
        return str(self.fm.get("type") or "")

    @property
    def layer(self) -> str:
        return str(self.fm.get("layer") or self.folder_layer or "")

    def get(self, key, default=None):
        return self.fm.get(key, default)

    def title(self) -> str:
        m = re.search(r"^# (.+)$", self.body, re.M)
        return m.group(1).strip() if m else self.name

    def summary(self) -> str:
        m = re.search(r"^## For future agent\s*\n+(.+?)(?:\n\n|\n#|\Z)", self.body, re.S | re.M)
        if not m:
            return ""
        s = " ".join(m.group(1).split())
        first = re.split(r"(?<=[.!?])\s", s, maxsplit=1)[0]
        return first if len(first) <= 180 else first[:180].rsplit(" ", 1)[0] + "..."

    def links(self):
        """[(target, anchor, is_embed)] from body and frontmatter, code removed."""
        out = []
        fm_text = FM_RE.match(self.text.lstrip("﻿").replace("\r\n", "\n"))
        for chunk in ((fm_text.group(1) if fm_text else ""), strip_code(self.body)):
            for m in LINK_RE.finditer(chunk):
                out.append((m.group(2).strip(), (m.group(3) or "").lstrip("#"), m.group(1) == "!"))
        return out


def iter_md(root: Path):
    """Notes in the brain. Follows symlinked folders: with sharing: drive, Company/ and Teams/<T>/ are links."""
    seen = set()
    for dirpath, dirnames, filenames in os.walk(root, followlinks=True):
        rel = Path(dirpath).relative_to(root)
        real = os.path.realpath(dirpath)
        if (rel.parts and rel.parts[0] in SKIP_DIRS) or real in seen:
            dirnames[:] = []
            continue
        seen.add(real)
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS and not d.startswith("."))
        for f in sorted(filenames):
            if f.endswith(".md"):
                yield Path(dirpath) / f


def scan(root: Path) -> list:
    notes = []
    for p in iter_md(root):
        try:
            notes.append(Note(root, p))
        except (OSError, UnicodeError):
            continue
    return notes


def name_index(notes) -> dict:
    """Lowercase note name (and every frontmatter alias) -> notes, as Obsidian resolves links."""
    idx = {}
    for n in notes:
        idx.setdefault(n.name.lower(), []).append(n)
        for a in as_list(n.fm.get("aliases")):
            if isinstance(a, str) and a.strip():
                idx.setdefault(a.strip().lower(), []).append(n)
    return idx


# ---------------------------------------------------------------------------
# Root, config, identity, periods
# ---------------------------------------------------------------------------

def _config_env_value(key: str) -> str:
    env_file = Path(os.environ.get("COMPANY_BRAIN_ENV_FILE") or Path.home() / ".config/company-brain/.env")
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            k, sep, v = line.strip().partition("=")
            if sep and k.strip().removeprefix("export ").strip() == key:
                return v.strip().strip('"').strip("'")
    except OSError:
        pass
    return ""


def find_root(explicit: str | None = None) -> Path | None:
    candidates = [explicit, os.environ.get("COMPANY_BRAIN_PATH"),
                  os.environ.get("CLAUDE_PLUGIN_OPTION_VAULT_PATH")]
    for c in candidates:
        if c and not c.startswith("${"):
            p = Path(c).expanduser().resolve()
            if (p / "brain.yaml").is_file():
                return p
    here = Path.cwd().resolve()
    for cand in (here, *here.parents):
        if (cand / "brain.yaml").is_file():
            return cand
    if (ENGINE.parent / "brain.yaml").is_file():
        return ENGINE.parent
    c = _config_env_value("COMPANY_BRAIN_PATH")
    if c and (Path(c).expanduser() / "brain.yaml").is_file():
        return Path(c).expanduser().resolve()
    return None


def load_config(root: Path) -> dict:
    try:
        cfg = parse_yaml((root / "brain.yaml").read_text(encoding="utf-8"))
    except OSError:
        cfg = {}
    return cfg if isinstance(cfg, dict) else {}


def period_info(day: dt.date, fy_start: int = 1) -> dict:
    fy_start = int(fy_start or 1)
    shifted = (day.month - fy_start) % 12
    q = shifted // 3 + 1
    fy = day.year + (1 if fy_start != 1 and day.month >= fy_start else 0)
    iso_year, iso_week, _ = day.isocalendar()
    week = f"{iso_year}-W{iso_week:02d}"
    monday = day - dt.timedelta(days=day.weekday())
    return {
        "date": day.isoformat(),
        "year": str(fy),
        "quarter": f"{fy}-Q{q}",
        "week": week,
        "week_start": monday.isoformat(),
        "week_end": (monday + dt.timedelta(days=6)).isoformat(),
        "daily_file": f"Personal/Daily/{day.isoformat()}.md",
        "weekly_file": f"Personal/Weekly/{week}.md",
    }


def whoami(root: Path) -> dict:
    cfg = load_config(root)
    me_path = root / "Personal" / "Me.md"
    me = {}
    if me_path.is_file():
        me, _ = split_frontmatter(me_path.read_text(encoding="utf-8"))
    company = cfg.get("company") or {}
    teams = sorted(p.name for p in (root / "Teams").iterdir() if p.is_dir()) if (root / "Teams").is_dir() else []
    info = period_info(TODAY, company.get("fiscal_year_start", 1))
    return {
        "brain": str(root),
        "engine": str(ENGINE),
        "company": company.get("name", "TBD"),
        "me": link_target(me.get("person")) if me else None,
        "my_teams": [link_target(t) for t in as_list(me.get("teams"))],
        "role": me.get("role"),
        "manager": link_target(me.get("manager")) if me.get("manager") else None,
        "timezone": me.get("timezone") or company.get("timezone"),
        "all_teams": teams,
        "sharing": (cfg.get("sharing") or {}).get("model", "local"),
        "period": info,
        "me_file_exists": me_path.is_file(),
    }


# ---------------------------------------------------------------------------
# Templates (Templater subset) and scaffolding
# ---------------------------------------------------------------------------

_MOMENT = re.compile(r"\[[^\]]*\]|YYYY|GGGG|gggg|MMMM|MMM|MM|M|DD|D|dddd|ddd|WW|ww|W|w|Q|YY")


def moment_format(day: dt.date, fmt: str) -> str:
    iso_year, iso_week, _ = day.isocalendar()

    def rep(m):
        t = m.group(0)
        if t.startswith("["):
            return t[1:-1]
        return {
            "YYYY": f"{day.year}", "YY": f"{day.year % 100:02d}", "GGGG": f"{iso_year}",
            "gggg": f"{iso_year}", "MMMM": day.strftime("%B"), "MMM": day.strftime("%b"),
            "MM": f"{day.month:02d}", "M": f"{day.month}", "DD": f"{day.day:02d}",
            "D": f"{day.day}", "dddd": day.strftime("%A"), "ddd": day.strftime("%a"),
            "WW": f"{iso_week:02d}", "ww": f"{iso_week:02d}", "W": f"{iso_week}",
            "w": f"{iso_week}", "Q": f"{(day.month - 1) // 3 + 1}",
        }[t]
    return _MOMENT.sub(rep, fmt)


_TP = re.compile(r"<%([-_]?)(\*?)(.*?)([-_]?)%>(\n?)", re.S)
_ASSIGN = re.compile(r"(?:const|let|var)\s+(\w+)\s*=\s*(?:await\s+)?tp\.system\.prompt\(\s*\"([^\"]*)\"\s*(?:,\s*\"([^\"]*)\")?[^;\n]*")


def _prompt_key(label: str) -> str:
    """Templater prompt label -> value key: 'layer: company, team or personal' -> 'layer'."""
    return re.split(r"[\s:(]", label.strip(), maxsplit=1)[0]


def render_template(text: str, title: str, values: dict, day: dt.date = TODAY) -> str:
    """Render the Templater subset Company Brain templates use, so one template
    serves Obsidian (Templater) and the CLI: tp.file.title, tp.file.cursor,
    tp.date.now(fmt[, offset]), tp.system.prompt(label[, default]), variables
    assigned from prompts inside <%* %> blocks, and -%> / _%> trimming."""
    env = {}

    def value_for(label, default):
        v = values.get(_prompt_key(label))
        if v is None:
            v = default if default is not None else "TBD"
        return v if isinstance(v, str) else yaml_value(v)

    def interp(expr):
        expr = expr.strip()
        if expr.startswith("tp.file.title"):
            return title
        if expr.startswith("tp.file.cursor"):
            return ""
        dm = re.match(r"tp\.date\.now\(\s*\"([^\"]*)\"\s*(?:,\s*(-?\d+))?\s*\)", expr)
        if dm:
            return moment_format(day + dt.timedelta(days=int(dm.group(2) or 0)), dm.group(1))
        pm = re.match(r"(?:await\s+)?tp\.system\.prompt\(\s*\"([^\"]*)\"\s*(?:,\s*\"([^\"]*)\")?", expr)
        if pm:
            return value_for(pm.group(1), pm.group(2))
        if re.fullmatch(r"\w+", expr):
            v = env.get(expr, values.get(expr))
            if v is not None:
                return v if isinstance(v, str) else yaml_value(v)
        return "TBD"

    def rep(m):
        _, is_exec, expr, trim, newline = m.groups()
        if is_exec:
            for am in _ASSIGN.finditer(expr):
                env[am.group(1)] = value_for(am.group(2), am.group(3))
            out = ""
        else:
            out = interp(expr)
        return out + ("" if trim else newline)
    return _TP.sub(rep, text)


def set_frontmatter(text: str, values: dict) -> str:
    """Set top-level scalar/flat-list keys in a note's frontmatter, keeping the rest."""
    m = FM_RE.match(text)
    if not m:
        return text
    lines = m.group(1).split("\n")
    for key, val in values.items():
        rendered = f"{key}: {yaml_value(val)}"
        for i, line in enumerate(lines):
            if re.match(rf"^{re.escape(key)}\s*:", line):
                j = i + 1
                while j < len(lines) and (lines[j].startswith((" ", "-")) and not re.match(r"^[A-Za-z_]", lines[j])):
                    j += 1
                lines[i:j] = [rendered]
                break
        else:
            lines.append(rendered)
    return "---\n" + "\n".join(lines) + "\n---\n" + text[m.end():]


def scaffold_ctx(root: Path, extra: dict | None = None) -> dict:
    who = whoami(root)
    me = who.get("me") or "TBD"
    ctx = {
        "COMPANY": who["company"], "TODAY": TODAY.isoformat(), "YEAR": who["period"]["year"],
        "QUARTER": who["period"]["quarter"], "WEEK": who["period"]["week"], "ME": me,
        "ME_FIRST": me.split(" ")[0], "ROLE": who.get("role") or "TBD",
        "TIMEZONE": who.get("timezone") or "TBD", "TEAM": "TBD", "TEAM_LEAD": "TBD",
        "MANAGER": who.get("manager") or "TBD",
    }
    ctx.update(extra or {})
    return ctx


def render_placeholders(s: str, ctx: dict) -> str:
    return re.sub(r"\{\{([A-Z_]+)\}\}", lambda m: str(ctx.get(m.group(1), m.group(0))), s)


def stamp_placeholders(root: Path) -> list[str]:
    """Fill unresolved {{TODAY}} / scaffold tokens in existing notes (template defaults).

    Only touches files that still contain {{PLACEHOLDER}} tokens. Once stamped,
    dates stay put; run again after resetting tokens in a fresh template copy.
    """
    ctx = scaffold_ctx(root)
    skip_parts = {".company-brain", ".git", ".obsidian", "Templates", "Exports", "Sources"}
    stamped = []
    for p in iter_md(root):
        if any(part in skip_parts for part in p.relative_to(root).parts):
            continue
        text = p.read_text(encoding="utf-8")
        if "{{" not in text:
            continue
        new = render_placeholders(text, ctx)
        if new != text:
            p.write_text(new, encoding="utf-8")
            stamped.append(p.relative_to(root).as_posix())
    return stamped



def render_scaffold(src: Path, dst_root: Path, ctx: dict) -> list:
    created = []
    if not src.is_dir():
        return created
    for p in sorted(src.rglob("*")):
        if p.is_dir() or p.name == ".DS_Store":
            continue
        rel = render_placeholders(p.relative_to(src).as_posix(), ctx)
        target = dst_root / rel
        if target.exists():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        if p.name == ".keep":
            target.touch()
        else:
            target.write_text(render_placeholders(p.read_text(encoding="utf-8"), ctx), encoding="utf-8")
        created.append(target.relative_to(dst_root).as_posix())
    return created


SCAFFOLD_SYSTEM_EXCLUDE = {"System/Build Plan.md"}


def scaffold_system_sources(root: Path) -> dict:
    """rel path -> vault file, for everything new brains get from scaffold/system."""
    files = [root / n for n in ("CLAUDE.md", "Home.md", ".gitignore", ".freshness.json", ".vault-config.json")]
    files += sorted((root / "System").rglob("*.md")) + sorted((root / "Templates").rglob("*.md"))
    files += sorted((root / COMMANDS_DIR).glob("*.md"))  # the generated /company-brain:<name> commands only
    obsidian = root / ".obsidian"
    files += sorted(p for p in obsidian.glob("*.json") if not p.name.startswith("workspace"))
    files += sorted(obsidian.glob("plugins/*/data.json"))
    return {p.relative_to(root).as_posix(): p for p in files
            if p.is_file() and p.relative_to(root).as_posix() not in SCAFFOLD_SYSTEM_EXCLUDE}


def scaffold_text(rel: str, text: str) -> str:
    """Vault note -> scaffold form: creation date back to {{TODAY}}, no links to excluded notes."""
    if rel.startswith("System/") or rel == "Home.md":
        m = FM_RE.match(text)
        if m:
            fm = re.sub(r"(?m)^date:.*$", "date: {{TODAY}}", m.group(1), count=1)
            text = text[:m.start(1)] + fm + text[m.end(1):]
    for ex in SCAFFOLD_SYSTEM_EXCLUDE:
        text = "\n".join(l for l in text.split("\n") if f"[[{Path(ex).stem}]]" not in l)
    return text


def sync_files(dst: Path, want: dict, have: dict, write: bool, owned=lambda path: True) -> dict:
    """Make `dst` hold `want` (rel path -> bytes). `have` maps rel path -> existing file.

    Files for which `owned(path)` is false were not written by this sync: they are never replaced or
    removed, and one standing where a wanted file should go is reported as blocked.
    """
    blocked = sorted(r for r in want if r in have and not owned(have[r]))
    added = sorted(r for r in want if r not in have)
    changed = sorted(r for r in want if r in have and r not in blocked and have[r].read_bytes() != want[r])
    removed = sorted(r for r in have if r not in want and owned(have[r]))
    if write:
        for r in added + changed:
            target = dst / r
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(want[r])
        for r in removed:
            have[r].unlink()
    return {"added": added, "changed": changed, "removed": removed, "blocked": blocked, "written": write}


def sync_report(res: dict, label: str, check: bool, in_sync: str, fix: str) -> str:
    """One report format for scaffold-sync and commands: what was (or would be) added, changed, removed."""
    if not (res["added"] or res["changed"] or res["removed"] or res["blocked"]):
        return f"{label} {in_sync}"
    verb = "Out of sync" if check else "Updated"
    text = (f"{verb}: {label} ({len(res['added'])} added, {len(res['changed'])} changed, {len(res['removed'])} removed)"
            + "".join(f"\n  + {r}" for r in res["added"]) + "".join(f"\n  ~ {r}" for r in res["changed"])
            + "".join(f"\n  - {r}" for r in res["removed"])
            + "".join(f"\n  ! {r}: written by hand, so it was left alone; rename it or delete it" for r in res["blocked"]))
    if check:
        text += f"\nRun {fix} to update it."
    return text


def scaffold_sync(root: Path, write: bool = True) -> dict:
    dst = SCAFFOLD / "system"
    want = {}
    for rel, p in scaffold_system_sources(root).items():
        data = p.read_bytes()
        want[rel] = scaffold_text(rel, data.decode("utf-8")).encode("utf-8") if rel.endswith(".md") else data
    have = {p.relative_to(dst).as_posix(): p for p in dst.rglob("*")
            if p.is_file() and p.name != ".DS_Store"} if dst.is_dir() else {}
    res = sync_files(dst, want, have, write)
    if write:
        for d in sorted((d for d in dst.rglob("*") if d.is_dir()), key=lambda d: len(d.parts), reverse=True):
            if not any(p.name != ".DS_Store" for p in d.iterdir()):
                shutil.rmtree(d)
    return {"scaffold": str(dst), **res}


# Project slash commands: Claude Code opened in the brain folder gets /company-brain:<name> from
# .claude/commands/company-brain/<name>.md (a subfolder name becomes the namespace), with or without
# the plugin and in cloud sessions, where plugins enabled by a repository do not load. Each file is a
# thin pointer to the skill's SKILL.md, generated here so the skills stay the single source of truth.
COMMANDS_DIR = Path(".claude") / "commands" / "company-brain"
COMMAND_HEADER = "<!-- Generated by ./brain commands from .company-brain/skills/{name}/SKILL.md; edit the skill, then rerun it. -->"


def parse_front_matter(text: str, strict: Path | None = None) -> tuple:
    """Top-level `key: value` front matter as (dict, body), for skills and upstream commands alike.

    A value sits on one line: plain (` #` starts a YAML comment), 'single-quoted', "double-quoted" (JSON
    escapes), or a JSON list. With `strict` (the file's path), a > or | block or a double-quoted value
    JSON cannot read stops with an error naming the file; without it such a value is kept as raw text.
    mcp/vault/vault_ops.py has its own copy (it must stay standalone); a test keeps the two in step.
    """
    m = FM_RE.match(text)
    meta = {}
    for line in (m.group(1) if m else "").splitlines():
        key, sep, value = line.partition(":")
        if not sep or line[:1].isspace() or not re.fullmatch(r"[A-Za-z][\w-]*", key):
            continue
        value = value.strip()
        double = re.fullmatch(r'("(?:[^"\\]|\\.)*"|\[.*\])\s*(?:#.*)?', value)
        single = re.fullmatch(r"'((?:[^']|'')*)'\s*(?:#.*)?", value)
        if value[:1] in (">", "|"):
            if strict:
                raise SystemExit(f"error: {strict}: write `{key}` on one line (a {value[0]} block is not supported)")
        elif double:
            try:
                value = json.loads(double.group(1))
            except ValueError:
                if strict and value.startswith('"'):
                    raise SystemExit(f"error: {strict}: `{key}` is not a valid double-quoted string "
                                     "(use only \\\" and \\\\ escapes, or leave it unquoted)") from None
        elif value.startswith('"'):
            if strict:
                raise SystemExit(f"error: {strict}: `{key}` has an unclosed double quote")
        elif single:
            value = single.group(1).replace("''", "'")
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].rstrip()
        meta[key] = value
    return meta, (text[m.end():] if m else text)


def yaml_line_value(s: str) -> str:
    """A one-line front matter value: plain when YAML reads it back unchanged, else JSON-quoted."""
    plain = (s and s == s.strip() and s[0] not in "-?:,[]{}#&*!|>'\"%@`" and ": " not in s and " #" not in s
             and not s.endswith(":") and not re.fullmatch(r"(true|false|yes|no|null|~|-?\d+(\.\d+)?)", s.lower()))
    return s if plain else json.dumps(s)


def skill_meta(path: Path) -> dict:
    """Front matter of a SKILL.md (name, description, argument-hint); see parse_front_matter."""
    return parse_front_matter(path.read_text(encoding="utf-8"), strict=path)[0]


def command_wrapper(name: str, meta: dict) -> str:
    head = [f"description: {json.dumps(meta['description'])}"]
    if meta.get("argument-hint"):
        head.append(f"argument-hint: {json.dumps(meta['argument-hint'])}")
    return (
        "---\n" + "\n".join(head) + "\n---\n\n"
        + COMMAND_HEADER.format(name=name) + "\n\n"
        f"Run the Company Brain `{name}` skill. Arguments, if any: $ARGUMENTS\n\n"
        f"1. Find the brain root: the nearest folder at or above the current one that holds `brain.yaml`. Read "
        f"`.company-brain/skills/{name}/SKILL.md` there and follow it step by step. If the brain has no "
        f"`.company-brain/`, read `skills/{name}/SKILL.md` in the engine folder named on the **Company Brain** line "
        "of the session context. If neither exists, say that the Company Brain engine was not found (open Claude in "
        "the brain folder, or install the company-brain plugin) and stop.\n"
        "2. When the skill refers to its own directory, that is the folder holding the `SKILL.md` you read. Its "
        "\"Before you start\" section says how to find the brain and how to run the `brain` CLI.\n"
    )


def commands_sync(root: Path, write: bool = True) -> dict:
    """Write one /company-brain:<name> command per skill; remove commands whose skill is gone."""
    want = {}
    for p in sorted((ENGINE / "skills").glob("*/SKILL.md")):
        if DRAFT_MARKER in p.read_text(encoding="utf-8"):
            continue  # an unfinished upstream draft gets no command until it is finished
        meta = skill_meta(p)
        if meta.get("name") != p.parent.name or not meta.get("description"):
            raise SystemExit(f"error: {p}: front matter needs name: {p.parent.name} and a description")
        want[f"{p.parent.name}.md"] = command_wrapper(p.parent.name, meta)
    dst = root / COMMANDS_DIR
    have = {p.name: p for p in dst.glob("*.md")} if dst.is_dir() else {}
    # only files this generator wrote (they carry its header) are replaced or removed; a hand-written
    # command in the folder is left alone and reported if it stands where a skill's command should go
    marker = COMMAND_HEADER.split("{name}")[0].encode("utf-8")
    res = sync_files(dst, {n: w.encode("utf-8") for n, w in want.items()}, have, write,
                     owned=lambda path: marker in path.read_bytes())
    return {"commands": COMMANDS_DIR.as_posix(), **res}


WATCH_PREFIX = "com.company-brain.scaffold-sync."
LAUNCH_AGENTS = Path.home() / "Library" / "LaunchAgents"


def watch_label(root: Path) -> str:
    return WATCH_PREFIX + hashlib.sha1(str(root.resolve()).encode()).hexdigest()[:8]


def _launchctl(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["launchctl", *args], capture_output=True, text=True)


def _watch_unload(label: str) -> None:
    _launchctl("bootout", f"gui/{os.getuid()}/{label}")
    (LAUNCH_AGENTS / f"{label}.plist").unlink(missing_ok=True)


def watch_install(root: Path, interval: int) -> dict:
    """Run scaffold-sync from launchd: on edits to the watched paths and every `interval` seconds."""
    if sys.platform != "darwin":
        raise SystemExit("error: --watch uses launchd (macOS); elsewhere schedule `./brain scaffold-sync --quiet` with cron")
    root = root.resolve()
    label = watch_label(root)
    stale = []
    for p in sorted(LAUNCH_AGENTS.glob(f"{WATCH_PREFIX}*.plist")):
        try:
            args = plistlib.loads(p.read_bytes())["ProgramArguments"]
        except Exception:
            continue
        if p.stem != label and not Path(args[1]).exists():
            _watch_unload(p.stem)
            stale.append(p.stem)
    dirs = [root / d for d in ("System", "Templates", COMMANDS_DIR.as_posix()) if (root / d).is_dir()]
    dirs += sorted(p for d in list(dirs) for p in d.rglob("*") if p.is_dir())
    paths = [root / n for n in ("CLAUDE.md", "Home.md", ".gitignore", ".obsidian")] + dirs
    log = Path.home() / "Library" / "Logs" / "company-brain" / f"{label}.log"
    spec = {
        "Label": label,
        "ProgramArguments": [sys.executable, str(ENGINE / "scripts" / "brain.py"), "--root", str(root),
                             "scaffold-sync", "--quiet"],
        "WatchPaths": [str(p) for p in paths if p.exists()],
        "StartInterval": interval,
        "RunAtLoad": True,
        "StandardOutPath": str(log),
        "StandardErrorPath": str(log),
    }
    log.parent.mkdir(parents=True, exist_ok=True)
    LAUNCH_AGENTS.mkdir(parents=True, exist_ok=True)
    _watch_unload(label)
    plist = LAUNCH_AGENTS / f"{label}.plist"
    plist.write_bytes(plistlib.dumps(spec))
    log_start = log.stat().st_size if log.exists() else 0
    for attempt in range(5):
        r = _launchctl("bootstrap", f"gui/{os.getuid()}", str(plist))
        if r.returncode == 0:
            break
        time.sleep(0.5)
    else:
        raise SystemExit(f"error: launchctl bootstrap failed: {r.stderr.strip()}")
    time.sleep(2)
    with log.open("rb") if log.exists() else open(os.devnull, "rb") as f:
        f.seek(log_start)
        blocked = b"Operation not permitted" in f.read()
    return {"label": label, "plist": str(plist), "log": str(log), "watched_paths": len(spec["WatchPaths"]),
            "interval": interval, "removed_stale": stale, "blocked": blocked, "python": sys.executable}


def watch_remove(root: Path) -> dict:
    label = watch_label(root)
    existed = (LAUNCH_AGENTS / f"{label}.plist").exists()
    _watch_unload(label)
    return {"label": label, "removed": existed}


UPSTREAM_CONF = ENGINE / "upstream.json"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def vendored_integrity(root: Path) -> list:
    """Problems with files marked mode=copy in upstream.json.

    A copy file is vendored byte for byte, so it must match the sha256 recorded when it was copied.
    Adapted files are ours to edit and are not checked here.
    """
    conf = json.loads(UPSTREAM_CONF.read_text(encoding="utf-8"))
    problems = []
    for f in conf["files"]:
        if f["mode"] != "copy":
            continue
        local = root / f["local"]
        if not local.is_file():
            problems.append(f"{f['local']}: missing")
        elif not f.get("sha256"):
            problems.append(f"{f['local']}: no sha256 recorded in upstream.json")
        elif sha256_file(local) != f["sha256"]:
            problems.append(f"{f['local']}: differs from the upstream copy recorded in upstream.json")
    return problems


def _freshness_module():
    scripts = str(Path(__file__).resolve().parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    import freshness_lint  # vendored from obsidian-second-brain, see upstream.json
    return freshness_lint


def freshness_report(root: Path, today=None) -> dict:
    """Run the vendored freshness lint (references/freshness-policy.md) over the brain."""
    return _freshness_module().lint_folder(root, today)


def freshness_findings_for(root: Path, path: Path, today=None) -> list:
    """Findings for one note, skipping what lint_folder skips (machine folders, exempt-dirs in .freshness.json)."""
    fl = _freshness_module()
    parts = path.resolve().relative_to(root.resolve()).parts
    cfg = fl.load_config(root)
    exempt = {d.strip("/") for d in cfg.get("exempt-dirs", [])}
    if path.suffix != ".md" or any(p.lower() in fl.SKIP_DIRS for p in parts):
        return []
    if any("/".join(parts[:i + 1]) in exempt for i in range(len(parts) - 1)):
        return []
    return fl.lint_file(path, "/".join(parts), cfg, today or dt.date.today())


def _git(root: Path, *args: str, check: bool = True, binary: bool = False):
    r = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=not binary)
    if check and r.returncode:
        err = r.stderr.decode() if binary else r.stderr
        raise SystemExit(f"error: git {' '.join(args)}: {err.strip()}")
    return r.stdout


# Upstream commands carry a triage decision in upstream.json "commands.map": adapted (a skill here was
# written from it), covered (an existing skill does its job), deferred (relevant, not ported yet) or
# declined (with the reason). Changes upstream to an adapted or covered command may belong in its skill.
TRACKED_DECISIONS = ("adapted", "covered")


def command_triage(root: Path, cmds: dict, ref: str) -> dict:
    """Upstream commands at `ref` against the triage record: new (untriaged), removed, and changed since triage.

    If upstream no longer has the commands folder (it moved or was renamed), nothing is guessed: the
    result says so with `missing_dir`, and --mark waits until commands.dir points at the new place.
    """
    folder = cmds.get("dir", "commands").strip("/")
    res = {"base": cmds["commit"], "playbook": cmds.get("playbook") or ".company-brain/references/upstream-sync.md",
           "dir": folder, "missing_dir": False, "new": [], "removed": [], "changed": []}
    if _git(root, "cat-file", "-t", f"{ref}:{folder}", check=False).strip() != "tree":
        res["missing_dir"] = True
        return res
    names = sorted(Path(p).stem for p in _git(root, "ls-tree", "--name-only", f"{ref}:{folder}").splitlines()
                   if p.endswith(".md"))
    triaged = cmds.get("map", {})
    # one diff for the whole folder; --no-renames keeps each path as itself
    stats = {}
    for line in _git(root, "diff", "--numstat", "--no-renames", cmds["commit"], ref, "--", f"{folder}/").splitlines():
        a, d, path = line.split("\t", 2)
        stats[path] = (int(a) if a != "-" else 0, int(d) if d != "-" else 0)
    for name, entry in sorted(triaged.items()):
        path = f"{folder}/{name}.md"
        if name in names and entry.get("decision") in TRACKED_DECISIONS and path in stats:
            res["changed"].append({"name": name, "upstream": path, "decision": entry["decision"],
                                   "skill": entry.get("skill"), "added": stats[path][0], "removed": stats[path][1]})
    res["new"] = [n for n in names if n not in triaged]
    res["removed"] = sorted(n for n in triaged if n not in names)
    return res


def triage_blockers(triage) -> list:
    """What must be triaged before --mark may record the sync."""
    if not triage:
        return []
    if triage["missing_dir"]:
        return [f"upstream has no {triage['dir']}/ folder: point commands.dir in upstream.json at where the commands moved"]
    return [f"new: {n}" for n in triage["new"]] + [f"removed upstream: {n}" for n in triage["removed"]]


# A remote of its own: in a fork or copy of this template, `upstream` usually names the template
# repository, not obsidian-second-brain, so that name is never reused.
UPSTREAM_REMOTE = "osb-upstream"


def fetch_upstream(root: Path, conf: dict) -> str:
    """Fetch obsidian-second-brain into the UPSTREAM_REMOTE remote (push disabled); return the branch ref."""
    top = _git(root, "rev-parse", "--show-toplevel", check=False).strip()
    if not top or Path(top).resolve() != root.resolve():
        raise SystemExit(f"error: {root} is not the root of a git repository; upstream-check compares git history")
    if UPSTREAM_REMOTE not in _git(root, "remote").split():
        _git(root, "remote", "add", UPSTREAM_REMOTE, conf["repo"])
    elif _git(root, "remote", "get-url", UPSTREAM_REMOTE).strip() != conf["repo"]:
        _git(root, "remote", "set-url", UPSTREAM_REMOTE, conf["repo"])
    _git(root, "remote", "set-url", "--push", UPSTREAM_REMOTE, "DISABLED")
    _git(root, "fetch", "--quiet", UPSTREAM_REMOTE, conf["branch"])
    return f"{UPSTREAM_REMOTE}/{conf['branch']}"


# --- draft a skill from an upstream command (upstream-check --draft) --------------------------------
# The draft does the mechanical part of adapting (front matter, the standard sections, upstream paths
# and tools swapped for this brain's) and marks every decision it cannot make with DRAFT_MARKER. An
# agent or a person finishes it with references/upstream-sync.md; a test fails while a marker is left.
DRAFT_MARKER = "TODO(upstream-sync)"
DRAFT_FOLDERS = {
    "daily": "`Personal/Daily/`", "weekly": "`Personal/Weekly/`", "meetings": "`<L>/Meetings/`",
    "projects": "`<L>/Projects/`", "decisions": "`<L>/Decisions/`", "ideas": "`Personal/Notes/`",
    "concepts": "`Personal/Notes/`", "entities": "`Company/Org/People/`", "people": "`Company/Org/People/`",
    "boards": "board (`Personal/My Board.md`, or `Teams/<Team>/<Team> Board.md` after asking)",
    "tasks": "board (`Personal/My Board.md`, or `Teams/<Team>/<Team> Board.md` after asking)",
}
# upstream reference files that have a counterpart here under another name
DRAFT_REFERENCES = {"write-rules.md": "propagation.md", "folder-map.md": "schemas.md"}
# what skills here may keep: the card format's middle dot, the done check, and pictographic emoji
# (priority dots, column icons). Text symbols such as a check mark or an arrow are rewritten instead.
DRAFT_ALLOWED = re.compile(r"[\u00b7\u2705\u26aa\u26ab\u2b50\ufe0f\U0001f300-\U0001faff]")
DRAFT_ASCII = {"\u2014": " - ", "\u2013": "-", "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
               "\u2192": "->", "\u2190": "<-", "\u2026": "...", "\u00d7": "x", "\u00a7": "section "}


def _draft_line(line: str, cmd_map: dict) -> tuple:
    """(rewritten line, what it could not map) for one line of an upstream command."""
    todo = []
    line = re.sub(r"`?_CLAUDE\.md`?", "`CLAUDE.md`", line)
    line = re.sub(r"\bobsidian-second-brain skill\b", "Company Brain", line)
    line = line.replace("SKILL_ROOT", "<engine>")

    def folder(m):
        kind = m.group(1).lower()
        if kind in DRAFT_FOLDERS:
            return f"the {DRAFT_FOLDERS[kind]}" + (" folder" if DRAFT_FOLDERS[kind].endswith("/`") else "")
        todo.append(f"no '{kind}' folder here: pick one from references/schemas.md")
        return f"the {kind} folder"
    # "the X folder (resolved per `references/folder-map.md` ...)", with or without the wiki/Obsidian aside
    line = re.sub(r"the (\w+) folder,? \(?resolved per `references/folder-map\.md`[^)\n]*\)?", folder, line)
    if "folder-map" in line:
        todo.append("folder lookup: use the folders in references/schemas.md")

    def reference(m):
        name = m.group(1)
        name = DRAFT_REFERENCES.get(name, name)
        if not (ENGINE / "references" / name).is_file():
            todo.append(f"references/{m.group(1)} has no counterpart here")
            return m.group(0)
        return f"references/{name}"
    line = re.sub(r"references/([\w.-]+\.md)", reference, line)
    if "Skill root" in line:
        todo.append("upstream's Skill root: the engine path is on the Company Brain line of the session context")
    line = re.sub(r"\s*\((?:wiki-style|Obsidian-style)[^)]*\)", "", line)
    for old, new in (("`Ideas/`", "`Personal/Notes/`"), ("`Daily/`", "`Personal/Daily/`"),
                     ("`wiki/daily/`", "`Personal/Daily/`")):
        line = line.replace(old, new)
    line = line.replace("`obsidian_search`", "`brain search` (or the brain MCP server's `brain_search`)")
    if re.search(r"obsidian_\w+", line):
        todo.append("an upstream MCP tool: use the brain CLI, file tools, or a brain_* MCP tool")

    def command(m):
        name = m.group(1)
        entry = cmd_map.get(name, {})
        if entry.get("decision") in TRACKED_DECISIONS:
            return f"/company-brain:{entry['skill']}"
        if name in cmd_map or name.startswith("obsidian-"):
            todo.append(f"/{name} has no skill here")
        return m.group(0)
    # a slash command, not a path segment: nothing path-like before the slash or after the name
    line = re.sub(r"(?<![\w./-])/((?:obsidian-)?[a-z][a-z-]*[a-z])(?![\w/-]|\.\w)", command, line)

    def script(m):
        name = m.group(1)
        if (ENGINE / "scripts" / name).is_file():
            return f'python3 "<engine>/scripts/{name}"'
        todo.append(f"scripts/{name} is not vendored here")
        return m.group(0)
    line = re.sub(r'uv run --directory "<engine>" scripts/(\w+\.py)', script, line)
    if "uv run" in line:
        todo.append("uv run: use python3 with a vendored script, or drop the step")
    line = re.sub(r"\bthe vault\b", "the brain", line)
    line = re.sub(r"\bvault\b", "brain", line)
    line = re.sub(r"[ \t]*\u2014[ \t]*", " - ", line)  # an em dash, spaced or not, becomes one spaced hyphen
    for old, new in DRAFT_ASCII.items():
        line = line.replace(old, new)
    if any(ord(c) > 127 and not DRAFT_ALLOWED.match(c) for c in line):
        todo.append("non-ASCII text: rewrite it in ASCII")
    return line, list(dict.fromkeys(todo))


def draft_skill(root: Path, conf: dict, ref: str, command: str, skill: str | None = None,
                skills_dir: Path | None = None) -> dict:
    """Write a first-draft SKILL.md adapted from upstream commands/<command>.md."""
    cmds = conf.get("commands") or {}
    folder = cmds.get("dir", "commands").strip("/")
    command = command.strip().lstrip("/")
    skill = skill or re.sub(r"^obsidian-", "", command)
    if not re.fullmatch(r"[a-z][a-z0-9-]*", skill):
        raise SystemExit(f"error: skill name {skill!r}: use lowercase letters, digits and hyphens")
    skills_dir = skills_dir or ENGINE / "skills"
    target = skills_dir / skill / "SKILL.md"
    if target.exists():
        raise SystemExit(f"error: {target} exists; pass --as <another-name>, or port the change into that skill by hand")
    raw = _git(root, "show", f"{ref}:{folder}/{command}.md", check=False)
    if not raw:
        raise SystemExit(f"error: upstream has no {folder}/{command}.md at {ref}")
    meta, body = parse_front_matter(raw)
    # upstream wraps every command in the same intro and closing rules; the skill sections replace both
    body = re.sub(r"(?m)^Use the obsidian-second-brain skill\. Execute .*\n+", "", body)
    body = re.split(r"\n---\n+\*\*AI-first rule:\*\*", body)[0]
    body = re.sub(r"(?ms)^\*\*(?:AI-first rule|Anti-fabrication):\*\*.*?(?:\n\n|\Z)", "", body)
    # the "read _CLAUDE.md first" step is covered by Before you start; drop it only when it says nothing else
    body = re.sub(r"(?m)^[ \t]*\d+[a-z]?\.[ \t]+Read `?_CLAUDE\.md`? first(?: if it exists(?: in the vault root)?)?\.?[ \t]*\n",
                  "", body)
    cmd_map = cmds.get("map", {})
    out, fence, held = [], None, []
    for raw_line in body.strip().splitlines():
        line, todo = _draft_line(raw_line, cmd_map)
        opener = re.match(r"([ \t]*)(```|~~~)", raw_line)
        if opener and fence is None:
            fence = opener.group(1)  # markers inside a code block wait below it, so the code stays runnable
            out.append(line + "".join(f" {DRAFT_MARKER}: {x}." for x in todo))
        elif fence is not None:
            out.append(line)
            held += todo
            if opener:
                out += [f"{fence}{DRAFT_MARKER}: {x} (in the code block above)." for x in dict.fromkeys(held)]
                fence, held = None, []
        else:
            out.append(line + "".join(f" {DRAFT_MARKER}: {x}." for x in todo))
    out += [f"{DRAFT_MARKER}: {x} (in the code block above)." for x in dict.fromkeys(held)]
    steps = "\n".join(out)
    desc, desc_todo = _draft_line(" ".join(str(meta.get("description", "")).split()), cmd_map)
    desc = desc.rstrip(".") or "TBD"
    triggers = [x for x in meta.get("triggers_en", []) if isinstance(x, str)]
    desc += "." + (" Use for " + ", ".join(f'"{x}"' for x in triggers) + "." if triggers else "")
    shared = (ENGINE / "skills" / "daily" / "SKILL.md").read_text(encoding="utf-8")
    before = shared[shared.index("## Before you start"):shared.index("## Steps")]
    always = shared[shared.index("## Always"):]
    hint = meta.get("argument-hint")
    title = skill.replace("-", " ").capitalize()
    head = _git(root, "rev-parse", "--short", ref).strip()
    text = (
        f"---\nname: {skill}\ndescription: {yaml_line_value(desc)}\n"
        + (f"argument-hint: {json.dumps(str(hint))}\n" if hint else "")
        # a draft only runs when typed: Claude must not start it on its own before it is reviewed
        + f"disable-model-invocation: true  # {DRAFT_MARKER}: delete this line when the draft is finished\n"
        + f"---\n\n# {title}\n\n"
        f"{DRAFT_MARKER}: first draft written by `./brain upstream-check --draft {command}` from upstream "
        f"`{folder}/{command}.md` at {head}. Finish it with `.company-brain/references/upstream-sync.md`, resolve "
        f"every {DRAFT_MARKER} marker, then replace this paragraph with what the skill does here.\n\n"
        + before
        + "## Adaptation checklist\n"
        + "".join(f"- [ ] {DRAFT_MARKER}: in the description, {x}.\n" for x in desc_todo)
        +
        f"- [ ] {DRAFT_MARKER}: for every note this skill writes, name the layer (personal by default) and where a "
        "shared write needs the user's yes (`references/layers.md`).\n"
        f"- [ ] {DRAFT_MARKER}: check each step against this brain's folders, note types and CLI "
        "(`references/schemas.md`, `brain new`, `brain period`, `brain search`) and its propagation rules "
        "(`references/propagation.md`).\n"
        f"- [ ] {DRAFT_MARKER}: ASCII punctuation only, no hard-coded dates or years.\n"
        f"- [ ] {DRAFT_MARKER}: wire it in (CLAUDE.md section 4, System/Skills.md, the README count, `./brain commands`, "
        "`upstream.json` commands.map as adapted), then delete this checklist.\n\n"
        "## Steps\n" + steps + "\n\n" + always
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return {"command": command, "skill": skill, "path": str(target), "upstream": f"{folder}/{command}.md",
            "commit": head, "todos": text.count(DRAFT_MARKER)}


def upstream_check(root: Path, diff: bool = False, copy: bool = False, mark: bool = False) -> dict:
    """Which files Company Brain borrowed from obsidian-second-brain changed upstream since the recorded commit."""
    conf = json.loads(UPSTREAM_CONF.read_text(encoding="utf-8"))
    ref = fetch_upstream(root, conf)
    base, head = conf["commit"], _git(root, "rev-parse", ref).strip()
    changed = []
    for f in conf["files"]:
        # a file vendored later than the rest carries its own "commit" until the next --mark
        rows = [l.split("\t") for l in _git(root, "diff", "--numstat", f.get("commit", base), ref, "--", f["upstream"]).splitlines() if l]
        if rows:
            changed.append({**f, "added": sum(int(a) for a, _, _ in rows if a != "-"),
                            "removed": sum(int(d) for _, d, _ in rows if d != "-"), "paths": [p for _, _, p in rows]})
    res = {"repo": conf["repo"], "ref": ref, "base": base, "head": head,
           "commits": int(_git(root, "rev-list", "--count", f"{base}..{ref}").strip()), "changed": changed}
    triage = command_triage(root, conf["commands"], ref) if conf.get("commands") else None
    if triage:
        res["commands"] = triage
    # refuse --mark before --copy touches anything, so a refused run leaves no half-applied sync
    blockers = triage_blockers(triage) if mark else []
    if blockers:
        raise SystemExit("error: triage the upstream commands first (" + "; ".join(blockers)
                         + f"), as {triage['playbook']} says, then --mark again")
    if diff and (changed or (triage and triage["changed"])):
        res["diff"] = "".join(_git(root, "diff", f.get("commit", base), ref, "--", f["upstream"]) for f in changed)
        res["diff"] += "".join(_git(root, "diff", triage["base"], ref, "--", c["upstream"])
                               for c in (triage["changed"] if triage else []))
    if copy:
        res["copied"] = []
        for f in changed:
            if f["mode"] == "copy":
                target = root / f["local"]
                target.write_bytes(_git(root, "show", f"{ref}:{f['upstream']}", binary=True))
                for entry in conf["files"]:
                    if entry["local"] == f["local"]:
                        entry["sha256"] = sha256_file(target)  # keep the integrity guard in step with the copy
                        entry["commit"] = head  # this file is now current; the next --mark clears it
                res["copied"].append(f["local"])
        if res["copied"]:
            UPSTREAM_CONF.write_text(json.dumps(conf, indent=2) + "\n", encoding="utf-8")
    if mark:
        conf["commit"] = head
        if triage:
            conf["commands"]["commit"] = head
        for entry in conf["files"]:
            entry.pop("commit", None)
        UPSTREAM_CONF.write_text(json.dumps(conf, indent=2) + "\n", encoding="utf-8")
        res["marked"] = head
    return res


def _set_brain_yaml(root: Path, section: str, key: str, value: str) -> None:
    path = root / "brain.yaml"
    lines = path.read_text(encoding="utf-8").split("\n")
    in_section = False
    for i, line in enumerate(lines):
        if re.match(rf"^{section}:\s*$", line):
            in_section = True
            continue
        if in_section and re.match(r"^\S", line):
            break
        if in_section and re.match(rf"^\s+{key}:", line):
            indent = line[: len(line) - len(line.lstrip())]
            comment = line[len(_strip_comment(line)):]
            lines[i] = f"{indent}{key}: {yaml_value(_scalar(value) if value.isdigit() else value)}{comment}"
            break
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Note creation (brain new)
# ---------------------------------------------------------------------------

KINDS = {
    # kind: (template file, default layer, subfolder within the layer)
    "objective": ("Objective Template.md", "company", "OKRs"),
    "annual-plan": ("Annual Plan Template.md", "company", "Planning"),
    "quarterly-plan": ("Quarterly Plan Template.md", "company", "Planning"),
    "strategy": ("Strategy Kernel Template.md", "company", "Strategy"),
    "playing-to-win": ("Playing to Win Template.md", "company", "Strategy"),
    "vpc": ("Value Proposition Canvas Template.md", "company", "Strategy"),
    "bmc": ("Business Model Canvas Template.md", "company", "Strategy"),
    "outcome": ("OST Outcome Template.md", "company", "Discovery"),
    "opportunity": ("OST Opportunity Template.md", "company", "Discovery"),
    "solution": ("OST Solution Template.md", "company", "Discovery"),
    "experiment": ("OST Experiment Template.md", "company", "Discovery"),
    "project": ("Project Template.md", "company", "Projects"),
    "meeting": ("Meeting Template.md", "company", "Meetings"),
    "decision": ("Decision Template.md", "company", "Decisions"),
    "knowledge": ("Knowledge Note Template.md", "personal", "Knowledge"),
    "person": ("Person Template.md", "company", "Org/People"),
    "one-on-one": ("One-on-One Template.md", "personal", "1-1s"),
    "daily": ("Daily Note Template.md", "personal", "Daily"),
    "weekly": ("Weekly Note Template.md", "personal", "Weekly"),
    "team-update": ("Team Update Template.md", "team", "Weekly"),
    "team-weekly": ("Team Weekly Template.md", "team", "Weekly"),
}
PERSONAL_SUBFOLDER = {"objective": "Goals", "knowledge": "Notes", "decision": "Decisions",
                      "meeting": "Meetings", "project": "Projects"}


def layer_root(root: Path, layer: str, team: str | None) -> Path:
    if layer == "company":
        return root / "Company"
    if layer == "team":
        if not team:
            raise SystemExit("error: --team is required for the team layer")
        if not (root / "Teams" / team).is_dir():
            raise SystemExit(f"error: no team folder Teams/{team} (create it with: brain team add \"{team}\")")
        return root / "Teams" / team
    if layer == "personal":
        return root / "Personal"
    raise SystemExit(f"error: unknown layer {layer!r} (company | team | personal)")


def note_name(kind: str, title: str, v: dict, who: dict) -> str:
    p = who["period"]
    owner_label = v.get("owner_label") or (
        "Company" if v["layer"] == "company" else v.get("team") if v["layer"] == "team"
        else (who.get("me") or "Me").split(" ")[0])
    if kind == "objective":
        n = v.get("n") or "1"
        prefix = "G" if v["layer"] == "personal" else "O"
        return f"{v.get('period') or p['quarter']} - {owner_label} - {prefix}{n} - {title}"
    if kind == "annual-plan":
        base = f"Annual Plan {v.get('period') or p['year']}"
        return f"{v['team']} - {base}" if v["layer"] == "team" else base
    if kind == "quarterly-plan":
        base = f"Quarterly Plan {v.get('period') or p['quarter']}"
        return f"{v['team']} - {base}" if v["layer"] == "team" else base
    prefixes = {"outcome": "OUT - ", "opportunity": "OPP - ", "solution": "SOL - ",
                "experiment": "EXP - ", "vpc": "VPC - ", "bmc": "BMC - ",
                "strategy": "Strategy - ", "playing-to-win": "Strategy - ", "one-on-one": "1-1 - "}
    if kind in prefixes:
        return prefixes[kind] + title
    if kind == "meeting":
        return f"{v.get('date') or p['date']} - {title}"
    if kind == "decision":
        return f"DEC-{v.get('date') or p['date']} - {title}"
    if kind == "daily":
        return v.get("date") or p["date"]
    if kind == "weekly":
        return v.get("week") or p["week"]
    if kind == "team-update":
        return f"{v.get('week') or p['week']} - {v['team']} - {v.get('author_label') or who.get('me') or 'TBD'}"
    if kind == "team-weekly":
        return f"{v.get('week') or p['week']} - {v['team']} - Team Weekly"
    return title


def create_note(root: Path, kind: str, title: str, layer: str | None = None, team: str | None = None,
                values: dict | None = None, name: str | None = None, write: bool = True) -> dict:
    if kind not in KINDS:
        raise SystemExit(f"error: unknown kind {kind!r}. Kinds: {', '.join(sorted(KINDS))}")
    tpl_file, default_layer, sub = KINDS[kind]
    who = whoami(root)
    layer = layer or default_layer
    if layer == "team" and not team:
        team = (who.get("my_teams") or [None])[0]
    values = dict(values or {})
    if layer == "personal":
        sub = PERSONAL_SUBFOLDER.get(kind, sub)
    if kind == "person":
        layer, team, sub = "company", None, "Org/People"
    folder = layer_root(root, layer, team) / sub
    route = dict(values, layer=layer, team=team)
    stem = name or note_name(kind, title, route, who)
    stem = re.sub(r'[\\/:*?"<>|#^\[\]]', "-", stem).strip()
    target = folder / f"{stem}.md"
    # search-before-create: same filename anywhere means it already exists
    existing = [n for n in scan(root) if n.name.lower() == stem.lower()]
    if existing:
        return {"created": False, "path": existing[0].rel, "reason": "a note with this name already exists"}
    tpl = root / "Templates" / tpl_file
    if not tpl.is_file():
        raise SystemExit(f"error: template not found: Templates/{tpl_file}")
    prompt_values = {k: v for k, v in values.items() if v is not None}
    prompt_values.setdefault("team", team or "TBD")
    prompt_values.setdefault("me", f"[[{who['me']}]]" if who.get("me") else "TBD")
    prompt_values["layer"] = layer
    prompt_values.setdefault("week", who["period"]["week"])
    prompt_values.setdefault("period", who["period"]["year"] if kind == "annual-plan" else who["period"]["quarter"])
    text = render_template(tpl.read_text(encoding="utf-8"), stem, prompt_values)
    if layer != "team" and kind != "person":
        text = re.sub(r"^team: *(TBD|\"\[\[TBD\]\]\"|)? *\n", "", text, count=1, flags=re.M)
    fm_set = {"date": values.get("date") or TODAY.isoformat(), "layer": layer}
    if kind == "objective":
        fm_set["level"] = layer
    if layer == "team" and team:
        fm_set["team"] = f"[[{team}]]"
    for k, v in values.items():
        if k in ("layer", "n", "owner_label", "author_label", "date") or v is None:
            continue
        fm_set[k] = v
    text = set_frontmatter(text, fm_set)
    if title and kind not in ("daily", "weekly"):
        text = re.sub(r"^# .*$", f"# {stem}", text, count=1, flags=re.M)
    if not write:
        return {"created": False, "path": target.relative_to(root).as_posix(), "text": text}
    folder.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    append_log(root, f"created {target.relative_to(root).as_posix()} ({kind})")
    return {"created": True, "path": target.relative_to(root).as_posix()}


def append_log(root: Path, line: str) -> None:
    try:
        log = root / "log.md"
        stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
        if not log.exists():
            log.write_text("# Operation log\n\nLocal only (gitignored). One line per brain write.\n\n", encoding="utf-8")
        with log.open("a", encoding="utf-8") as fh:
            fh.write(f"- {stamp} {line}\n")
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Promotion (brain promote): the only path from Personal/ to a shared layer
# ---------------------------------------------------------------------------

PERSONAL_ONLY_FIELDS = ("energy", "mood", "promoted_to")
PERSONAL_ONLY_KINDS = ("daily", "weekly", "one-on-one")
TEAM_ONLY_KINDS = ("team-update", "team-weekly")
NOT_PROMOTABLE = {
    "me": "the identity record stays in Personal/",
    "daily": "daily notes are not shared; promote the meeting, decision, or knowledge note that came out of the day",
    "one-on-one": "1:1 notes stay in Personal/; promote a decision or meeting note instead",
    "objective": "a personal goal becomes a team objective through the okr skill, with the team lead",
    "person": "people profiles already live in Company/Org/People",
}
TYPE_KIND = {"plan": "quarterly-plan"}
UPDATE_SECTIONS = {"highlights": "Highlights", "kr progress": "KR progress",
                   "next week": "Next week", "help needed": "Help needed"}
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")


def _split_head(text: str):
    m = FM_RE.match(text)
    return (text[:m.end()], text[m.end():]) if m else ("", text)


def _headings(lines):
    """[(line index, level, title)] for headings outside code fences."""
    out, fence = [], False
    for i, line in enumerate(lines):
        if FENCE_RE.match(line):
            fence = not fence
            continue
        m = None if fence else HEADING_RE.match(line)
        if m:
            out.append((i, len(m.group(1)), m.group(2)))
    return out


def _section_span(lines, title_re: str, level: int = 2):
    """(start, end) line span of the first section whose heading matches, heading included."""
    heads = _headings(lines)
    for k, (i, lvl, title) in enumerate(heads):
        if lvl == level and re.fullmatch(title_re, title, re.I):
            end = next((j for j, l2, _ in heads[k + 1:] if l2 <= level), len(lines))
            return i, end
    return None


def drop_private(body: str):
    """Remove every `# Private` / `## Private` section (to the next heading of the same or higher level)."""
    lines = body.split("\n")
    heads = _headings(lines)
    drop = set()
    for k, (i, lvl, title) in enumerate(heads):
        if lvl <= 2 and title.lower() == "private":
            end = next((j for j, l2, _ in heads[k + 1:] if l2 <= lvl), len(lines))
            drop.update(range(i, end))
    count = sum(1 for i, lvl, t in heads if lvl <= 2 and t.lower() == "private")
    kept = [l for i, l in enumerate(lines) if i not in drop]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).rstrip() + "\n", count


def unlink_personal(text: str, idx: dict):
    """Rewrite links to Personal/ notes as plain text (alias or note name), outside code."""
    found = []

    def rep(m):
        target = m.group(2).strip()
        hits = idx.get(target.split("/")[-1].lower(), [])
        if not (target.startswith("Personal/") or (hits and all(h.folder_layer == "personal" for h in hits))):
            return m.group(0)
        found.append(target.split("/")[-1])
        return m.group(4)[1:].strip() if m.group(4) else target.split("/")[-1]

    parts, pos = [], 0
    for c in CODE_RE.finditer(text):
        parts += [LINK_RE.sub(rep, text[pos:c.start()]), c.group(0)]
        pos = c.end()
    parts.append(LINK_RE.sub(rep, text[pos:]))
    return "".join(parts), found


def drop_frontmatter_keys(text: str, keys):
    m = FM_RE.match(text)
    if not m:
        return text, []
    out, dropped, skipping = [], [], False
    for line in m.group(1).split("\n"):
        km = re.match(r"^([A-Za-z_][\w-]*)\s*:", line)
        if km:
            skipping = km.group(1) in keys
            if skipping:
                dropped.append(km.group(1))
                continue
        elif skipping:
            continue
        out.append(line)
    return "---\n" + "\n".join(out) + "\n---\n" + text[m.end():], dropped


def replace_section(text: str, title: str, content: list) -> str:
    lines = text.split("\n")
    span = _section_span(lines, re.escape(title))
    if not span:
        return text
    start, end = span
    return "\n".join(lines[:start + 1] + content + [""] + lines[end:])


def find_note(root: Path, notes, ref: str) -> Note:
    p = Path(ref).expanduser()
    for cand in ((p if p.is_absolute() else root / p), (p if p.is_absolute() else root / p).with_suffix(".md")):
        if cand.is_file():
            rel = cand.resolve().relative_to(root.resolve()).as_posix()
            hit = next((n for n in notes if n.rel == rel), None)
            if hit:
                return hit
    hits = [n for n in notes if n.name.lower() == Path(ref).stem.lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        raise SystemExit(f"error: no note named or at {ref!r}")
    raise SystemExit(f"error: {ref!r} is ambiguous: " + ", ".join(n.rel for n in hits) + " (pass the path)")


def _team_update_from_weekly(root: Path, src: Note, team: str, who: dict, name: str | None):
    lines = src.body.split("\n")
    span = _section_span(lines, r"Team update\b.*")
    if not span:
        raise SystemExit(f"error: {src.rel} has no `## Team update` section; draft it with the weekly skill first")
    draft, _ = drop_private("\n".join(lines[span[0] + 1:span[1]]))
    sections, current = {}, None
    for line in draft.split("\n"):
        lm = re.match(r"^\s*[-*]\s+(Highlights|KR progress|Next week|Help needed)\s*:\s*(.*)$", line, re.I)
        if lm:
            current = UPDATE_SECTIONS[lm.group(1).lower()]
            sections.setdefault(current, [])
            if lm.group(2).strip():
                sections[current].append(f"- {lm.group(2).strip()}")
        elif line.strip():
            sections.setdefault(current or "Highlights", []).append(line)
    sections = {t: ls for t, ls in sections.items() if any(re.sub(r"[-*\s]|TBD", "", l) for l in ls)}
    if not sections:
        raise SystemExit(f"error: the team update draft in {src.rel} is empty or TBD")
    me = who.get("me")
    if not me or me == "TBD":
        raise SystemExit("error: Personal/Me.md has no person; set it first (brain init --me \"Full Name\") so the update has an author")
    res = create_note(root, "team-update", "", layer="team", team=team, name=name, write=False,
                      values={"author": f"[[{me}]]", "week": str(src.get("week") or src.name),
                              "krs": as_list(src.get("krs"))})
    if "text" not in res:
        return res, []
    text = res["text"]
    for title, content in sections.items():
        text = replace_section(text, title, content)
    dropped = [t for i, lvl, t in _headings(lines) if lvl == 2 and i != span[0] and t.lower() != "private"]
    return dict(res, text=text), dropped


def promote(root: Path, ref: str, to: str, team: str | None = None, kind: str | None = None,
            name: str | None = None, write: bool = False) -> dict:
    notes = scan(root)
    src = find_note(root, notes, ref)
    if src.folder_layer not in ("personal", "team"):
        raise SystemExit(f"error: {src.rel} is not in Personal/ or Teams/; only personal and team notes are promoted")
    if src.folder_layer == "team" and to != "company":
        raise SystemExit("error: team notes are promoted to the company layer (--to company)")
    if src.get("promoted_to"):
        raise SystemExit(f"error: {src.rel} was already promoted to {src.get('promoted_to')}; edit the shared note instead")
    if not src.fm:
        raise SystemExit(f"error: {src.rel} has no frontmatter; add date, type, tags, ai-first, and layer first")
    ntype = src.type
    kind = kind or ("team-update" if ntype == "weekly" else TYPE_KIND.get(ntype, ntype))
    for k in (ntype, kind):
        if k in NOT_PROMOTABLE:
            raise SystemExit(f"error: {k} notes are not promoted: {NOT_PROMOTABLE[k]}")
    if kind in PERSONAL_ONLY_KINDS:
        raise SystemExit(f"error: {kind} is a personal-only kind; pick a shared --kind")
    if kind not in KINDS:
        raise SystemExit(f"error: no target folder for type {ntype!r}; pass --kind (one of: "
                         + ", ".join(k for k in sorted(KINDS) if k not in PERSONAL_ONLY_KINDS + tuple(NOT_PROMOTABLE)) + ")")
    if kind in TEAM_ONLY_KINDS and to != "team":
        raise SystemExit(f"error: {kind} notes belong to a team (--to team)")
    who = whoami(root)
    if to == "team":
        team = team or (who.get("my_teams") or [None])[0]
        if not team:
            raise SystemExit("error: --team is required (no home team in Personal/Me.md)")
        layer_root(root, "team", team)
    else:
        team = None
    src_text = src.text.lstrip("\ufeff").replace("\r\n", "\n")
    removed = {"private_sections": 0, "sections": [], "personal_links": [], "fields": []}

    if kind == "team-update" and ntype == "weekly":
        res, removed["sections"] = _team_update_from_weekly(root, src, team, who, name)
        if "text" not in res:
            return res
        rel, text = res["path"], res["text"]
        removed["private_sections"] = drop_private(src.body)[1]
    else:
        head, body = _split_head(src_text)
        body, removed["private_sections"] = drop_private(body)
        text, dropped = drop_frontmatter_keys(head + body, PERSONAL_ONLY_FIELDS + (("team",) if to == "company" else ()))
        removed["fields"] = [d for d in dropped if d != "team"]
        fm_set = {"layer": to}
        if to == "team":
            fm_set["team"] = f"[[{team}]]"
        tags = as_list(src.get("tags"))
        if "private" in tags:
            fm_set["tags"] = [t for t in tags if t != "private"]
            removed["fields"].append("tag private")
        text = set_frontmatter(text, fm_set)
        stem = re.sub(r'[\\/:*?"<>|#^\[\]]', "-", name or src.name).strip()
        folder = layer_root(root, to, team) / KINDS[kind][2]
        rel = (folder / f"{stem}.md").relative_to(root).as_posix()
        clash = [n for n in notes if n.name.lower() == stem.lower() and n.folder_layer != "personal"]
        if clash:
            return {"created": False, "path": clash[0].rel, "reason": "a shared note with this name already exists"}

    text, removed["personal_links"] = unlink_personal(text, name_index(notes))
    diff = "".join(difflib.unified_diff(src_text.splitlines(True), text.splitlines(True),
                                        fromfile=src.rel, tofile=rel))
    out = {"created": False, "dry_run": not write, "source": src.rel, "path": rel, "kind": kind,
           "layer": to, "team": team, "removed": removed, "diff": diff, "text": text, "errors": []}
    if not write:
        return out
    target = root / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    src.path.write_text(set_frontmatter(src_text, {"promoted_to": f"[[{rel[:-3]}]]"}), encoding="utf-8")
    append_log(root, f"promoted to {rel} ({kind}, {to} layer)")
    out["created"] = True
    out["errors"] = [i for i in check(root) if i["path"] == rel and i["severity"] == "error"]
    return out


# ---------------------------------------------------------------------------
# Auto blocks
# ---------------------------------------------------------------------------

def write_auto_block(path: Path, key: str, content: str, header: str) -> str:
    start, end = AUTO_START.format(key=key), AUTO_END.format(key=key)
    block = f"{start}\n{content.rstrip()}\n{end}"
    if path.exists():
        text = path.read_text(encoding="utf-8")
        if start in text and end in text:
            pre, rest = text.split(start, 1)
            _, post = rest.split(end, 1)
            new = pre + block + post
        else:
            new = text.rstrip() + "\n\n" + block + "\n"
        if new != text:
            path.write_text(new, encoding="utf-8")
            return "updated"
        return "unchanged"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header.rstrip() + "\n\n" + block + "\n", encoding="utf-8")
    return "created"


def generated_header(ntype: str, title: str, layer: str, purpose: str, team: str | None = None) -> str:
    team_line = f'team: "[[{team}]]"\n' if team else ""
    return (f"---\ndate: {TODAY.isoformat()}\ntype: {ntype}\ntags: [{ntype}, generated]\n"
            f"ai-first: true\nlayer: {layer}\n{team_line}generated_by: brain refresh\n---\n\n"
            f"# {title}\n\n## For future agent\n{purpose} Content between the `brain:auto` markers is "
            f"regenerated by `brain refresh`; edit the source notes, not this view.\n")


def mermaid_label(s: str) -> str:
    return s.replace('"', "#quot;").replace("[", "(").replace("]", ")")


# ---------------------------------------------------------------------------
# OKRs
# ---------------------------------------------------------------------------

KR_LINE = re.compile(r"^\s*[-*]\s+(?:\[[ xX]\]\s+)?(.*?)\s*\^(kr\d+)\s*$")
FIELD = re.compile(r"\[([a-z_]+)::\s*([^\]]*(?:\]\][^\]]*)?)\]")


def _num(v):
    try:
        return float(str(v).replace(",", "").replace("%", "").strip())
    except (TypeError, ValueError):
        return None


def parse_krs(note: Note) -> list:
    krs = []
    sec = re.search(r"^## Key results\s*\n(.*?)(?=^## |\Z)", note.body, re.S | re.M)
    if not sec:
        return krs
    for line in sec.group(1).splitlines():
        m = KR_LINE.match(line)
        if not m:
            continue
        text, block = m.group(1), m.group(2)
        fields = {k: v.strip() for k, v in FIELD.findall(text)}
        label = FIELD.sub("", text).strip()
        label = re.sub(r"^\*\*KR\d+\*\*\s*", "", re.sub(r"\s+", " ", label))
        krs.append({"id": block, "label": label, "fields": fields,
                    "checked": bool(re.match(r"^\s*[-*]\s+\[[xX]\]", line)),
                    "progress": kr_progress(fields, bool(re.match(r"^\s*[-*]\s+\[[xX]\]", line)))})
    return krs


def kr_progress(f: dict, checked: bool = False):
    p = _num(f.get("progress"))
    if p is not None:
        return max(0.0, min(1.0, p / 100 if p > 1 else p))
    b, t, c = _num(f.get("baseline")), _num(f.get("target")), _num(f.get("current"))
    if t is not None and c is not None:
        b = b if b is not None else 0.0
        if t == b:
            return None  # placeholder or malformed KR: no defined progress
        return max(0.0, min(1.0, (c - b) / (t - b)))
    return 1.0 if checked else None


def _real_link(v) -> str:
    """Link target, or '' for empty and TBD placeholders."""
    target = link_target(v) if v else ""
    return "" if target.strip().upper() in ("", "TBD") else target


def okr_model(notes) -> dict:
    objs = {}
    for n in notes:
        if n.type != "objective":
            continue
        krs = parse_krs(n)
        scores = [k["progress"] for k in krs if k["progress"] is not None]
        objs[n.name.lower()] = {
            "note": n, "name": n.name, "level": str(n.get("level") or n.layer),
            "period": str(n.get("period") or ""), "status": str(n.get("status") or ""),
            "owner": link_target(n.get("owner")), "parent": _real_link(n.get("parent")),
            "parent_kr": link_anchor(n.get("parent")) if _real_link(n.get("parent")) else "",
            "krs": krs, "score": round(sum(scores) / len(scores), 2) if scores else None,
            "last_checkin": str(n.get("last_checkin") or ""), "children": [],
        }
    for o in objs.values():
        p = objs.get(o["parent"].lower()) if o["parent"] else None
        if p:
            p["children"].append(o)
    return objs


def _period_match(o_period: str, period: str, year: str) -> bool:
    return o_period in (period, year) or (o_period.startswith(year) and period == year)


def render_okr_tree(objs: dict, period: str, include_personal: bool = False) -> str:
    """Cascade for a period. Shared trees (include_personal=False) never list personal
    goals: the tree lives in Company/ and a link to Personal/ would be a leak."""
    year = period.split("-")[0]
    in_scope = {k: o for k, o in objs.items() if _period_match(o["period"], period, year)
                and (include_personal or (o["level"] != "personal" and o["note"].folder_layer != "personal"))}
    roots = [o for o in in_scope.values()
             if not o["parent"] or o["parent"].lower() not in in_scope]
    order = {"company": 0, "team": 1, "personal": 2}
    roots.sort(key=lambda o: (order.get(o["level"], 3), o["period"], o["name"]))
    lines = [f"Period: **{period}** (with {year} annual objectives). Score is the mean KR progress, 0.0 to 1.0. "
             f"Generated {TODAY.isoformat()}.", ""]

    def fmt_score(s):
        return "no data" if s is None else f"{s:.2f}"

    def walk(o, depth):
        ind = "  " * depth
        status = f", {o['status']}" if o["status"] else ""
        lines.append(f"{ind}- [[{o['name']}]] ({o['level']}, score {fmt_score(o['score'])}{status})")
        kr_ids = {kr["id"] for kr in o["krs"]}
        for kr in o["krs"]:
            owner = link_target(kr["fields"].get("owner", "")) if kr["fields"].get("owner") else ""
            conf = kr["fields"].get("confidence", "")
            extra = ", ".join(x for x in [f"progress {fmt_score(kr['progress'])}", conf and f"confidence {conf}",
                                          owner and f"owner [[{owner}]]"] if x)
            lines.append(f"{ind}  - {kr['id'].upper()} {kr['label']} ({extra})")
            for c in sorted(o["children"], key=lambda c: c["name"]):
                if c["parent_kr"] == kr["id"] and c["name"].lower() in in_scope:
                    walk(c, depth + 2)
        for c in sorted(o["children"], key=lambda c: c["name"]):
            if c["parent_kr"] not in kr_ids and c["name"].lower() in in_scope:
                walk(c, depth + 1)

    if not roots:
        lines.append("No objectives found for this period yet. Create one with `/company-brain:okr`.")
    for r in roots:
        walk(r, 0)
    unaligned = [o for o in in_scope.values() if o["level"] in ("team", "personal") and not o["parent"]]
    if unaligned:
        lines += ["", "### Not aligned to a parent", ""]
        lines += [f"- [[{o['name']}]] ({o['level']}) has no `parent:`" for o in sorted(unaligned, key=lambda o: o["name"])]
    # mermaid
    nodes, edges, ids = [], [], {}
    for i, o in enumerate(sorted(in_scope.values(), key=lambda o: o["name"])):
        ids[o["name"].lower()] = f"o{i}"
        short = o["name"].split(" - ")[-1]
        nodes.append(f'  o{i}["{mermaid_label(short)}<br/>{o["level"]} {fmt_score(o["score"])}"]:::{o["level"]}')
    for o in in_scope.values():
        if o["parent"].lower() in ids:
            edges.append(f"  {ids[o['parent'].lower()]} --> {ids[o['name'].lower()]}")
    if nodes:
        lines += ["", "### Cascade", "", "```mermaid", "flowchart LR"] + nodes + edges + [
            "  classDef company fill:#dbeafe,stroke:#1d4ed8", "  classDef team fill:#dcfce7,stroke:#15803d",
            "  classDef personal fill:#ffedd5,stroke:#c2410c", "```"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Opportunity solution trees
# ---------------------------------------------------------------------------

OST_TYPES = ("outcome", "opportunity", "solution", "experiment")
CANVAS_COLOR = {"outcome": "6", "opportunity": "5", "solution": "4", "experiment": "3"}


def ost_forest(notes, scope_root: str) -> list:
    nodes = {n.name.lower(): n for n in notes if n.type in OST_TYPES and n.rel.startswith(scope_root + "/")}
    children = {}
    for n in nodes.values():
        parent = link_target(n.get("parent")).lower() if n.get("parent") else ""
        if parent in nodes:
            children.setdefault(parent, []).append(n)
    for k in children:
        children[k].sort(key=lambda n: (OST_TYPES.index(n.type), n.name))
    roots = [n for n in nodes.values() if n.type == "outcome"]
    orphans = [n for n in nodes.values() if n.type != "outcome"
               and not (n.get("parent") and link_target(n.get("parent")).lower() in nodes)]

    def build(n):
        return {"note": n, "children": [build(c) for c in children.get(n.name.lower(), [])]}
    return [build(r) for r in sorted(roots, key=lambda n: n.name)], orphans


def ost_mermaid(tree: dict) -> str:
    out, counter = ["```mermaid", "flowchart TD"], [0]

    def walk(t, parent_id=None):
        nid = f"n{counter[0]}"
        counter[0] += 1
        n = t["note"]
        extra = ""
        if n.type == "solution" and n.get("impact") is not None:
            extra = f" (I{n.get('impact')}/E{n.get('effort')})"
        if n.type == "experiment" and n.get("result"):
            extra = f" ({n.get('result')})"
        out.append(f'  {nid}["{mermaid_label(n.name + extra)}"]:::{n.type}')
        if parent_id:
            out.append(f"  {parent_id} --> {nid}")
        for c in t["children"]:
            walk(c, nid)
    walk(tree)
    out += ["  classDef outcome fill:#ede9fe,stroke:#6d28d9", "  classDef opportunity fill:#cffafe,stroke:#0e7490",
            "  classDef solution fill:#dcfce7,stroke:#15803d", "  classDef experiment fill:#fef9c3,stroke:#a16207", "```"]
    return "\n".join(out)


def ost_canvas(tree: dict) -> dict:
    W, H, GX, GY = 400, 260, 60, 160
    nodes, edges, leaf_x = [], [], [0]

    def layout(t, depth):
        kids = [layout(c, depth + 1) for c in t["children"]]
        if kids:
            x = (kids[0]["x"] + kids[-1]["x"]) / 2
        else:
            x = leaf_x[0]
            leaf_x[0] += W + GX
        node = {"id": f"n{len(nodes)}", "x": int(x), "y": depth * (H + GY), "t": t}
        nodes.append(node)
        for k in kids:
            edges.append({"id": f"e{len(edges)}", "fromNode": node["id"], "fromSide": "bottom",
                          "toNode": k["id"], "toSide": "top"})
        return node
    layout(tree, 0)
    return {
        "nodes": [{"id": n["id"], "type": "file", "file": n["t"]["note"].rel, "x": n["x"], "y": n["y"],
                   "width": W, "height": H, "color": CANVAS_COLOR.get(n["t"]["note"].type, "0")} for n in nodes],
        "edges": edges,
    }


def scope_roots(root: Path) -> list:
    """[(scope label, folder rel path, layer, team)] for company and every team."""
    out = [("Company", "Company", "company", None)]
    if (root / "Teams").is_dir():
        for t in sorted(p.name for p in (root / "Teams").iterdir() if p.is_dir()):
            out.append((t, f"Teams/{t}", "team", t))
    return out


def hub_path(root: Path, folder: str, area: str, team: str | None) -> Path:
    """Company/Discovery/Company Discovery.md or Teams/<T>/Discovery/<T> Discovery.md"""
    return root / folder / area / f"{team or 'Company'} {area}.md"


# ---------------------------------------------------------------------------
# Effort-impact matrix
# ---------------------------------------------------------------------------

QUADRANTS = {
    "Quick wins": "high impact, low effort: do these first",
    "Big bets": "high impact, high effort: plan deliberately, slice into experiments",
    "Fill-ins": "low impact, low effort: do when there is slack",
    "Money pits": "low impact, high effort: avoid or rethink",
}


def quadrant(impact: float, effort: float) -> str:
    hi = impact >= 3
    lo_e = effort < 3
    return ("Quick wins" if lo_e else "Big bets") if hi else ("Fill-ins" if lo_e else "Money pits")


def matrix_items(notes, scope_root: str) -> list:
    items = []
    for n in notes:
        if n.type not in ("solution", "project") or not n.rel.startswith(scope_root + "/"):
            continue
        if str(n.get("status") or "").lower() in DONE_STATUSES:
            continue
        i, e = _num(n.get("impact")), _num(n.get("effort"))
        if i is None or e is None:
            continue
        rice = None
        r, c = _num(n.get("reach")), {"high": 1.0, "medium": 0.8, "low": 0.5}.get(str(n.get("confidence") or "").lower())
        if r is not None and c is not None and e:
            rice = round(r * i * c / e, 1)
        items.append({"note": n, "impact": i, "effort": e, "quadrant": quadrant(i, e), "rice": rice})
    items.sort(key=lambda x: (-x["impact"], x["effort"], x["note"].name))
    return items


def render_matrix(items: list) -> str:
    if not items:
        return ("No scored items yet. Add `impact:` and `effort:` (1-5) to solution or project notes, "
                "then run `brain refresh`.")
    lines = ["```mermaid", "quadrantChart", "  title Effort vs impact", "  x-axis Low effort --> High effort",
             "  y-axis Low impact --> High impact", "  quadrant-1 Big bets", "  quadrant-2 Quick wins",
             "  quadrant-3 Fill-ins", "  quadrant-4 Money pits"]
    seen = {}
    for it in items:
        key = (it["impact"], it["effort"])
        k = seen.get(key, 0)
        seen[key] = k + 1
        x = min(0.97, max(0.03, (it["effort"] - 1) / 4 + 0.025 * k))
        y = min(0.97, max(0.03, (it["impact"] - 1) / 4 - 0.025 * k))
        label = re.sub(r"[^A-Za-z0-9 _.-]", "", re.sub(r"^(SOL|OPP) - ", "", it["note"].name))[:40].strip() or "item"
        lines.append(f"  {label}: [{x:.2f}, {y:.2f}]")
    lines.append("```")
    for q, desc in QUADRANTS.items():
        qi = [it for it in items if it["quadrant"] == q]
        lines += ["", f"### {q} ({len(qi)})", f"_{desc}_", ""]
        lines += [f"- [[{it['note'].name}]] impact {it['impact']:g}, effort {it['effort']:g}, "
                  f"{it['note'].type}, status {it['note'].get('status') or 'TBD'}" for it in qi] or ["- none"]
    rice = sorted([it for it in items if it["rice"] is not None], key=lambda x: -x["rice"])
    if rice:
        lines += ["", "### RICE ranking", "", "| Item | Reach | Impact | Confidence | Effort | RICE |",
                  "|---|---|---|---|---|---|"]
        lines += [f"| [[{it['note'].name}]] | {it['note'].get('reach')} | {it['impact']:g} | "
                  f"{it['note'].get('confidence')} | {it['effort']:g} | {it['rice']} |" for it in rice]
    lines += ["", f"Scale: impact and effort 1-5; 3 counts as high impact and high effort. Generated {TODAY.isoformat()}."]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Org chart
# ---------------------------------------------------------------------------

def render_org_chart(notes) -> str:
    people = sorted([n for n in notes if n.type == "person" and n.rel.startswith("Company/Org/People/")],
                    key=lambda n: n.name)
    if not people:
        return "No people yet. Add profiles with `/company-brain:org` or `brain person add`."
    ids = {p.name.lower(): f"p{i}" for i, p in enumerate(people)}
    lines = ["```mermaid", "flowchart TD"]
    for p in people:
        role = str(p.get("role") or "").replace('"', "")
        lines.append(f'  {ids[p.name.lower()]}["{mermaid_label(p.name)}<br/>{mermaid_label(role)}"]')
    for p in people:
        m = _real_link(p.get("manager")).lower()
        if m in ids:
            lines.append(f"  {ids[m]} --> {ids[p.name.lower()]}")
    lines.append("```")
    by_team = {}
    for p in people:
        by_team.setdefault(_real_link(p.get("team")) or "No team", []).append(p)
    lines += ["", "### By team", ""]
    for team in sorted(by_team):
        team_link = team if team == "No team" else f"[[{team}]]"
        lines.append(f"- {team_link}: " + ", ".join(
            f"[[{p.name}]] ({p.get('role') or 'role TBD'})" for p in by_team[team]))
    missing = sorted({_real_link(p.get("manager")) for p in people
                      if _real_link(p.get("manager")) and _real_link(p.get("manager")).lower() not in ids})
    if missing:
        lines += ["", "Managers without a profile (create them to complete the chart): " +
                  ", ".join(f"[[{m}]]" for m in missing)]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Index
# ---------------------------------------------------------------------------

def render_index(root: Path, notes) -> str:
    cfg = load_config(root)
    groups = {}
    for n in notes:
        if n.name in ("index", "log", "Home", "CLAUDE", "README") and "/" not in n.rel:
            continue
        layer = n.folder_layer or "root"
        sect = {"company": "Company", "team": f"Team: {n.team}" if n.team else "Teams",
                "personal": "Personal (local only, never committed)", "system": "System"}.get(layer, "Root")
        groups.setdefault(sect, {}).setdefault(n.type or "untyped", []).append(n)
    order = ["Company"] + sorted(k for k in groups if k.startswith("Team")) + \
            ["Personal (local only, never committed)", "System", "Root"]
    out = ["# Index", "",
           f"Catalog of every note in {(cfg.get('company') or {}).get('name', 'the company')} brain, generated "
           f"{TODAY.isoformat()} by `brain index`. Read this first to navigate; each line is the note's "
           "first preamble sentence. Local file (gitignored): it lists personal notes.", ""]
    for sect in order:
        if sect not in groups:
            continue
        out += [f"## {sect}", ""]
        for t in sorted(groups[sect]):
            out.append(f"### {t}")
            for n in sorted(groups[sect][t], key=lambda n: n.name):
                s = n.summary()
                out.append(f"- [[{n.name}]]" + (f" - {s}" if s else ""))
            out.append("")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check(root: Path, notes=None) -> list:
    notes = notes if notes is not None else scan(root)
    idx = name_index(notes)
    issues = []
    who = whoami(root)
    period = who["period"]

    def add(sev, n, msg):
        issues.append({"severity": sev, "path": n.rel if n else "", "message": msg})

    inbound = {}
    for n in notes:
        is_board = "kanban-plugin" in n.fm
        exempt = n.rel in EXEMPT_FILES or is_board
        shared = n.folder_layer in ("company", "team")
        if not exempt:
            missing = [k for k in ("date", "type", "tags") if not n.fm.get(k)]
            if n.fm.get("ai-first") is not True:
                missing.append("ai-first: true")
            if missing:
                add("warn", n, "missing AI-first frontmatter: " + ", ".join(missing))
            if not re.search(r"^## For future agent\s*$|^> \[!\w+\][-+]? For future agent", n.body, re.M):
                add("warn", n, "missing `## For future agent` preamble")
            declared = str(n.fm.get("layer") or "")
            if n.folder_layer in ("company", "team", "personal") and declared and declared != n.folder_layer:
                add("error", n, f"layer: {declared} does not match its folder ({n.folder_layer})")
        if shared and re.search(r"^## Private\s*$", n.body, re.M):
            add("error", n, "shared note contains a `## Private` section (move it to Personal/)")
        for target, anchor, embed in n.links():
            if re.search(r"\.(?!md$)[A-Za-z0-9]{2,6}$", target):
                continue  # canvas, image, pdf: not a note
            hits = idx.get(target.split("/")[-1].lower(), [])
            if not hits:
                if not target.startswith(("http", "TBD")) and target != "TBD":
                    add("info", n, f"unresolved link [[{target}]] (create a stub or fix the name)")
                continue
            for h in hits:
                if h is not n:
                    inbound[h.rel] = inbound.get(h.rel, 0) + 1
            if shared and all(h.folder_layer == "personal" for h in hits):
                add("error", n, f"leak: shared note links to personal note [[{target}]]")
    for n in notes:
        if n.rel not in inbound and n.rel not in EXEMPT_FILES and n.folder_layer in ("company", "team") \
                and n.type not in ("hub", "okr-tree", "prioritization", "org-chart") and "kanban-plugin" not in n.fm:
            add("info", n, "orphan: no other note links here")
    objs = okr_model(notes)
    for o in objs.values():
        n = o["note"]
        if o["status"] in ("done", "dropped"):
            continue
        current = o["period"] in (period["quarter"], period["year"])
        if o["level"] in ("team", "personal") and not o["parent"]:
            add("warn", n, "objective is not aligned (no `parent:` objective or KR)")
        if o["parent"] and o["parent"].lower() not in objs:
            add("warn", n, f"parent [[{o['parent']}]] is not an objective note")
        if not o["krs"]:
            add("warn", n, "objective has no key results with block ids (^kr1) under `## Key results`")
        for kr in o["krs"]:
            if not kr["fields"].get("owner"):
                add("info", n, f"{kr['id']} has no owner")
        if current:
            try:
                last = dt.date.fromisoformat(o["last_checkin"][:10])
                if (TODAY - last).days > 14:
                    add("warn", n, f"no check-in for {(TODAY - last).days} days")
            except ValueError:
                add("warn", n, "no `last_checkin:` date on a current objective")
    for f in freshness_report(root)["findings"]:
        issues.append({"severity": "warn" if f["severity"] == "error" else "info", "path": f["file"],
                       "message": f"{f['rule']} line {f['line']}: {f['text']}"})
    return issues


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

def gdrive_roots() -> list:
    base = Path.home() / "Library" / "CloudStorage"
    return sorted(p for p in base.glob("GoogleDrive-*") if p.is_dir()) if base.is_dir() else []


def portable_source(path: Path) -> dict:
    p = path.expanduser().resolve()
    for g in gdrive_roots():
        try:
            return {"gdrive": p.relative_to(g.resolve()).as_posix()}
        except ValueError:
            pass
    try:
        return {"desktop": p.relative_to((Path.home() / "Desktop").resolve()).as_posix()}
    except ValueError:
        pass
    try:
        return {"home": p.relative_to(Path.home().resolve()).as_posix()}
    except ValueError:
        return {"path": p.as_posix()}


def resolve_portable(entry: dict):
    if entry.get("gdrive"):
        for g in gdrive_roots():
            cand = g / entry["gdrive"]
            if cand.exists():
                return cand
        return None
    if entry.get("desktop"):
        return Path.home() / "Desktop" / entry["desktop"]
    if entry.get("home"):
        return Path.home() / entry["home"]
    return Path(entry["path"]) if entry.get("path") else None


def write_sources_registry(root: Path) -> None:
    src = root / "Sources"
    src.mkdir(exist_ok=True)
    rows = []
    for p in sorted(src.iterdir()):
        if p.is_symlink():
            target = os.readlink(p)
            rows.append(f"| {p.name} | `{target}` | {'yes' if p.exists() else 'BROKEN'} |")
    (src / "Sources.md").write_text(
        f"---\ndate: {TODAY.isoformat()}\ntype: hub\ntags: [hub, sources]\nai-first: true\nlayer: personal\n---\n\n"
        "# Sources\n\n## For future agent\nLocal registry of external folders mounted into this brain as read-only "
        "sources (symlinks), regenerated by `brain connect`. Read files through `Sources/<Name>/...`; never write "
        "there. Rules: `.company-brain/references/sources.md`.\n\n| Name | Points to | Reachable |\n|---|---|---|\n"
        + ("\n".join(rows) if rows else "| none yet | run `brain connect <path> --name <Name>` | |") + "\n",
        encoding="utf-8")


def add_shared_source(root: Path, name: str, entry: dict) -> None:
    cfg_path = root / "brain.yaml"
    text = cfg_path.read_text(encoding="utf-8")
    cfg = load_config(root)
    sources = [s for s in as_list(cfg.get("sources")) if isinstance(s, dict) and s.get("name") != name]
    sources.append(dict({"name": name}, **entry))
    block = "sources:" + ("".join(
        "\n  - " + "\n    ".join(f"{k}: {yaml_value(v)}" for k, v in s.items()) for s in sources) if sources else " []")
    if re.search(r"^sources:.*?(?=^\S|\Z)", text, re.S | re.M):
        text = re.sub(r"^sources:.*?(?=^\S|\Z)", block + "\n", text, count=1, flags=re.S | re.M)
    else:
        text = text.rstrip() + "\n" + block + "\n"
    cfg_path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# Context (session hook, MCP brain_context) and export pack
# ---------------------------------------------------------------------------

def _note_text(root: Path, rel: str, limit: int = 4000) -> str:
    p = root / rel
    if not p.is_file():
        return ""
    _, body = split_frontmatter(p.read_text(encoding="utf-8"))
    body = re.sub(r"<!-- brain:auto:(start|end) [\w-]+ -->\n?", "", body)
    return body.strip()[:limit]


def context_pack(root: Path, level: int = 1) -> dict:
    who = whoami(root)
    out = {"whoami": who}
    if level >= 1:
        for k in ("Mission", "Vision", "Values"):
            out[k.lower()] = _note_text(root, f"Company/{k}.md", 2500)
        notes = scan(root)
        out["okr_tree"] = render_okr_tree(okr_model(notes), who["period"]["quarter"])
    if level >= 2:
        notes = scan(root)
        out["strategy"] = {n.name: n.body.strip()[:3000] for n in notes
                           if n.type in ("strategy", "vpc", "bmc") and n.folder_layer == "company"}
        out["teams"] = {n.name: n.summary() for n in notes if n.type == "team"}
        out["roadmap"] = _note_text(root, "Company/Roadmap/Company Roadmap.md", 4000)
    return out


EXPORT_GROUPS = [
    ("01 Company overview", lambda n: n.folder_layer == "company" and n.type in ("mission", "vision", "values", "hub") and n.rel.count("/") == 1),
    ("02 Strategy", lambda n: n.folder_layer in ("company", "team") and n.type in ("strategy", "vpc", "bmc", "plan")),
    ("03 OKRs", lambda n: n.folder_layer in ("company", "team") and n.type in ("objective", "okr-tree")),
    ("04 Org and teams", lambda n: n.folder_layer in ("company", "team") and n.type in ("person", "team", "org-chart")),
    ("05 Discovery and roadmap", lambda n: n.folder_layer in ("company", "team") and n.type in OST_TYPES + ("prioritization",)),
    ("06 Projects", lambda n: n.folder_layer in ("company", "team") and n.type == "project" and str(n.get("status") or "") not in ("archived",)),
    ("07 Decisions", lambda n: n.folder_layer in ("company", "team") and n.type == "decision"),
    ("08 Team weekly roll-ups", lambda n: n.folder_layer == "team" and n.type == "team-weekly"),
]


def export_pack(root: Path, out_dir: Path) -> list:
    notes = [n for n in scan(root) if n.folder_layer in ("company", "team")]
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("*.md"):
        old.unlink()
    written = []
    company = whoami(root)["company"]
    for title, pred in EXPORT_GROUPS:
        sel = sorted([n for n in notes if pred(n)], key=lambda n: n.rel)
        if title.startswith("08"):
            sel = sel[-8:]
        if not sel:
            continue
        parts = [f"# {company} - {title.split(' ', 1)[1]}", "",
                 f"Exported {TODAY.isoformat()} from the Company Brain (company and team layers only). "
                 "Read-only snapshot: edit the vault, then re-export.", ""]
        for n in sel:
            body = re.sub(r"<!-- brain:auto:(start|end) [\w-]+ -->\n?", "", n.body).strip()
            body = re.sub(r"```dataview.*?```", "(live Dataview query omitted)", body, flags=re.S)
            meta = ", ".join(f"{k}: {v}" for k, v in n.fm.items()
                             if k in ("layer", "team", "owner", "status", "period", "level", "role", "manager", "segment", "impact", "effort", "roadmap") and v)
            parts += [f"## {n.name}", f"`{n.rel}` | {meta}", "", body, "", "---", ""]
        path = out_dir / f"{title}.md"
        path.write_text("\n".join(parts), encoding="utf-8")
        written.append(path)
    instr = out_dir / "PROJECT_INSTRUCTIONS.md"
    instr.write_text(PROJECT_INSTRUCTIONS.replace("{{COMPANY}}", company).replace("{{DATE}}", TODAY.isoformat()),
                     encoding="utf-8")
    written.append(instr)
    return written


PROJECT_INSTRUCTIONS = """# Claude Project instructions ({{COMPANY}} Company Brain)

Paste the text below into the Project's custom instructions, and upload the other files in this folder as Project knowledge. Exported {{DATE}}.

---

You are the {{COMPANY}} Company Brain assistant. The Project knowledge is a read-only snapshot of the company and team layers of the Company Brain vault: mission, vision, values, strategy (Value Proposition Canvases, strategy kernel), OKRs and their cascade, org and teams, discovery (opportunity solution trees), prioritization, roadmap, projects, decisions, and recent team weekly roll-ups.

How to answer:
- Ground every answer in the Project knowledge and name the note it came from (the `## <note name>` headings).
- When asked how work connects to strategy, trace it: project or solution, to opportunity, to outcome, to key result, to objective, to annual objective, to mission.
- Use the frameworks as the vault does: Value Proposition Canvas for customer fit, opportunity solution trees for discovery, effort-impact (and RICE) for prioritization, Now-Next-Later for the roadmap, OKR scores from 0.0 to 1.0 where 0.7 is a good result.
- The snapshot has a date. If a question depends on something that changes weekly (KR progress, project status), say the export date and suggest checking the live vault.
- You cannot edit the brain from here. To change it, the user runs the Company Brain skills in Claude Code or Cowork on the vault.
- Personal notes are never in this snapshot. Do not speculate about individuals beyond their shared profile.
"""


def session_summary(root: Path) -> str:
    who = whoami(root)
    p = who["period"]
    me = who.get("me")
    lines = [
        f"**Company Brain** for {who['company']} at `{root}` (engine `{ENGINE}`).",
        f"Run the CLI as: `python3 \"{ENGINE}/scripts/brain.py\" --root \"{root}\" <command>` "
        "(period, new, promote, refresh, index, check, connect, export-pack; see --help).",
        f"Today {p['date']}, {p['quarter']}, week {p['week']}. Sharing model: {who['sharing']}.",
    ]
    if me:
        lines.append(f"Me: [[{me}]] ({who.get('role') or 'role TBD'}), teams: "
                     + (", ".join(f"[[{t}]]" for t in who["my_teams"]) or "none") + ".")
    else:
        lines.append("No Personal/Me.md yet: run /company-brain:setup before writing personal or team notes.")
    lines += [
        "Before writing to the brain, follow the brain's CLAUDE.md (layers, routing, AI-first rules). "
        "Layers: Company/ and Teams/ are shared; Personal/ is local-only. Never link from a shared note to a "
        "Personal note, and never copy `## Private` content out of Personal/.",
        "Do not use the obsidian-second-brain MCP tools for this brain: they point at a different vault.",
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def need_root(args) -> Path:
    root = find_root(args.root)
    if not root:
        raise SystemExit("error: no Company Brain found (no brain.yaml above the current directory; "
                         "pass --root or set COMPANY_BRAIN_PATH)")
    return root


def emit(args, data, text=None):
    if getattr(args, "json", False) or text is None:
        print(json.dumps(data, indent=2, default=str))
    else:
        print(text)


def cmd_root(args):
    print(need_root(args))


def cmd_whoami(args):
    emit(args, whoami(need_root(args)))


def cmd_period(args):
    root = need_root(args)
    day = dt.date.fromisoformat(args.date) if args.date else TODAY
    emit(args, period_info(day, (load_config(root).get("company") or {}).get("fiscal_year_start", 1)))


PLACEHOLDER_COMPANY = "Your Company"


def _rename_placeholder(root: Path, old: str, new: str) -> None:
    """Replace the scaffold's placeholder company name in already-created hubs."""
    for p in iter_md(root):
        if p.relative_to(root).parts[0] not in ("Company", "Teams", "Personal"):
            continue
        text = p.read_text(encoding="utf-8")
        if old in text:
            p.write_text(text.replace(old, new), encoding="utf-8")


def cmd_init(args):
    root = Path(args.root).expanduser().resolve() if args.root else (find_root() or Path.cwd())
    if not (root / "brain.yaml").is_file():
        shutil.copy(SCAFFOLD / "brain.yaml", root / "brain.yaml")
    if args.company:
        old = (load_config(root).get("company") or {}).get("name") or ""
        _set_brain_yaml(root, "company", "name", args.company)
        if old == PLACEHOLDER_COMPANY and args.company != old:
            _rename_placeholder(root, old, args.company)
    if args.timezone:
        _set_brain_yaml(root, "company", "timezone", args.timezone)
    if args.fiscal_year_start:
        _set_brain_yaml(root, "company", "fiscal_year_start", str(args.fiscal_year_start))
    if args.sharing:
        _set_brain_yaml(root, "sharing", "model", args.sharing)
    me_ctx = {}
    if args.me:
        me_ctx = {"ME": args.me, "ME_FIRST": args.me.split(" ")[0], "ROLE": args.role or "TBD",
                  "TIMEZONE": args.timezone or (load_config(root).get("company") or {}).get("timezone") or "TBD",
                  "MANAGER": args.manager or "TBD",
                  "TEAMS_YAML": "[" + ", ".join(f'"[[{t}]]"' for t in (args.team or [])) + "]",
                  "FIRST_TEAM": (args.team or ["TBD"])[0]}
    created = render_scaffold(SCAFFOLD / "system", root, scaffold_ctx(root, me_ctx))
    created += render_scaffold(SCAFFOLD / "company", root, scaffold_ctx(root, me_ctx))
    for t in args.team or []:
        created += render_scaffold(SCAFFOLD / "team", root, scaffold_ctx(root, dict(me_ctx, TEAM=t, TEAM_LEAD=args.lead or "TBD")))
    if args.me:
        created += render_scaffold(SCAFFOLD / "personal", root, scaffold_ctx(root, me_ctx))
        prof = create_note(root, "person", args.me, values={
            "role": args.role or "TBD", "team": f"[[{args.team[0]}]]" if args.team else "TBD",
            "manager": f"[[{args.manager}]]" if args.manager else "TBD"}, name=args.me)
        if prof.get("created"):
            created.append(prof["path"])
    for gitkeep in ("Sources", "Exports"):
        (root / gitkeep).mkdir(exist_ok=True)
    write_sources_registry(root)
    stamped = stamp_placeholders(root)
    emit(args, {"root": str(root), "created": created, "stamped": stamped},
         f"Brain at {root}\nCreated {len(created)} files" + "".join(f"\n  + {c}" for c in created)
         + (f"\nStamped {len(stamped)} placeholder dates" + "".join(f"\n  ~ {s}" for s in stamped) if stamped else ""))


def cmd_scaffold_sync(args):
    root = need_root(args)
    if ENGINE.resolve() != (root / ".company-brain").resolve():
        raise SystemExit(f"error: scaffold-sync updates the engine shipped inside the brain ({root / '.company-brain'}), "
                         f"but this engine is {ENGINE}; run ./brain scaffold-sync from that brain")
    if args.watch:
        res = watch_install(root, args.interval)
        emit(args, res, f"Watching {root}: scaffold syncs on edits to System/, Templates/, CLAUDE.md, Home.md, the slash commands, "
                        f"and vault settings, and every {args.interval}s\n  agent: {res['plist']}\n  log: {res['log']}"
                        + "".join(f"\n  removed stale agent {s}" for s in res["removed_stale"])
                        + "\nStop with ./brain scaffold-sync --unwatch"
                        + (f"\nwarning: macOS privacy settings block background access to this folder, so the agent "
                           f"cannot run. Move the brain out of Desktop, Documents, and Downloads (for example to "
                           f"~/Brains) and run --watch again there, or give {res['python']} Full Disk Access in "
                           f"System Settings > Privacy & Security." if res["blocked"] else ""))
        return
    if args.unwatch:
        res = watch_remove(root)
        emit(args, res, f"Stopped watching {root}" if res["removed"] else f"No watcher was installed for {root}")
        return
    res = scaffold_sync(root, write=not args.check)
    drift = res["added"] + res["changed"] + res["removed"]
    rel = Path(res["scaffold"]).relative_to(root).as_posix()
    if args.quiet and not drift:
        return
    text = sync_report(res, rel, args.check, "is in sync with the vault", "./brain scaffold-sync")
    if args.quiet:
        text = f"{dt.datetime.now():%Y-%m-%d %H:%M:%S} {text}"
    emit(args, res, text)
    if args.check and drift:
        sys.exit(1)


def cmd_commands(args):
    root = need_root(args)
    local = root / ".company-brain"
    if local.is_dir() and ENGINE.resolve() != local.resolve():
        raise SystemExit(f"error: this brain ships its own engine ({local}), but this engine is {ENGINE}; "
                         "run ./brain commands from that brain so the commands match its skills")
    res = commands_sync(root, write=not args.check)
    emit(args, res, sync_report(res, res["commands"], args.check, "is in sync with the skills",
                                "./brain commands, then ./brain scaffold-sync,"))
    if res["blocked"] or (args.check and (res["added"] or res["changed"] or res["removed"])):
        sys.exit(1)


def cmd_upstream_check(args):
    root = need_root(args)
    if ENGINE.resolve() != (root / ".company-brain").resolve():
        raise SystemExit(f"error: upstream-check tracks the engine shipped inside the brain ({root / '.company-brain'}), "
                         f"but this engine is {ENGINE}; run ./brain upstream-check from that brain")
    if args.verify:
        problems = vendored_integrity(root)
        emit(args, {"problems": problems},
             "Vendored files match upstream.json" if not problems else
             "Vendored files were edited:\n  " + "\n  ".join(problems)
             + "\nUndo the edit, or take the upstream version with ./brain upstream-check --copy.")
        if problems:
            sys.exit(1)
        return
    if args.draft:
        if args.diff or args.copy or args.mark:
            raise SystemExit("error: --draft runs on its own; run the check, --diff, --copy and --mark separately")
        conf = json.loads(UPSTREAM_CONF.read_text(encoding="utf-8"))
        res = draft_skill(root, conf, fetch_upstream(root, conf), args.draft, args.draft_as)
        rel = Path(res["path"]).resolve().relative_to(root.resolve()).as_posix()
        emit(args, res, f"Drafted {rel} from upstream {res['upstream']} at {res['commit']}, with {res['todos']} "
                        f"{DRAFT_MARKER} markers to resolve.\nNext: finish it with "
                        ".company-brain/references/upstream-sync.md, then ./brain commands and the checks there.")
        return
    res = upstream_check(root, diff=args.diff, copy=args.copy, mark=args.mark)
    base, head = res["base"][:7], res["head"][:7]
    text = f"Upstream {res['repo']} is at {head}, {res['commits']} commits after the recorded {base}"
    if res["changed"]:
        text += f"\nBorrowed files changed upstream ({len(res['changed'])}):"
        for f in res["changed"]:
            text += f"\n  {f['mode']:<5}  {f['upstream']} -> {f['local']} (+{f['added']} -{f['removed']})"
    else:
        text += "\nNone of the borrowed files changed upstream."
    tri = res.get("commands")
    pending = triage_blockers(tri)
    if tri:
        if tri["missing_dir"]:
            text += f"\nUpstream has no {tri['dir']}/ folder any more, so its commands cannot be compared."
        if tri["new"]:
            text += f"\nUpstream commands not triaged yet ({len(tri['new'])}): " + ", ".join(tri["new"])
        if tri["changed"]:
            text += f"\nUpstream commands changed since triage ({len(tri['changed'])}), check the skill each became:"
            for c in tri["changed"]:
                text += f"\n  {c['decision']:<7}  {c['upstream']} -> skills/{c['skill']} (+{c['added']} -{c['removed']})"
        if tri["removed"]:
            text += f"\nUpstream commands removed ({len(tri['removed'])}): " + ", ".join(tri["removed"])
        if pending or tri["changed"]:
            text += f"\nTo bring them in, follow {tri['playbook']}."
    if res.get("diff"):
        text += "\n\n" + res["diff"].rstrip()
    for p in res.get("copied", []):
        text += f"\nCopied upstream version into {p}"
    if res.get("marked"):
        text += f"\nRecorded {head} as the synced upstream commit in .company-brain/upstream.json; commit it with your changes."
    elif res["changed"] or pending or (tri and tri["changed"]):
        steps = ["--diff to read the changes"]
        if res["changed"]:
            steps += ["--copy to take the 'copy' files as they are", "port 'adapt' changes by hand"]
        if tri and tri["changed"]:
            steps.append("port what fits from the changed commands into their skills")
        if pending:
            steps.append("record a decision for every new or removed command in upstream.json commands.map")
        text += "\nNext: " + ", ".join(steps) + ", then --mark and commit."
    elif res["commits"]:
        text += "\nRun with --mark to record it as synced."
    if res["commits"] and not res.get("marked"):
        text += f"\nOther upstream changes (docs, scripts not borrowed yet): git log --oneline {base}..{res['ref']}"
    emit(args, res, text)


def cmd_team_add(args):
    root = need_root(args)
    created = render_scaffold(SCAFFOLD / "team", root, scaffold_ctx(root, {"TEAM": args.name, "TEAM_LEAD": args.lead or "TBD"}))
    if args.lead:
        prof = create_note(root, "person", args.lead, name=args.lead,
                           values={"role": "TBD", "team": f"[[{args.name}]]", "manager": "TBD"})
        if prof.get("created"):
            created.append(prof["path"])
    emit(args, {"created": created}, f"Team {args.name}: {len(created)} files" + "".join(f"\n  + {c}" for c in created))


def _values_from_sets(sets) -> dict:
    values = {}
    for s in sets or []:
        k, sep, v = s.partition("=")
        if not sep:
            raise SystemExit(f"error: --set expects key=value, got {s!r}")
        values[k.strip()] = _scalar(v) if v.strip().startswith(("[", "true", "false")) or re.fullmatch(r"-?\d+(\.\d+)?", v.strip()) else v.strip()
    return values


def cmd_person_add(args):
    root = need_root(args)
    values = {"role": args.role or "TBD", "team": f"[[{args.team}]]" if args.team else "TBD",
              "manager": f"[[{args.manager}]]" if args.manager else "TBD"}
    res = create_note(root, "person", args.name, values=values, name=args.name)
    emit(args, res, ("created " if res["created"] else "exists ") + res["path"])


def cmd_new(args):
    root = need_root(args)
    res = create_note(root, args.kind, args.title or "", layer=args.layer, team=args.team,
                      values=_values_from_sets(args.set), name=args.name)
    emit(args, res, ("created " if res["created"] else "exists ") + res["path"])
    if not res["created"]:
        sys.exit(3)


def cmd_promote(args):
    root = need_root(args)
    res = promote(root, args.note, args.to, team=args.team, kind=args.kind, name=args.name, write=args.yes)
    if res.get("reason"):
        emit(args, res, f"exists {res['path']} ({res['reason']})")
        sys.exit(3)
    r = res["removed"]
    removed = []
    if r["private_sections"]:
        removed.append(f"{r['private_sections']} `Private` section(s)")
    if r["sections"]:
        removed.append("weekly sections that are not part of the team update: " + ", ".join(r["sections"]))
    if r["personal_links"]:
        removed.append("links to personal notes, kept as plain text: " + ", ".join(sorted(set(r["personal_links"]))))
    if r["fields"]:
        removed.append("personal-only fields: " + ", ".join(r["fields"]))
    lines = [f"{'Published' if res['created'] else 'Would publish'} {res['source']} -> {res['path']} "
             f"({res['kind']}, {res['layer']} layer)",
             "Removed:" + ("" if removed else " nothing")] + [f"  - {x}" for x in removed]
    if res["created"]:
        lines.append(f"Added promoted_to to {res['source']}.")
        lines += [f"  ! {e['message']}" for e in res["errors"]] or ["Layer check: no errors."]
    else:
        lines += ["", res["diff"].rstrip(), "", "Dry run: nothing was written. Re-run with --yes to publish."]
    if res["kind"] != "team-update":
        lines.append("Rewrite the `## For future agent` preamble for the shared audience.")
    emit(args, res, "\n".join(lines))
    if res["errors"]:
        sys.exit(4)


def refresh(root: Path, quiet=False) -> dict:
    stamped = stamp_placeholders(root)
    notes = scan(root)
    who = whoami(root)
    period = who["period"]
    report = {path: "stamped" for path in stamped}
    objs = okr_model(notes)
    for per in (period["quarter"], period["year"]):
        path = root / "Company" / "OKRs" / f"OKR Tree - {per}.md"
        report[path.relative_to(root).as_posix()] = write_auto_block(
            path, "okr-tree", render_okr_tree(objs, per),
            generated_header("okr-tree", f"OKR Tree - {per}", "company",
                             f"This note is the generated OKR cascade for {per}: company and team objectives with KR progress and alignment gaps (personal goals are excluded from shared trees)."))
    if (root / "Personal").is_dir():
        per = period["quarter"]
        path = root / "Personal" / "Goals" / f"My OKR Tree - {per}.md"
        report[path.relative_to(root).as_posix()] = write_auto_block(
            path, "okr-tree", render_okr_tree(objs, per, include_personal=True),
            generated_header("okr-tree", f"My OKR Tree - {per}", "personal",
                             f"This note is the generated OKR cascade for {per} including my personal goals, so I can see how they ladder up to team and company key results. Local only."))
    for label, folder, layer, team in scope_roots(root):
        forest, orphans = ost_forest(notes, folder)
        hub = hub_path(root, folder, "Discovery", team)
        parts = []
        for tree in forest:
            name = tree["note"].name
            canvas = root / folder / "Discovery" / f"OST - {name.replace('OUT - ', '')}.canvas"
            canvas.write_text(json.dumps(ost_canvas(tree), indent=1), encoding="utf-8")
            parts += [f"### [[{name}]]", f"Canvas: [[{canvas.name}]]", "", ost_mermaid(tree), ""]
        if orphans:
            parts += ["### Not connected to an outcome", ""] + [f"- [[{o.name}]] ({o.type})" for o in sorted(orphans, key=lambda o: o.name)]
        if not parts:
            parts = ["No outcomes yet. Start a tree with `/company-brain:ost`."]
        if hub.exists() or forest or orphans:
            report[hub.relative_to(root).as_posix()] = write_auto_block(
                hub, "ost", "\n".join(parts),
                generated_header("hub", hub.stem, layer, f"This note is the discovery hub for {label}: opportunity solution trees from outcome to experiment.", team))
        items = matrix_items(notes, folder)
        mpath = root / folder / "Roadmap" / "Company Prioritization.md" if not team else root / folder / f"{team} Prioritization.md"
        if mpath.exists() or items:
            report[mpath.relative_to(root).as_posix()] = write_auto_block(
                mpath, "matrix", render_matrix(items),
                generated_header("prioritization", mpath.stem, layer, f"This note is the generated effort-impact matrix (with RICE where scored) for {label}'s open solutions and projects.", team))
    org = root / "Company" / "Org" / "Org Chart.md"
    report[org.relative_to(root).as_posix()] = write_auto_block(
        org, "org-chart", render_org_chart(notes),
        generated_header("org-chart", "Org Chart", "company", "This note is the generated org chart built from people profiles (manager and team fields)."))
    (root / "index.md").write_text(render_index(root, scan(root)), encoding="utf-8")
    report["index.md"] = "rebuilt"
    return report


def cmd_refresh(args):
    root = need_root(args)
    rep = refresh(root)
    emit(args, rep, "\n".join(f"{v:9} {k}" for k, v in rep.items()))


def cmd_index(args):
    root = need_root(args)
    (root / "index.md").write_text(render_index(root, scan(root)), encoding="utf-8")
    print("rebuilt index.md")


def cmd_check(args):
    root = need_root(args)
    issues = check(root)
    if args.severity:
        rank = {"info": 0, "warn": 1, "error": 2}
        issues = [i for i in issues if rank[i["severity"]] >= rank[args.severity]]
    if args.json:
        print(json.dumps(issues, indent=2))
    else:
        for sev in ("error", "warn", "info"):
            sel = [i for i in issues if i["severity"] == sev]
            if sel:
                print(f"\n{sev.upper()} ({len(sel)})")
                for i in sel:
                    print(f"  {i['path']}: {i['message']}")
        counts = {s: sum(1 for i in issues if i["severity"] == s) for s in ("error", "warn", "info")}
        print(f"\n{counts['error']} errors, {counts['warn']} warnings, {counts['info']} info")
    sys.exit(1 if any(i["severity"] == "error" for i in issues) else 0)


def cmd_freshness(args):
    root = need_root(args)
    report = freshness_report(root)
    lines = [f"[{f['rule']}] {f['severity']}: {f['file']}:{f['line']}  {f['text']}" for f in report["findings"]]
    lines.append(f"\n{report['errors']} error(s), {report['warnings']} warning(s)")
    if not report["findings"]:
        lines.append("Freshness-clean: every fact is timeless, dated, or a pointer.")
    else:
        lines.append("Fix: add `(as of YYYY-MM-DD)`, turn it into a pointer to where the truth lives, or move it into a dated note.")
    emit(args, report, "\n".join(lines))
    if report["errors"] or (args.strict and report["warnings"]):
        sys.exit(1)


def cmd_search(args):
    """Search the brain from a shell, a cron job or CI, with no agent (port of upstream scripts/vault_search.py)."""
    root = need_root(args)
    os.environ["COMPANY_BRAIN_PATH"] = str(root)
    sys.path.insert(0, str(ENGINE / "mcp" / "vault"))
    import vault_ops  # the same search the brain MCP server serves
    try:
        results = vault_ops.search(args.query, limit=args.limit, semantic=False if args.lexical else None)
    except (RuntimeError, OSError) as exc:
        raise SystemExit(f"error: search failed: {exc}")
    # ASCII escapes, not raw UTF-8: a console in a legacy code page cannot print a CJK or emoji title.
    print(json.dumps(results))


def cmd_connect(args):
    root = need_root(args)
    src = root / "Sources"
    src.mkdir(exist_ok=True)
    done = []
    if args.sync:
        for entry in as_list(load_config(root).get("sources")):
            if not isinstance(entry, dict) or not entry.get("name"):
                continue
            target = resolve_portable(entry)
            link = src / entry["name"]
            if target and target.exists() and not link.exists():
                link.symlink_to(target, target_is_directory=target.is_dir())
                done.append(f"linked {entry['name']} -> {target}")
            elif not target or not target.exists():
                done.append(f"missing {entry['name']} (not found on this machine: {entry})")
    else:
        if not args.path:
            raise SystemExit("error: give a path to connect, or --sync")
        target = Path(args.path).expanduser().resolve()
        if not target.exists():
            raise SystemExit(f"error: {target} does not exist")
        if target == root or root in target.parents:
            raise SystemExit("error: cannot connect a folder inside the brain itself")
        name = args.name or target.name
        link = src / name
        if link.exists() or link.is_symlink():
            raise SystemExit(f"error: Sources/{name} already exists")
        link.symlink_to(target, target_is_directory=target.is_dir())
        done.append(f"linked {name} -> {target}")
        if args.shared:
            add_shared_source(root, name, portable_source(target))
            done.append(f"recorded {name} in brain.yaml sources (teammates run: brain connect --sync)")
    write_sources_registry(root)
    print("\n".join(done) or "nothing to do")


def cmd_sources(args):
    root = need_root(args)
    src = root / "Sources"
    data = {"mounted": [], "shared_in_config": as_list(load_config(root).get("sources")),
            "google_drive_roots": [str(g) for g in gdrive_roots()]}
    if src.is_dir():
        for p in sorted(src.iterdir()):
            if p.is_symlink():
                data["mounted"].append({"name": p.name, "target": os.readlink(p), "reachable": p.exists()})
    emit(args, data)


def cmd_gdoc(args):
    p = Path(args.path).expanduser()
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise SystemExit(f"error: cannot read pointer file {p}: {e}")
    doc_id = d.get("doc_id") or d.get("resource_id", "").split(":")[-1]
    kind = {".gdoc": "document", ".gsheet": "spreadsheets", ".gslides": "presentation"}.get(p.suffix, "file")
    url = d.get("url") or (f"https://docs.google.com/{kind}/d/{doc_id}" if doc_id else "")
    print(json.dumps({"file": str(p), "doc_id": doc_id, "kind": kind, "url": url}, indent=2))


def cmd_export_pack(args):
    root = need_root(args)
    out = Path(args.out).expanduser() if args.out else root / "Exports" / "Claude Project"
    files = export_pack(root, out)
    total = sum(f.stat().st_size for f in files)
    print(f"Wrote {len(files)} files ({total // 1024} KB) to {out}")
    for f in files:
        print(f"  {f.name}")


def cmd_context(args):
    root = need_root(args)
    if args.session:
        print(session_summary(root))
    else:
        emit(args, context_pack(root, args.level))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="brain", description="Company Brain command line")
    ap.add_argument("--root", help="brain root (default: COMPANY_BRAIN_PATH or nearest brain.yaml)")
    ap.add_argument("--json", action="store_true", help="JSON output where supported")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("root", help="print the brain root").set_defaults(fn=cmd_root)
    sub.add_parser("whoami", help="identity, teams, period").set_defaults(fn=cmd_whoami)
    p = sub.add_parser("period", help="current year, quarter, week, and today's file names")
    p.add_argument("--date")
    p.set_defaults(fn=cmd_period)

    p = sub.add_parser("init", help="scaffold the brain, a team, and your Personal/ layer (idempotent)")
    p.add_argument("--company")
    p.add_argument("--me", help="your full name")
    p.add_argument("--role")
    p.add_argument("--team", action="append", help="team name (repeatable); first is your home team")
    p.add_argument("--lead", help="lead of the team(s) created")
    p.add_argument("--manager")
    p.add_argument("--timezone")
    p.add_argument("--fiscal-year-start", type=int)
    p.add_argument("--sharing", choices=["git", "drive", "local"])
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("scaffold-sync", help="copy System/, Templates/, CLAUDE.md, Home.md, slash commands, and vault settings "
                                             "into the scaffold new brains start from")
    g = p.add_mutually_exclusive_group()
    g.add_argument("--check", action="store_true", help="report drift only; exit 1 when out of sync")
    g.add_argument("--watch", action="store_true", help="macOS: sync automatically in the background (launchd agent)")
    g.add_argument("--unwatch", action="store_true", help="remove the background agent for this brain")
    p.add_argument("--interval", type=int, default=300, help="with --watch: also sync every N seconds (default 300)")
    p.add_argument("--quiet", action="store_true", help="print only when something changed")
    p.set_defaults(fn=cmd_scaffold_sync)

    p = sub.add_parser("commands", help="generate the /company-brain:<name> slash commands in .claude/commands/ "
                                        "from the skills")
    p.add_argument("--check", action="store_true", help="report drift only; exit 1 when out of date")
    p.set_defaults(fn=cmd_commands)

    p = sub.add_parser("upstream-check", help="show which files borrowed from obsidian-second-brain changed upstream")
    p.add_argument("--diff", action="store_true", help="print the upstream changes to those files")
    p.add_argument("--copy", action="store_true", help="overwrite the unchanged-copy files with the upstream version")
    p.add_argument("--mark", action="store_true", help="record the current upstream commit as synced")
    p.add_argument("--draft", metavar="COMMAND",
                   help="write a first-draft skill from an upstream command (e.g. obsidian-merge), to finish by hand")
    p.add_argument("--as", dest="draft_as", metavar="SKILL", help="with --draft: the skill's name here")
    p.add_argument("--verify", action="store_true",
                   help="offline: fail if a vendored copy file was edited (checks sha256 in upstream.json)")
    p.set_defaults(fn=cmd_upstream_check)

    p = sub.add_parser("search", help="search the brain without an agent: JSON results (keyword, plus semantic when available)")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=6)
    p.add_argument("--lexical", action="store_true", help="keyword search only")
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("freshness", help="freshness lint: undated claims about fast-changing facts (references/freshness-policy.md)")
    p.add_argument("--strict", action="store_true", help="warnings (aged stamps) also fail the run")
    p.set_defaults(fn=cmd_freshness)

    team = sub.add_parser("team", help="team spaces").add_subparsers(dest="sub", required=True)
    p = team.add_parser("add")
    p.add_argument("name")
    p.add_argument("--lead")
    p.set_defaults(fn=cmd_team_add)

    person = sub.add_parser("person", help="shared people profiles").add_subparsers(dest="sub", required=True)
    p = person.add_parser("add")
    p.add_argument("name")
    p.add_argument("--role")
    p.add_argument("--team")
    p.add_argument("--manager")
    p.set_defaults(fn=cmd_person_add)

    p = sub.add_parser("new", help="create a note from a template in the right folder with the right name")
    p.add_argument("kind", choices=sorted(KINDS))
    p.add_argument("--title", default="")
    p.add_argument("--layer", choices=["company", "team", "personal"])
    p.add_argument("--team")
    p.add_argument("--name", help="exact filename stem (overrides the naming pattern)")
    p.add_argument("--set", action="append", help="frontmatter or template value key=value (repeatable)")
    p.set_defaults(fn=cmd_new)

    p = sub.add_parser("promote", help="publish a personal note to a team or the company (dry run unless --yes)")
    p.add_argument("note", help="path from the brain root, or the note name")
    p.add_argument("--to", choices=["team", "company"], required=True)
    p.add_argument("--team")
    p.add_argument("--kind", choices=sorted(KINDS), help="target kind when the note's type has no shared folder")
    p.add_argument("--name", help="filename stem for the shared note (default: the source name)")
    p.add_argument("--yes", action="store_true", help="write it; only after the user approved the dry run")
    p.set_defaults(fn=cmd_promote)

    sub.add_parser("refresh", help="rebuild OKR tree, OST views and canvases, matrix, org chart, index").set_defaults(fn=cmd_refresh)
    sub.add_parser("index", help="rebuild index.md").set_defaults(fn=cmd_index)
    p = sub.add_parser("check", help="layer leaks, AI-first compliance, OKR hygiene, links")
    p.add_argument("--severity", choices=["info", "warn", "error"])
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("connect", help="mount a Desktop or Google Drive folder under Sources/")
    p.add_argument("path", nargs="?")
    p.add_argument("--name")
    p.add_argument("--shared", action="store_true", help="record in brain.yaml so teammates can --sync")
    p.add_argument("--sync", action="store_true", help="recreate shared mounts from brain.yaml")
    p.set_defaults(fn=cmd_connect)
    sub.add_parser("sources", help="list mounted and shared sources, detect Google Drive").set_defaults(fn=cmd_sources)
    p = sub.add_parser("gdoc", help="resolve a .gdoc/.gsheet/.gslides pointer to its id and URL")
    p.add_argument("path")
    p.set_defaults(fn=cmd_gdoc)
    p = sub.add_parser("export-pack", help="write the read-only Claude Project pack (company + team layers)")
    p.add_argument("--out")
    p.set_defaults(fn=cmd_export_pack)
    p = sub.add_parser("context", help="company context (JSON) or the session summary")
    p.add_argument("--level", type=int, default=1)
    p.add_argument("--session", action="store_true")
    p.set_defaults(fn=cmd_context)

    args = ap.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
