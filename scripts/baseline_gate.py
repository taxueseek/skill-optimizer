#!/usr/bin/env python3
"""Compare prove reports: refuse ship if new report is worse than baseline.

Usage:
  python3 baseline_gate.py --baseline before.json --current after.json
  python3 baseline_gate.py --baseline before.json --current after.json --json

Expects reports from prove_skill.py --json.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def gate(baseline: dict, current: dict) -> dict:
    b_err = len(baseline.get("audit", {}).get("errors") or baseline.get("errors") or [])
    c_err = len(current.get("audit", {}).get("errors") or current.get("errors") or [])
    b_warn = len(baseline.get("audit", {}).get("warnings") or baseline.get("warnings") or [])
    c_warn = len(current.get("audit", {}).get("warnings") or current.get("warnings") or [])
    b_ok = baseline.get("ship_ready", baseline.get("ok", False))
    c_ok = current.get("ship_ready", current.get("ok", False))
    b_live = (baseline.get("live") or {}).get("ok", True)
    c_live = (current.get("live") or {}).get("ok", True)

    reasons = []
    passed = True

    if c_err > b_err:
        passed = False
        reasons.append(f"errors increased {b_err} → {c_err}")
    if c_warn > b_warn + 2:  # allow tiny noise
        passed = False
        reasons.append(f"warnings increased sharply {b_warn} → {c_warn}")
    if b_ok and not c_ok:
        passed = False
        reasons.append("ship_ready flipped true → false")
    if b_live and not c_live:
        passed = False
        reasons.append("live replay regressed")

    # Improvements note
    improvements = []
    if c_err < b_err:
        improvements.append(f"errors {b_err} → {c_err}")
    if c_warn < b_warn:
        improvements.append(f"warnings {b_warn} → {c_warn}")
    if c_ok and not b_ok:
        improvements.append("became ship_ready")

    return {
        "passed": passed,
        "baseline_errors": b_err,
        "current_errors": c_err,
        "baseline_warnings": b_warn,
        "current_warnings": c_warn,
        "reasons": reasons,
        "improvements": improvements,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--current", required=True)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = gate(load(Path(args.baseline)), load(Path(args.current)))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("PASS" if result["passed"] else "FAIL")
        for r in result["reasons"]:
            print(" -", r)
        for i in result["improvements"]:
            print(" +", i)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
