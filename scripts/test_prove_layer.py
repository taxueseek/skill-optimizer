#!/usr/bin/env python3
"""Minimal tests for prove layer (stdlib unittest)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent


def run_py(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *args],
        cwd=str(SCRIPTS),
        capture_output=True,
        text=True,
    )


class TestProveLayer(unittest.TestCase):
    def test_audit_good_minimal_skill(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "demo-skill"
            d.mkdir()
            (d / "SKILL.md").write_text(
                "---\n"
                "name: demo-skill\n"
                "description: >\n"
                "  Use when the user asks to demo a skill ship gate,\n"
                "  prove a skill is ready, or run skill verification.\n"
                "  Triggers: prove skill, ship gate, demo skill verify.\n"
                "  NOT for: one-off chat.\n"
                "---\n\n"
                "# Demo\n\nDo the thing.\n",
                encoding="utf-8",
            )
            cp = run_py("skill_audit.py", str(d), "--json")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            rep = json.loads(cp.stdout)
            self.assertTrue(rep["ok"], rep)

    def test_prove_detects_hardcode(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "bad-skill"
            d.mkdir()
            (d / "SKILL.md").write_text(
                "---\n"
                "name: bad-skill\n"
                "description: Use when testing hardcode detection for prove layer.\n"
                "---\n\n"
                "Path: /Users/realperson/secret/project\n",
                encoding="utf-8",
            )
            cp = run_py("prove_skill.py", str(d), "--json")
            rep = json.loads(cp.stdout)
            self.assertFalse(rep["ship_ready"])
            self.assertTrue(any(e.get("pattern") == "F-HARDCODE" for e in rep["audit"]["errors"]))

    def test_live_verify_sh(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "live-skill"
            d.mkdir()
            (d / "SKILL.md").write_text(
                "---\n"
                "name: live-skill\n"
                "description: >\n"
                "  Use when testing live verify script for prove layer,\n"
                "  skill ship gate with verify.sh, or automated skill checks.\n"
                "---\n\n# Live\n",
                encoding="utf-8",
            )
            scripts = d / "scripts"
            scripts.mkdir()
            verify = scripts / "verify.sh"
            verify.write_text("#!/usr/bin/env bash\nset -euo pipefail\necho ok\nexit 0\n")
            verify.chmod(0o755)
            cp = run_py("prove_skill.py", str(d), "--json", "--strict")
            self.assertEqual(cp.returncode, 0, cp.stdout + cp.stderr)
            rep = json.loads(cp.stdout)
            self.assertTrue(rep["ship_ready"])
            self.assertEqual(rep["live"]["mode"], "verify.sh")

    def test_baseline_gate_blocks_regression(self):
        good = {"audit": {"errors": [], "warnings": []}, "ship_ready": True, "ok": True, "live": {"ok": True}}
        bad = {"audit": {"errors": [{"msg": "x"}], "warnings": []}, "ship_ready": False, "ok": False, "live": {"ok": True}}
        with tempfile.TemporaryDirectory() as td:
            b = Path(td) / "b.json"
            c = Path(td) / "c.json"
            b.write_text(json.dumps(good))
            c.write_text(json.dumps(bad))
            cp = run_py("baseline_gate.py", "--baseline", str(b), "--current", str(c), "--json")
            self.assertEqual(cp.returncode, 1)
            self.assertFalse(json.loads(cp.stdout)["passed"])


if __name__ == "__main__":
    unittest.main()
