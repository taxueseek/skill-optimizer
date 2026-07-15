#!/usr/bin/env python3
"""Prove layer orchestrator — skill-optimizer.

Combines structural audit + live/fixture replay into one ship gate.
Distilled from session-digger engineering practice:
  freeze baseline → measure → change → re-measure → gate.

Usage:
  python3 prove_skill.py <skill-folder>
  python3 prove_skill.py <skill-folder> --json
  python3 prove_skill.py <skill-folder> --json > prove-report.json
  python3 prove_skill.py <skill-folder> --strict

Exit codes:
  0 — ship_ready (or soft pass with warnings only when not --strict live)
  1 — blocked (errors or failed live)
  2 — bad args
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from skill_audit import audit_skill  # noqa: E402
from live_replay import replay  # noqa: E402


def prove(skill_dir: Path) -> dict:
    skill_dir = skill_dir.resolve()
    audit = audit_skill(skill_dir)
    live = replay(skill_dir)

    errors = audit.get("errors") or []
    warnings = audit.get("warnings") or []

    # Ship policy (digger-style: green CI is not enough, but empty live is allowed if declared)
    live_ok = bool(live.get("ok"))
    live_skipped = bool(live.get("skipped"))
    audit_ok = bool(audit.get("ok"))

    ship_ready = audit_ok and live_ok
    # If live skipped with no verify assets, still allow ship only when audit clean —
    # but flag F-NO-LIVE so humans don't over-claim.
    claims = []
    if ship_ready and not live_skipped:
        claims.append("live_or_automated_verify_passed")
    if ship_ready and live_skipped:
        claims.append("audit_clean_but_live_skipped_dry_run_only")
        warnings = list(warnings) + [{
            "id": "live_skipped",
            "msg": live.get("message") or "live replay skipped",
            "pattern": "F-NO-LIVE",
        }]

    blockers = [e["msg"] for e in errors]
    if not live_ok and not live_skipped:
        blockers.append("live_replay_failed")

    return {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "skill_dir": str(skill_dir),
        "skill_name": skill_dir.name,
        "ok": audit_ok and live_ok,
        "ship_ready": ship_ready and len(errors) == 0,
        "blockers": blockers,
        "claims": claims,
        "audit": audit,
        "live": live,
        "next_actions": _next_actions(errors, warnings, live),
        "note": (
            "Prove layer does not edit the skill. "
            "Fix blockers, re-run, optional: baseline_gate.py --baseline old.json --current new.json"
        ),
    }


def _next_actions(errors, warnings, live) -> list[str]:
    actions = []
    for e in errors[:5]:
        actions.append(f"Fix ERROR [{e.get('pattern')}]: {e['msg']}")
    if not live.get("ok") and not live.get("skipped"):
        actions.append("Fix failing scripts/verify.sh or tests/")
    if live.get("skipped") and live.get("mode") == "none":
        actions.append(
            "Add scripts/verify.sh (or tests/) for live proof, "
            "or run agent smoke with-skill vs baseline and attach evidence"
        )
    for w in warnings[:3]:
        if w.get("pattern") == "F-DESC-TRAP":
            actions.append("Rewrite description to triggering conditions only")
        elif w.get("pattern") == "F-HARDCODE":
            actions.append("Replace personal paths with $HOME / placeholders")
    if not actions:
        actions.append("Optional: freeze this report as baseline for next change")
    return actions


def main() -> int:
    ap = argparse.ArgumentParser(description="Prove a skill is ship-ready")
    ap.add_argument("skill_folder")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true", help="exit 1 if not ship_ready")
    ap.add_argument("-o", "--output", help="write JSON report to file")
    args = ap.parse_args()
    skill = Path(args.skill_folder)
    if not skill.is_dir():
        print(f"ERROR: not a directory: {skill}", file=sys.stderr)
        return 2

    report = prove(skill)

    if args.output:
        Path(args.output).write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"=== prove: {report['skill_name']} ===")
        print(f"ship_ready: {report['ship_ready']}")
        print(f"audit ok: {report['audit']['ok']}  "
              f"errors={len(report['audit']['errors'])}  "
              f"warnings={len(report['audit']['warnings'])}")
        live = report["live"]
        print(f"live mode: {live.get('mode')}  ok={live.get('ok')}  skipped={live.get('skipped')}")
        if report["blockers"]:
            print("blockers:")
            for b in report["blockers"]:
                print(f"  - {b}")
        print("next:")
        for a in report["next_actions"]:
            print(f"  → {a}")
        if report["claims"]:
            print("claims:", ", ".join(report["claims"]))

    if args.strict and not report["ship_ready"]:
        return 1
    if not report["ok"] and args.strict:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
