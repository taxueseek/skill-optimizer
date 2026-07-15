#!/usr/bin/env python3
"""Structural + privacy + description audit for any skill folder.

Ported from session-digger skill-health patterns, generalized for skill-optimizer prove layer.

Usage:
  python3 skill_audit.py <skill-folder>
  python3 skill_audit.py <skill-folder> --json
  python3 skill_audit.py <skill-folder> --strict   # exit 1 if any error

Does not auto-edit. Prints machine-readable report.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from failure_patterns import FAILURE_PATTERNS

TRIGGER_HINTS = (
    "use when", "triggers", "use for", "fires on", "when the user",
    "适用于", "触发", "当用户", "when:",
)
PLACEHOLDER_RE = re.compile(
    r"\bTODO\b|\bTBD\b|\bFIXME\b|待定|占位|\[Outcome\]|\[TODO\]", re.I
)
# Description trap: how-steps in description field
TRAP_RE = re.compile(
    r"(write the test first|first .{0,40} then|step ?\d|"
    r"always use|never use|1\. .{5,40} 2\.)",
    re.I,
)
# Personal path markers (skill-health style)
PERSONAL_PATH_RE = re.compile(r"/Users/[A-Za-z0-9._-]+/")
PERSONAL_HOME_RE = re.compile(r"/home/[A-Za-z0-9._-]+/")
ALLOW_PATH_MARKERS = ("/Users/<", "/Users/test/", "/Users/joker/", "/Users/alice/", "/home/<", "/home/test/")


def parse_frontmatter(text: str) -> tuple[dict, str | None]:
    if not text.lstrip().startswith("---"):
        return {}, "no opening --- frontmatter"
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, "frontmatter not closed"
    raw = parts[1]
    fields: dict[str, str] = {}
    key = None
    buf: list[str] = []
    for line in raw.splitlines():
        if not line.strip() and key is None:
            continue
        m = re.match(r"^([A-Za-z][\w-]*)\s*:\s*(.*)$", line)
        if m and not line.startswith((" ", "\t", "-")):
            if key:
                fields[key] = " ".join(buf).strip().strip("\"'")
            key = m.group(1)
            rest = m.group(2).strip()
            if rest in (">", "|", ""):
                buf = []
            else:
                buf = [rest]
        elif key is not None:
            buf.append(line.strip())
    if key:
        fields[key] = " ".join(buf).strip().strip("\"'")
    return fields, None


def scan_hardcodes(skill_dir: Path) -> list[dict]:
    hits = []
    watch = ["SKILL.md", "README.md", "CLAUDE.md", "scripts", "references", "agents", "assets"]
    files: list[Path] = []
    for rel in watch:
        p = skill_dir / rel
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            files.extend(x for x in p.rglob("*") if x.is_file())
    for p in files:
        if p.suffix not in {".md", ".py", ".sh", ".toml", ".json", ".yaml", ".yml", ".txt", ""}:
            if p.name not in {"SKILL.md", "README.md"}:
                continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            bad = False
            if PERSONAL_PATH_RE.search(line):
                bad = not any(a in line for a in ALLOW_PATH_MARKERS)
            elif PERSONAL_HOME_RE.search(line):
                bad = not any(a in line for a in ALLOW_PATH_MARKERS)
            if not bad:
                continue
            safe = PERSONAL_PATH_RE.sub("/Users/<user>/", line.strip())
            safe = PERSONAL_HOME_RE.sub("/home/<user>/", safe)[:160]
            hits.append({
                "file": str(p.relative_to(skill_dir)),
                "line": i,
                "snippet": safe,
                "pattern": "F-HARDCODE",
            })
    return hits


def audit_skill(skill_dir: Path) -> dict:
    skill_dir = skill_dir.resolve()
    errors: list[dict] = []
    warnings: list[dict] = []
    info: dict = {"skill_dir": str(skill_dir), "name": skill_dir.name}

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append({"id": "missing_skill_md", "msg": "SKILL.md missing", "pattern": "A"})
        return _report(info, errors, warnings, hardcodes=[])

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fields, fm_err = parse_frontmatter(text)
    if fm_err:
        errors.append({"id": "frontmatter", "msg": fm_err, "pattern": "A"})
    name = fields.get("name", "").strip()
    desc = fields.get("description", "").strip()
    info["frontmatter_name"] = name
    info["description_len"] = len(desc)
    info["body_lines"] = text.count("\n") + 1

    if not name:
        errors.append({"id": "name_missing", "msg": "frontmatter name missing", "pattern": "A"})
    elif name != skill_dir.name:
        errors.append({
            "id": "name_mismatch",
            "msg": f"name '{name}' != directory '{skill_dir.name}'",
            "pattern": "A",
        })
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        warnings.append({
            "id": "name_format",
            "msg": "name should be kebab-case, ≤64 chars",
            "pattern": "A",
        })

    if not desc:
        errors.append({"id": "desc_missing", "msg": "description missing", "pattern": "D"})
    else:
        if len(desc) < 40:
            warnings.append({"id": "desc_short", "msg": "description < 40 chars", "pattern": "D"})
        lower = desc.lower()
        if not any(h in lower for h in TRIGGER_HINTS):
            warnings.append({
                "id": "desc_no_trigger",
                "msg": "description lacks clear trigger phrasing (use when / 触发 / …)",
                "pattern": "D",
            })
        if TRAP_RE.search(desc):
            errors.append({
                "id": "description_trap",
                "msg": "Description Trap: description looks like workflow steps",
                "pattern": "F-DESC-TRAP",
            })
        # Over-broad single-token triggers
        if re.search(r"\buse when\b.{0,20}\b(test|help|fix|run)\b\s*$", lower):
            warnings.append({
                "id": "description_substring_trap",
                "msg": "possible over-broad trigger word (F-SUBSTR)",
                "pattern": "F-SUBSTR",
            })

    # Placeholders in body (outside code fences lightly)
    body = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    for m in PLACEHOLDER_RE.finditer(body):
        warnings.append({
            "id": "placeholder",
            "msg": f"placeholder leftover: {m.group(0)}",
            "pattern": "A",
        })
        break  # one is enough signal

    # Referenced paths
    for m in re.finditer(r"`((?:scripts|references|assets|agents)/[^`\s]+)`", text):
        rel = m.group(1)
        if not (skill_dir / rel).exists():
            warnings.append({
                "id": "missing_ref",
                "msg": f"referenced path missing: {rel}",
                "pattern": "A",
            })

    if info["body_lines"] > 650:
        warnings.append({
            "id": "body_too_long",
            "msg": f"SKILL.md ~{info['body_lines']} lines; consider references/",
            "pattern": "C",
        })

    hardcodes = scan_hardcodes(skill_dir)
    for h in hardcodes:
        errors.append({
            "id": "hardcode_paths",
            "msg": f"{h['file']}:{h['line']} personal path",
            "pattern": "F-HARDCODE",
            "detail": h["snippet"],
        })

    # Optional: scripts/ present but no tests or fixtures note
    if (skill_dir / "scripts").is_dir() and not any(
        (skill_dir / d).exists() for d in ("tests", "evals", "fixtures", "test-prompts.json")
    ):
        warnings.append({
            "id": "no_live_assets",
            "msg": "has scripts/ but no tests|evals|fixtures — prove layer recommended",
            "pattern": "F-NO-LIVE",
        })

    return _report(info, errors, warnings, hardcodes)


def _report(info, errors, warnings, hardcodes) -> dict:
    patterns_hit = sorted({
        e.get("pattern") for e in errors + warnings if e.get("pattern")
    })
    return {
        "ok": len(errors) == 0,
        "info": info,
        "errors": errors,
        "warnings": warnings,
        "hardcode_hits": len(hardcodes),
        "patterns_hit": patterns_hit,
        "pattern_catalog_size": len(FAILURE_PATTERNS),
        "note": "Audit only — no auto-edit. Fix then re-run prove_skill.py",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit a skill folder (prove layer)")
    ap.add_argument("skill_folder")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any error")
    args = ap.parse_args()
    skill = Path(args.skill_folder)
    if not skill.is_dir():
        print(f"ERROR: not a directory: {skill}", file=sys.stderr)
        return 2
    report = audit_skill(skill)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        info = report["info"]
        print(f"skill: {info.get('name')}  body_lines={info.get('body_lines')}")
        print(f"ok: {report['ok']}  errors={len(report['errors'])}  warnings={len(report['warnings'])}  hardcodes={report['hardcode_hits']}")
        for e in report["errors"]:
            print(f"  ERROR [{e.get('pattern')}] {e['msg']}")
        for w in report["warnings"]:
            print(f"  WARN  [{w.get('pattern')}] {w['msg']}")
        if report["patterns_hit"]:
            print("patterns:", ", ".join(report["patterns_hit"]))
    if args.strict and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    # Allow running from any cwd
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
