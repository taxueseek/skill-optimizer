# Prove Pipeline

> Live evidence gate for skills. Complements (does not replace) smoke tests and 7:2:1 evals.

## Why

session-digger taught: **green structure ≠ correct behavior**.  
Exit-code regexes, model placeholders, and false adapter routing only appeared under real data.

Prove forces:

```
freeze baseline → audit + live replay → change → re-prove → baseline_gate
```

## Commands

From skill-optimizer repo root:

```bash
# Full prove report (human)
python3 scripts/prove_skill.py /path/to/target-skill

# JSON for CI / baseline freeze
python3 scripts/prove_skill.py /path/to/target-skill --json -o /tmp/prove-after.json

# Structural audit only
python3 scripts/skill_audit.py /path/to/target-skill --json

# Live / fixture replay only
python3 scripts/live_replay.py /path/to/target-skill --json

# Refuse regressions
python3 scripts/baseline_gate.py \
  --baseline /tmp/prove-before.json \
  --current  /tmp/prove-after.json
```

Resolve optimizer root if needed:

```bash
export SKILL_OPTIMIZER_ROOT="$(cd "$(dirname "$0")/.." && pwd)"  # from scripts/
# or clone path of this repo
export SKILL_OPTIMIZER_ROOT="$HOME/src/skill-optimizer"
```

## Ship policy

| Condition | `ship_ready` |
|-----------|--------------|
| audit errors = 0 AND live ok (script/pytest green) | **true** + claim `live_or_automated_verify_passed` |
| audit errors = 0 AND live skipped (no verify assets) | **true** but claim `dry_run_only` + **F-NO-LIVE** warning |
| any audit error OR live failed | **false** — do not ship |

`--strict` exits 1 when not ship_ready.

## What target skills should provide

**Best:** `scripts/verify.sh` (or `prove.sh`) that exits 0 only if real checks pass.

**Good:** `tests/` with pytest.

**Minimum for agent skills without code:** `evals/` or `test-prompts.json` + documented agent smoke (with-skill vs baseline). Prove will mark live as assets_only / skipped.

## Insertion into platform creators

After **Smoke Test** / before **Package**:

1. Run `prove_skill.py` on the skill under construction  
2. Fix blockers  
3. Freeze JSON as baseline before further edits  
4. After edits: re-prove + `baseline_gate.py`  
5. Only then package / install  

## Relationship to existing eval pipeline

| Layer | Owner | Evidence |
|-------|--------|----------|
| Smoke (with/without skill) | platform creator | qualitative delta |
| 7:2:1 eval + grade | platform creator | pass_rate delta |
| **Prove** | **shared scripts/** | audit + live/fixture gate |
| Luban 活体 | luban skill | public product readiness |

Prove is the **cheap always-on ratchet**. Full eval remains for high-stakes skills.
