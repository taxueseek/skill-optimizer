#!/usr/bin/env python3
"""Quality audit for any skill folder.

Checks are phrased as durable design principles (see quality_principles.py),
not as a changelog of past incidents.

Usage:
  python3 skill_audit.py <skill-folder>
  python3 skill_audit.py <skill-folder> --json
  python3 skill_audit.py <skill-folder> --strict
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from quality_principles import PRINCIPLES

TRIGGER_HINTS = (
    "use when", "triggers", "use for", "fires on", "when the user",
    "适用于", "触发", "当用户", "when:",
)
PLACEHOLDER_RE = re.compile(
    r"\bTODO\b|\bTBD\b|\bFIXME\b|待定|占位|\[Outcome\]|\[TODO\]", re.I
)
# Workflow-in-description (model may skip body)
WORKFLOW_IN_DESC_RE = re.compile(
    r"(write the test first|first .{0,40} then|step ?\d|"
    r"always use|never use|1\. .{5,40} 2\.)",
    re.I,
)
PERSONAL_PATH_RE = re.compile(r"/Users/[A-Za-z0-9._-]+/")
PERSONAL_HOME_RE = re.compile(r"/home/[A-Za-z0-9._-]+/")
ALLOW_PATH = (
    "/Users/<", "/Users/test/", "/Users/joker/", "/Users/alice/",
    "/home/<", "/home/test/",
)


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
            buf = [] if rest in (">", "|", "") else [rest]
        elif key is not None:
            buf.append(line.strip())
    if key:
        fields[key] = " ".join(buf).strip().strip("\"'")
    return fields, None


def scan_paths(skill_dir: Path) -> list[dict]:
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
            if PERSONAL_PATH_RE.search(line):
                if any(a in line for a in ALLOW_PATH):
                    continue
            elif PERSONAL_HOME_RE.search(line):
                if any(a in line for a in ALLOW_PATH):
                    continue
            else:
                continue
            safe = PERSONAL_PATH_RE.sub("/Users/<user>/", line.strip())
            safe = PERSONAL_HOME_RE.sub("/home/<user>/", safe)[:160]
            hits.append({
                "file": str(p.relative_to(skill_dir)),
                "line": i,
                "snippet": safe,
                "principle": "portable_paths",
            })
    return hits


def audit_skill(skill_dir: Path) -> dict:
    skill_dir = skill_dir.resolve()
    errors: list[dict] = []
    warnings: list[dict] = []
    info: dict = {"skill_dir": str(skill_dir), "name": skill_dir.name}

    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        errors.append({
            "id": "missing_skill_md",
            "msg": "SKILL.md is missing",
            "principle": "structure_isnt_proof",
        })
        return _finish(info, errors, warnings)

    text = skill_md.read_text(encoding="utf-8", errors="replace")
    fields, fm_err = parse_frontmatter(text)
    if fm_err:
        errors.append({"id": "frontmatter", "msg": fm_err, "principle": "structure_isnt_proof"})

    name = (fields.get("name") or "").strip()
    desc = (fields.get("description") or "").strip()
    info["frontmatter_name"] = name
    info["description_len"] = len(desc)
    info["body_lines"] = text.count("\n") + 1

    if not name:
        errors.append({"id": "name_missing", "msg": "frontmatter name is missing", "principle": "structure_isnt_proof"})
    elif name != skill_dir.name:
        errors.append({
            "id": "name_mismatch",
            "msg": f"name '{name}' does not match directory '{skill_dir.name}'",
            "principle": "structure_isnt_proof",
        })
    elif not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or len(name) > 64:
        warnings.append({
            "id": "name_format",
            "msg": "prefer kebab-case name, at most 64 characters",
            "principle": "structure_isnt_proof",
        })

    if not desc:
        errors.append({
            "id": "desc_missing",
            "msg": "description is missing",
            "principle": "description_as_gate",
        })
    else:
        if len(desc) < 40:
            warnings.append({
                "id": "desc_short",
                "msg": "description is very short; hard to trigger reliably",
                "principle": "intent_triggers",
            })
        lower = desc.lower()
        if not any(h in lower for h in TRIGGER_HINTS):
            warnings.append({
                "id": "desc_no_trigger",
                "msg": "description lacks clear when-to-use language",
                "principle": "intent_triggers",
            })
        if WORKFLOW_IN_DESC_RE.search(desc):
            errors.append({
                "id": "description_as_manual",
                "msg": "description looks like step-by-step workflow; keep steps in the body",
                "principle": "description_as_gate",
            })

    body = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    if PLACEHOLDER_RE.search(body):
        warnings.append({
            "id": "placeholder",
            "msg": "unresolved placeholder left in SKILL.md",
            "principle": "defaults_dont_mask",
        })

    for m in re.finditer(r"`((?:scripts|references|assets|agents)/[^`\s]+)`", text):
        rel = m.group(1)
        if not (skill_dir / rel).exists():
            warnings.append({
                "id": "missing_ref",
                "msg": f"referenced path missing: {rel}",
                "principle": "structure_isnt_proof",
            })

    if info["body_lines"] > 650:
        warnings.append({
            "id": "body_long",
            "msg": f"SKILL.md is ~{info['body_lines']} lines; consider progressive disclosure",
            "principle": "signal_over_noise",
        })

    for h in scan_paths(skill_dir):
        errors.append({
            "id": "personal_path",
            "msg": f"{h['file']}:{h['line']} uses a machine-specific absolute path",
            "principle": "portable_paths",
            "detail": h["snippet"],
        })

    has_code = (skill_dir / "scripts").is_dir()
    has_evidence = any(
        (skill_dir / d).exists()
        for d in ("tests", "evals", "fixtures", "test-prompts.json")
    ) or (skill_dir / "scripts" / "verify.sh").is_file()
    if has_code and not has_evidence:
        warnings.append({
            "id": "no_automated_check",
            "msg": "scripts present but no tests/evals/verify — hard to prove changes",
            "principle": "structure_isnt_proof",
        })

    return _finish(info, errors, warnings)


def _finish(info, errors, warnings) -> dict:
    principles = sorted({
        x.get("principle") for x in errors + warnings if x.get("principle")
    })
    return {
        "ok": len(errors) == 0,
        "info": info,
        "errors": errors,
        "warnings": warnings,
        "principles_touched": principles,
        "principles_available": list(PRINCIPLES.keys()),
        "note": "Audit only. Fix issues, then re-run prove_skill.py.",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Audit skill quality principles")
    ap.add_argument("skill_folder")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
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
        print(f"skill: {info.get('name')}  lines≈{info.get('body_lines')}")
        print(
            f"ok: {report['ok']}  "
            f"errors={len(report['errors'])}  warnings={len(report['warnings'])}"
        )
        for e in report["errors"]:
            print(f"  ERROR [{e.get('principle')}] {e['msg']}")
        for w in report["warnings"]:
            print(f"  WARN  [{w.get('principle')}] {w['msg']}")
    if args.strict and not report["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    raise SystemExit(main())
