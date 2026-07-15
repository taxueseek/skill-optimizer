# Failure Pattern Library

> Distilled from **session-digger** engineering (v0.9.8–v0.9.11) for skill-optimizer **prove** layer.
> Each pattern is a *class* of defects: one structural fix eliminates a family of bugs.

| ID | Title | Skill symptom | Fix direction |
|----|--------|---------------|---------------|
| **F-SUBSTR** | Over-broad substring triggers | Fires when user merely *mentions* a word | Intent phrases + exclusions; structural signals |
| **F-PLACEHOLDER** | Defaults block real values | Config stuck on dummy model/path | Only fill empty fields; allow overwrite |
| **F-ESCAPED** | Double-escaped regex | Lint/tests never match real strings | Unit-test patterns on fixtures |
| **F-ADAPTER-TRAP** | Low-confidence specialized path | Wrong skill/handler → empty results | Confidence gate + fallback |
| **F-INSTALL-DRIFT** | Multiple install copies | Edit A, run B | Single true source / env root |
| **F-HARDCODE** | Personal absolute paths | Non-portable skill assets | `$HOME`, env, `/Users/<user>/` |
| **F-DESC-TRAP** | Description recaps workflow | Model skips body | Trigger conditions only |
| **F-NO-LIVE** | No live evidence | “Looks fine” until production | `scripts/verify.sh` or agent smoke + baseline |
| **F-NOISE-AS-SIGNAL** | Wrappers counted as content | System/env text as user I/O | Strip wrappers; skip empty after clean |

Machine-readable catalog: `scripts/failure_patterns.py`.

## How prove uses these

- `skill_audit.py` tags findings with `pattern: F-*`
- `prove_skill.py` lists next actions by pattern
- Agents should **encode the principle**, not patch one case
