#!/usr/bin/env python3
"""Live / fixture replay helpers for the prove layer.

Does NOT invent agent behavior. Runs what the skill itself declares:

1. If ``scripts/verify.sh`` or ``scripts/prove.sh`` exists → run it
2. Else if ``package.json`` / ``pyproject`` with known test cmds → optional
3. Else if ``evals/`` or ``test-prompts.json`` or ``tests/`` exists → report presence
4. Else → status=skipped (must dry_run smoke via agent)

Usage:
  python3 live_replay.py <skill-folder>
  python3 live_replay.py <skill-folder> --json
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def _run(cmd: list[str], cwd: Path, timeout: int = 120) -> dict:
    t0 = time.time()
    try:
        cp = subprocess.run(
            cmd,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        return {
            "cmd": cmd,
            "exit_code": cp.returncode,
            "duration_sec": round(time.time() - t0, 3),
            "stdout_tail": (cp.stdout or "")[-2000:],
            "stderr_tail": (cp.stderr or "")[-1000:],
            "ok": cp.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"cmd": cmd, "exit_code": -1, "ok": False, "error": "timeout"}
    except OSError as e:
        return {"cmd": cmd, "exit_code": -1, "ok": False, "error": str(e)}


def replay(skill_dir: Path) -> dict:
    skill_dir = skill_dir.resolve()
    result = {
        "skill_dir": str(skill_dir),
        "mode": "none",
        "ok": False,
        "skipped": False,
        "runs": [],
        "assets": {},
    }

    assets = {
        "verify_sh": (skill_dir / "scripts" / "verify.sh").is_file(),
        "prove_sh": (skill_dir / "scripts" / "prove.sh").is_file(),
        "tests_dir": (skill_dir / "tests").is_dir(),
        "evals_dir": (skill_dir / "evals").is_dir(),
        "test_prompts": (skill_dir / "test-prompts.json").is_file(),
        "pytest": any((skill_dir / "tests").glob("test_*.py")) if (skill_dir / "tests").is_dir() else False,
    }
    result["assets"] = assets

    # Prefer explicit prove/verify scripts
    for name in ("prove.sh", "verify.sh"):
        script = skill_dir / "scripts" / name
        if script.is_file():
            result["mode"] = name
            # make executable best-effort
            try:
                script.chmod(script.stat().st_mode | 0o111)
            except OSError:
                pass
            run = _run(["bash", str(script)], skill_dir)
            result["runs"].append(run)
            result["ok"] = run.get("ok", False)
            return result

    # Pytest if present
    if assets["pytest"]:
        result["mode"] = "pytest"
        run = _run([sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"], skill_dir)
        result["runs"].append(run)
        result["ok"] = run.get("ok", False)
        return result

    # Presence-only: evals / test-prompts mean agent smoke is required
    if assets["evals_dir"] or assets["test_prompts"] or assets["tests_dir"]:
        result["mode"] = "assets_only"
        result["skipped"] = True
        result["ok"] = True  # structural OK; agent must run smoke separately
        result["message"] = (
            "Fixtures/evals present but no scripts/verify.sh — "
            "run agent smoke (with-skill vs baseline) before ship"
        )
        return result

    result["mode"] = "none"
    result["skipped"] = True
    result["ok"] = True
    result["message"] = (
        "No verify script or tests — mark as dry_run only; "
        "do not claim live proof (F-NO-LIVE)"
    )
    return result


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("skill_folder")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    skill = Path(args.skill_folder)
    if not skill.is_dir():
        print(f"ERROR: not a directory: {skill}", file=sys.stderr)
        return 2
    rep = replay(skill)
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=2))
    else:
        print(f"mode={rep['mode']} ok={rep['ok']} skipped={rep['skipped']}")
        if rep.get("message"):
            print(rep["message"])
        for r in rep.get("runs") or []:
            print(f"  exit={r.get('exit_code')} cmd={r.get('cmd')}")
    return 0 if rep.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
