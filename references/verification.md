# Verification (prove)

How to know a skill is ready — without treating verification as a dump of past war stories.

## Place in the loop

```
Gates → Write → Validate → Smoke → (optional full eval) → Verify → Package
```

- **Smoke** (platform creator): with-skill vs without-skill on one real prompt  
- **Eval** (platform creator): 7:2:1 cases, grading, benchmarks  
- **Verify** (shared scripts): structure + portability + automated check if declared  

Full eval is for high-stakes skills. Verify is the cheap bar every skill can clear.

## Commands

From the skill-optimizer repository root:

```bash
python3 scripts/prove_skill.py /path/to/skill
python3 scripts/prove_skill.py /path/to/skill --json -o report.json
python3 scripts/prove_skill.py /path/to/skill --strict

python3 scripts/skill_audit.py /path/to/skill
python3 scripts/live_replay.py /path/to/skill

# After an edit, ensure you did not regress:
python3 scripts/baseline_gate.py --baseline before.json --current after.json
```

## Ship recommendation

| Situation | Recommendation |
|-----------|----------------|
| No structural errors, automated check green | Ready to package |
| No structural errors, no automated check | Structurally OK; be honest that proof is limited — add verify/tests when the skill has scripts |
| Structural errors or failed automated check | Not ready |

## What a solid skill can declare

1. **`scripts/verify.sh`** — preferred; project-specific real checks, exit 0 on success  
2. **`tests/`** with pytest  
3. **Agent-only skills** — keep smoke protocol in the creator workflow; verify still audits structure and portability  

## Principles

See `quality-principles.md`. Checks are mapped to principles so advice stays general and transferable.
