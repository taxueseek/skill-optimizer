#!/usr/bin/env python3
"""Skill verification gate for skill-optimizer.

Answers one question: is this skill ready to ship *with evidence*?

  structure + portability audit
  + automated check if the skill provides one (verify script / tests)
  = ship recommendation

Not a catalog of old bugs — a reusable quality bar.

Usage:
  python3 prove_skill.py <skill-folder>
  python3 prove_skill.py <skill-folder> --json
  python3 prove_skill.py <skill-folder> --strict
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_audit import audit_skill  # noqa: E402
from live_replay import replay  # noqa: E402


def prove(skill_dir: Path) -> dict:
    skill_dir = skill_dir.resolve()
    audit = audit_skill(skill_dir)
    live = replay(skill_dir)

    errors = list(audit.get("errors") or [])
    warnings = list(audit.get("warnings") or [])
    audit_ok = bool(audit.get("ok"))
    live_ok = bool(live.get("ok"))
    live_skipped = bool(live.get("skipped"))

    ship_ready = audit_ok and live_ok
    evidence = []
    if ship_ready and not live_skipped:
        evidence.append("automated_check_passed")
    if ship_ready and live_skipped:
        evidence.append("structure_ok_no_automated_check")
        warnings.append({
            "id": "evidence_limited",
            "msg": (
                live.get("message")
                or "No verify script or tests — treat as structural pass only"
            ),
            "principle": "structure_isnt_proof",
        })

    blockers = [e["msg"] for e in errors]
    if not live_ok and not live_skipped:
        blockers.append("automated check failed")

    return {
        "version": "1.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill_dir": str(skill_dir),
        "skill_name": skill_dir.name,
        "ok": audit_ok and live_ok,
        "ship_ready": ship_ready and not errors,
        "blockers": blockers,
        "evidence": evidence,
        "audit": audit,
        "live": live,
        "next_actions": _next(errors, warnings, live),
        "note": (
            "Does not modify the skill. "
            "Optional: baseline_gate.py to compare two prove reports."
        ),
    }


def _next(errors, warnings, live) -> list[str]:
    out = []
    for e in errors[:5]:
        out.append(e["msg"])
    if not live.get("ok") and not live.get("skipped"):
        out.append("Fix the failing verify script or test suite")
    if live.get("skipped") and live.get("mode") == "none":
        out.append(
            "Add scripts/verify.sh or tests/ so changes can be proven automatically; "
            "or keep a short smoke protocol (with-skill vs without) for agent-only skills"
        )
    for w in warnings:
        if w.get("principle") == "description_as_gate":
            out.append("Rewrite description as when-to-use only; move steps into the body")
            break
    if not out:
        out.append("Optional: save this report and re-run after the next edit")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="Verify a skill is ready to ship")
    ap.add_argument("skill_folder")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("-o", "--output")
    args = ap.parse_args()
    skill = Path(args.skill_folder)
    if not skill.is_dir():
        print(f"ERROR: not a directory: {skill}", file=sys.stderr)
        return 2

    report = prove(skill)
    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"=== verify: {report['skill_name']} ===")
        print(f"ship_ready: {report['ship_ready']}")
        a = report["audit"]
        print(
            f"structure: ok={a['ok']}  "
            f"errors={len(a['errors'])}  warnings={len(a['warnings'])}"
        )
        live = report["live"]
        print(
            f"check: mode={live.get('mode')}  "
            f"ok={live.get('ok')}  skipped={live.get('skipped')}"
        )
        if report["blockers"]:
            print("blockers:")
            for b in report["blockers"]:
                print(f"  - {b}")
        print("next:")
        for step in report["next_actions"]:
            print(f"  → {step}")
        if report["evidence"]:
            print("evidence:", ", ".join(report["evidence"]))

    if args.strict and not report["ship_ready"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
