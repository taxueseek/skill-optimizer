#!/usr/bin/env python3
"""Quality principles for skill design and verification.

These are durable engineering principles — not a log of past bugs.
Checks in skill_audit map to principle ids; language stays product-facing.
"""
from __future__ import annotations

from typing import Any

# principle_id → definition (for docs / report enrichment)
PRINCIPLES: dict[str, dict[str, str]] = {
    "intent_triggers": {
        "title": "Trigger on intent, not collisions",
        "rule": (
            "A skill should fire when the user wants the job done, "
            "not when they merely mention a related word."
        ),
        "ask": "Would a casual mention of a keyword still force this skill open?",
    },
    "description_as_gate": {
        "title": "Description is a gate, not a manual",
        "rule": (
            "Frontmatter description states when to load the skill. "
            "How to do the work lives in the body — otherwise the model "
            "skips reading instructions."
        ),
        "ask": "If I only read the description, do I already know every step?",
    },
    "defaults_dont_mask": {
        "title": "Defaults must not mask real values",
        "rule": (
            "Placeholder or default fields should yield when real config appears. "
            "Never treat a label as permanent truth."
        ),
        "ask": "Can a real setting overwrite the default, or is it stuck?",
    },
    "realistic_checks": {
        "title": "Checks use realistic inputs",
        "rule": (
            "Validators and tests should exercise strings and shapes that "
            "appear in real use — not only idealized examples."
        ),
        "ask": "Does this check pass on a real sample, or only on the happy-path string?",
    },
    "portable_paths": {
        "title": "Portable over personal paths",
        "rule": (
            "Skills are shared assets. Prefer env vars, $HOME, and placeholders "
            "over machine-specific absolute paths."
        ),
        "ask": "Would this skill break on another machine without edits?",
    },
    "structure_isnt_proof": {
        "title": "Structure is not proof",
        "rule": (
            "Valid YAML and a tidy folder do not prove the skill works. "
            "Require an observable check: script, tests, or documented smoke."
        ),
        "ask": "What observable evidence shows this skill still works after a change?",
    },
    "measure_direction": {
        "title": "Measure before and after",
        "rule": (
            "Improvements need a baseline. Compare reports so changes cannot "
            "quietly get worse."
        ),
        "ask": "Do we know if this edit improved or degraded the skill?",
    },
    "single_source": {
        "title": "One source of truth for installs",
        "rule": (
            "When multiple copies exist, edit and run the same one — "
            "or document which root is authoritative."
        ),
        "ask": "Which path does the agent actually load?",
    },
    "signal_over_noise": {
        "title": "Prefer signal over wrapper noise",
        "rule": (
            "System shells, meta tags, and boilerplate should not be treated "
            "as the user's real request or the skill's real output."
        ),
        "ask": "Are we optimizing on noise that users never meant as content?",
    },
}


def as_list() -> list[dict[str, Any]]:
    return [{"id": k, **v} for k, v in PRINCIPLES.items()]
