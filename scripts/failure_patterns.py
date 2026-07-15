#!/usr/bin/env python3
"""Failure pattern library distilled from session-digger engineering.

Each pattern is a class of bugs that one structural fix can eliminate.
Used by skill_audit / prove_skill for diagnosis language and check IDs.
"""
from __future__ import annotations

from typing import Any

# id → definition
FAILURE_PATTERNS: dict[str, dict[str, Any]] = {
    "F-SUBSTR": {
        "title": "Over-broad substring routing / triggers",
        "digger_example": "Free-text 'sonnet'/'claude' forced Claude adapter",
        "skill_generalization": (
            "description or routing uses loose substrings that fire on mentions, "
            "not intent (e.g. trigger on any 'test' word)"
        ),
        "check": "description_substring_trap",
        "fix": "Use intent phrases + exclusions; require structural signals",
    },
    "F-PLACEHOLDER": {
        "title": "Default placeholder blocks real values",
        "digger_example": "_empty_stats(model='workbuddy') never updated",
        "skill_generalization": (
            "defaults / placeholders in SKILL or scripts swallow real config "
            "(model names, paths, env ids)"
        ),
        "check": "placeholder_defaults",
        "fix": "Only set defaults when field is empty; allow overwrite of known placeholders",
    },
    "F-ESCAPED": {
        "title": "Double-escaped regex / never-matching patterns",
        "digger_example": r"Exit Code:\\s* never matched real 'Exit Code: 1'",
        "skill_generalization": "Lint/test patterns don't match real fixture strings",
        "check": "regex_against_fixtures",
        "fix": "Unit-test patterns on real sample strings, not only docs",
    },
    "F-ADAPTER-TRAP": {
        "title": "Low-confidence specialized path hijacks generic",
        "digger_example": "Wrong dedicated adapter → all stats zero",
        "skill_generalization": (
            "Skill claims exclusive ownership of a broad domain without "
            "confidence gate; blocks better generic handling"
        ),
        "check": "overclaiming_description",
        "fix": "Confidence-gated routing; explicit exclusions; fallback path",
    },
    "F-INSTALL-DRIFT": {
        "title": "Multiple install copies diverge",
        "digger_example": "~/.claude/skills vs ~/.agents/skills different SHAs",
        "skill_generalization": "User has N copies; edited one, ran another",
        "check": "install_drift",
        "fix": "Symlink to single true source or document SESSION/SKILL root env",
    },
    "F-HARDCODE": {
        "title": "Personal absolute paths / identity in assets",
        "digger_example": "/Users/realname/... in SKILL.md",
        "skill_generalization": "Non-portable paths, machine names, real emails in skill",
        "check": "hardcode_paths",
        "fix": "Use $HOME, env vars, placeholders like /Users/<user>/",
    },
    "F-DESC-TRAP": {
        "title": "Description recaps workflow (Description Trap)",
        "digger_example": "N/A — skill-creator pattern",
        "skill_generalization": "Model follows description, skips SKILL.md body",
        "check": "description_trap",
        "fix": "Triggering conditions only; put steps in body",
    },
    "F-NO-LIVE": {
        "title": "Green CI / dry-run without live evidence",
        "digger_example": "Adapters looked fine until real JSONL replay",
        "skill_generalization": "Shipped without fixture replay or real command run",
        "check": "live_replay",
        "fix": "baseline_gate + real fixture or verify command before ship",
    },
    "F-NOISE-AS-SIGNAL": {
        "title": "System noise counted as user content",
        "digger_example": "env JSON / system-reminder counted as user messages",
        "skill_generalization": "Skill treats wrappers, meta, or boilerplate as primary I/O",
        "check": "noise_filtering",
        "fix": "Strip known wrappers; skip empty after clean",
    },
}


def list_patterns() -> list[dict[str, Any]]:
    return [{"id": k, **v} for k, v in FAILURE_PATTERNS.items()]


def pattern_ids() -> list[str]:
    return list(FAILURE_PATTERNS.keys())
