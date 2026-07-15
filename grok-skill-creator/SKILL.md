---
name: grok-skill-creator
description: >
  Create, test, and optimize Grok skills.
  Use when creating a skill from scratch, editing one, testing if a skill works,
  optimizing skill triggering, benchmarking performance, or packaging a .skill file.
  Triggers: "create skill", "new skill", "edit skill", "test skill",
  "skill not triggering", "optimize description", "package skill", "benchmark skill",
  "prove skill", "skill ship gate", "live verify skill".
  NOT for: CLAUDE.md rules, one-off prompts, project conventions.
---

# Skill Creator — Grok

Create skills that extend Grok with specialized workflows. Leverages Grok's native subagent spawning, `bash`, `read`, `write`, `edit` tools.

## Three Gates (Pre-flight)

All must pass. If any is no → stop.

1. **Grok can't already do this well?** → Skill is overhead.
2. **User will use it 5+ times?** → One-shot → direct prompt.
3. **Model has it built-in?** → Skill adds complexity, not value.

## Skill Anatomy

```
skill-name/
├── SKILL.md          # Required — frontmatter + instructions
├── scripts/          # Optional — executable code
├── references/       # Optional — loaded on demand
└── assets/           # Optional — templates, icons, fonts
```

**Frontmatter:**

```yaml
name: kebab-case       # Required. Letters, digits, hyphens. Max 64 chars. Verb-led.
description: >         # Required. Triggering conditions + what it does. Slightly "pushy".
  Use when [trigger], [trigger], or [symptom].
paths:                 # Optional. Glob patterns for auto-discovery.
  - "src/**/*.tsx"
```

**Discovery** — Grok finds SKILL.md from:
- Project: `./.grok/skills/` (walked up to repo root)
- User: `~/.grok/skills/`
- Plugins: any enabled plugin's `skills/` directory
- Config: `[skills] paths` in `~/.grok/config.toml`
- Claude Code compat: `.claude/skills/`, `~/.agents/skills/`, `AGENTS.md`

**Invocation**: User-invocable skills appear as slash commands `/<skill-name>`.

## The #1 Mistake: Description Trap

When description summarizes the workflow, the model follows the description and skips the body.

```yaml
# ❌ BAD: Summarizes workflow → model takes shortcut
description: Use for TDD — write test first, watch it fail, write minimal code

# ✅ GOOD: Triggering conditions only → forces model to read the body
description: Use when implementing features or bugfixes, before writing code
```

**Formula:** `[Action verb] + [value]. Use when [trigger 1], [trigger 2], ...`
Include 5+ triggers. Add exclusions. Be slightly "pushy" to combat undertriggering.

## Creation: 7 Steps

### 1. Classify Complexity

| Tier | SKILL.md | Dirs |
|------|----------|------|
| Simple | < 150 lines | None |
| Medium | 100-300 | `scripts/` or `references/` |
| Complex | 200-650 | Multiple |

Start Simple. Easier to add than remove.

### 2. Capture Intent

From conversation history first: tools used, steps, corrections, I/O formats.
Fill gaps: what should it do? when trigger? expected output? test cases needed?

### 3. Choose Freedom Level

- **High** (text): many valid approaches
- **Medium** (parameterized scripts): preferred pattern exists
- **Low** (specific scripts): fragile ops, consistency critical

### 4. Write SKILL.md

**Body structure:** Overview → When to Use → Core Workflow → Quick Reference → Common Mistakes

**Rules:**
- Imperative form, explain the *why*
- One excellent example > many mediocre
- ALWAYS/NEVER in caps → yellow flag → reframe with reasoning
- Context window is shared — every token must earn its place
- Keep SKILL.md < 500 lines; add hierarchy when approaching limit
- References one level deep, TOC when > 100 lines
- No README, CHANGELOG, or extraneous files

**Skill types need different structures:**

| Type | Focus | Key section |
|------|-------|-------------|
| Discipline | Rules | Rationalization table + Red Flags |
| Technique | How-to | Step-by-step + edge cases |
| Pattern | Mental model | When to apply + counter-examples |
| Reference | API/docs | Searchable index + retrieval paths |

### 5. Validate

- YAML valid, `name` + `description` present
- Description has 5+ trigger phrases
- No placeholders, referenced paths exist

### 6. Smoke Test

Spawn 2 subagents — one WITH skill, one WITHOUT. Verify baseline differs. Do NOT tell subagent it's being tested.

### 7. Iterate

Improve → re-test → repeat until user satisfied or progress stalls.

### 8. Prove (ship gate — always before package)

Green smoke ≠ proven. Run the **shared prove layer** (session-digger engineering practice):

```bash
# From skill-optimizer repo root (or set SKILL_OPTIMIZER_ROOT)
python3 scripts/prove_skill.py <path-to-target-skill>
python3 scripts/prove_skill.py <path-to-target-skill> --json -o /tmp/prove.json
python3 scripts/prove_skill.py <path-to-target-skill> --strict   # CI: exit 1 if not ship_ready
```

**Policy:**

| Result | Action |
|--------|--------|
| `ship_ready: true` + live not skipped | Package / install OK |
| `ship_ready: true` but live skipped | Ship only if user accepts **dry_run**; file F-NO-LIVE |
| blockers present | Fix → re-prove; do not package |

**Baseline ratchet** (after a change):

```bash
python3 scripts/prove_skill.py <skill> --json -o /tmp/before.json
# ... edit skill ...
python3 scripts/prove_skill.py <skill> --json -o /tmp/after.json
python3 scripts/baseline_gate.py --baseline /tmp/before.json --current /tmp/after.json
```

Target skills should prefer `scripts/verify.sh` (exit 0 on real checks) or `tests/`. See `../references/prove-pipeline.md` and `../references/failure-patterns.md`.

## Evaluation Pipeline

### Architecture

Subagents return results in response but may not reliably write to disk. **Controller persists all results.** Use parallel spawning for eval runs, blocking for graders.

### Flow

**1. Test cases** — 10-20 prompts, 7:2:1 ratio (common/edge/anomalous):
```json
[{"id": 0, "prompt": "user task", "expectations": ["includes X"]}]
```

**2. Paired subagents** — spawn WITH + WITHOUT in same turn, batch 2-3 cases:

With-skill:
```
Execute this task:
- Skill path: <path>
- Task: <prompt>
- Save outputs to: <workspace>/iter-N/eval-<ID>/with_skill/outputs/
```

Without-skill (baseline): same prompt, no skill path → `without_skill/outputs/`

**3. Persist on notification** — immediately write responses to disk. This is the only opportunity to capture timing data.

**4. Grade** — blocking grader per case:
```json
{"expectations": [{"text": "...", "passed": true, "evidence": "..."}],
 "summary": {"passed": 2, "failed": 1, "total": 3, "pass_rate": 0.67}}
```

**5. Aggregate** → `benchmark.json` + `benchmark.md`:
```
| Metric | with_skill | without_skill | Delta |
| Pass rate | 85% ± 5% | 35% ± 8% | +50% |
```

Use `scripts/aggregate_benchmark.py` when available.

**6. Analyze** — non-discriminating (always pass), flaky (high variance), broken (always fail both).

**7. Present** — show qualitative outputs + quantitative data. For visual review, use `eval-viewer/generate_review.py` (HTML with Outputs + Benchmark tabs).

### Metrics

| Metric | Target |
|--------|--------|
| Routing accuracy | > 90% |
| Output usability | > 80% |
| Redundant tokens | < 20% |

## Description Optimization

Grok sees name + description in system-reminder. Simple queries may not trigger even with perfect match; complex/multi-step queries trigger reliably.

1. Create 20 realistic eval queries (should-trigger + should-not-trigger near-misses)
2. User reviews and edits
3. Spawn subagent per query to test triggering — 3 runs each
4. Use `LongCat-2.0-Preview` model (best context efficiency for this task)
5. 60% train / 40% held-out test split
6. Analyze failures → improve description → re-run (up to 5 iterations)
7. Select by **test score** (not train) to avoid overfitting
8. Apply to frontmatter, show before/after

**Eval query quality matters.** Bad: `"Format this data"`. Good: `"ok so my boss just sent me this xlsx file (called 'Q4 sales final FINAL v2.xlsx') and she wants me to add a profit margin column. Revenue is in column C and costs in column D I think"`

## Bulletproofing Discipline Skills

Close loopholes explicitly. Build rationalization table from testing:

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. 30 seconds to test. |
| "I'll test after" | Tests-after = what it does. Tests-first = what it should do. |
| "Skill is obviously clear" | Clear to you ≠ clear to other agents. |

Red Flags list → easy self-check:
```
## Red Flags — STOP
- Code before test
- "This is different because..."
- "I'm confident it's good"
**All = Delete. Start over.**
```

## Problem Classification

| Class | Meaning | Fix |
|-------|---------|-----|
| A — Functional | Broken | Quick scan |
| B — Efficiency | Wastes tokens | Quant analysis |
| C — Architecture | Structural | Deep diagnosis |
| D — Trigger | Wrong trigger | Classifier cal |

P0 (blocking) → P1 (noticeable) → P2 (nice). Fix functional first.

## Forward-testing & Blind Comparison

**Forward-testing:** Launch subagents that don't know they're testing. Use real task prompts, never meta-prompts. Fresh threads, raw artifacts, clean up between iterations.

**Blind comparison:** Give two outputs to an independent grader without telling it which is which. Judge quality, then analyze why the winner won. Uses `agents/comparator.md` + `agents/analyzer.md`. Optional — human review loop usually sufficient.

## Packaging

1. Validate: `python scripts/quick_validate.py <skill-folder>`
2. **Prove:** `python3 ../scripts/prove_skill.py <skill-folder> --strict` (from this creator dir, or use repo-root path)
3. Package only if ship_ready:

```bash
cd <skill-dir>/.. && zip -r <name>.skill <name>/ \
  -x "<name>/evals/*" -x "<name>/iteration-*/*" \
  -x "<name>/workspace/*" -x "*__pycache__*" -x "*.DS_Store"
```

Generate `<name>-summary.md`: description, when to use, file structure, usage (`/<name>`), requirements. Note prove claims (live vs dry_run).

## 5 Common Failures

| # | Failure | Fix |
|---|---------|-----|
| 1 | Description too vague | 5+ trigger phrases, formula |
| 2 | SKILL.md dumping ground (800+ lines) | < 500 lines, split to references/ |
| 3 | ALWAYS/NEVER caps | Explain reasoning |
| 4 | No smoke test before shipping | Run Step 6 |
| 5 | Description summarizes workflow | Triggering conditions ONLY |
| 6 | No live proof (F-NO-LIVE) | Step 8 prove + `scripts/verify.sh` or tests |

## Reference Files

- `agents/grader.md` — assertion evaluation
- `agents/comparator.md` — blind A/B comparison
- `agents/analyzer.md` — benchmark analysis
- `references/schemas.md` — JSON structures (evals, grading, benchmark)
- `scripts/aggregate_benchmark.py` — benchmark aggregation
- `scripts/quick_validate.py` — pre-packaging validation
- `../scripts/prove_skill.py` — **ship gate** (audit + live)
- `../references/prove-pipeline.md` — prove policy
- `../references/failure-patterns.md` — F-* pattern catalog

## Meta-Advice

1. **Description is everything.** Great skill + bad description = invisible.
2. **Explain why.** Model generalizes better with reasoning.
3. **Draft then look fresh.** First draft: too detailed or too vague.
4. **Generalize from feedback.** Encode the principle, not the fix.
5. **Bundle repeated work.** If subagents independently write similar scripts → `scripts/`.
6. **Context window is shared.** Every token earns its place.
7. **Test before deploying.** 15 min testing saves hours debugging.
