#!/usr/bin/env python3
"""Run the skill's own automated check, if it declares one.

Order:
  1. scripts/verify.sh or scripts/prove.sh
  2. pytest under tests/
  3. else skip (agent smoke remains the owner's responsibility)

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
        "pytest": (
            any((skill_dir / "tests").glob("test_*.py"))
            if (skill_dir / "tests").is_dir()
            else False
        ),
    }
    result["assets"] = assets

    for name in ("prove.sh", "verify.sh"):
        script = skill_dir / "scripts" / name
        if not script.is_file():
            continue
        result["mode"] = name
        try:
            script.chmod(script.stat().st_mode | 0o111)
        except OSError:
            pass
        run = _run(["bash", str(script)], skill_dir)
        result["runs"].append(run)
        result["ok"] = run.get("ok", False)
        return result

    if assets["pytest"]:
        result["mode"] = "pytest"
        run = _run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=line"],
            skill_dir,
        )
        result["runs"].append(run)
        result["ok"] = run.get("ok", False)
        return result

    if assets["evals_dir"] or assets["test_prompts"] or assets["tests_dir"]:
        result["mode"] = "manual_eval_assets"
        result["skipped"] = True
        result["ok"] = True
        result["message"] = (
            "Eval assets exist but no verify.sh/pytest entrypoint — "
            "run agent smoke (with skill vs without) and keep notes"
        )
        return result

    result["mode"] = "none"
    result["skipped"] = True
    result["ok"] = True
    result["message"] = (
        "No automated check declared — structural audit only; "
        "prefer adding scripts/verify.sh or tests/ for future changes"
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
    return 0 if rep.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
