---
name: mimo-skill-creator
description: >
  Create, test, and optimize skills for MiMo Code.
  Use when creating a skill, editing one, testing if a skill works,
  optimizing skill triggering, or packaging a .skill file.
  Triggers: "create skill", "new skill", "edit skill", "test skill",
  "skill not triggering", "optimize description", "package skill",
  "prove skill", "skill ship gate".
  NOT for: CLAUDE.md rules, one-off prompts, project conventions.
---

# Skill Creator — MiMo Code

Create skills that extend MiMo Code with specialized workflows. Leverages `task`, `bash`, `read`, `write`, `edit`, `skill` tools natively.

## Three Gates (Pre-flight)

All must pass before starting. If any is no → stop.

1. **MiMo Code can't already do this well?** → Skill is overhead.
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

**Frontmatter** — only 3 fields are read by MiMo Code:

```yaml
name: kebab-case       # Required. Letters, digits, hyphens. Max 64 chars.
description: >         # Required. Max 500 chars. Triggering conditions ONLY.
  Use when [trigger], [trigger], or [symptom].
hidden: true           # Optional. true = loaded but not in available_skills list.
```

**Placement** — MiMo Code discovers SKILL.md recursively from:
- Project: `.mimocode/skills/**`, `.claude/skills/**`, `.agents/skills/**`, `.codex/skills/**`
- Global: `~/.config/mimocode/skills/**`, `~/.claude/skills/**`, `~/.agents/skills/**`
- Config: `skills.paths` and `skills.urls` in `mimocode.json`

## The #1 Mistake: Description Trap

When description summarizes the workflow, the model follows the description and skips the body.

```yaml
# ❌ BAD: Summarizes workflow → model takes shortcut
description: Use for TDD — write test first, watch it fail, write minimal code

# ✅ GOOD: Triggering conditions only → forces model to read the body
description: Use when implementing features or bugfixes, before writing code
```

**Formula:** `[Action verb] + [value]. Use when [trigger 1], [trigger 2], ...`
Include 5+ triggers. Add exclusions. Be slightly "pushy".

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

**Body structure:** Overview → When to Use → Core Workflow → Quick Reference → Common Mistakes → Integration

**Rules:**
- Imperative form, explain the *why*
- One excellent example > many mediocre
- ALWAYS/NEVER in caps → yellow flag → reframe with reasoning
- Context window is shared — every token must earn its place
- Cross-reference by name (`compose:tdd`), not @link (force-loads, burns context)
- Target: redundant content < 20%

**Skill types need different structures:**

| Type | Focus | Key section |
|------|-------|-------------|
| Discipline | Rules | Rationalization table + Red Flags |
| Technique | How-to | Step-by-step + edge cases |
| Pattern | Mental model | When to apply + counter-examples |
| Reference | API/docs | Searchable index + retrieval paths |

### 5. Validate

- YAML valid, `name` + `description` present
- Description < 500 chars, "Use when..." format
- No placeholders, referenced paths exist

### 6. Smoke Test

Spawn 2 subagents via `task` tool — one WITH skill, one WITHOUT:

```
task({
  action: "spawn",
  agent: "general",
  description: "smoke-test-with-skill",
  prompt: "Follow these instructions:\n\n## Skill: <name>\n<paste SKILL.md>\n\n## Task\n<test task>"
})
```

Verify baseline differs. Do NOT tell subagent it's being tested.

### 7. Iterate

Improve → re-test → repeat until user satisfied or progress stalls.

### 8. Prove (ship gate)

```bash
python3 scripts/prove_skill.py <path-to-target-skill>
python3 scripts/prove_skill.py <path-to-target-skill> --json -o /tmp/prove.json
python3 scripts/prove_skill.py <path-to-target-skill> --strict
```

Ship only when `ship_ready`. Prefer target skill `scripts/verify.sh` or `tests/`.  
Baseline ratchet: `baseline_gate.py --baseline before.json --current after.json`.  
See `../references/prove-pipeline.md` and `../references/failure-patterns.md`.

## Evaluation Pipeline

### Architecture

MiMo Code subagents return results in response but do NOT reliably write to disk. **Controller persists all results.** Use `spawn` for parallel eval, `run` for blocking graders.

### Flow

**1. Test cases** — 10-20 prompts, 7:2:1 ratio (common/edge/anomalous):
```json
[{"id": 0, "prompt": "user task", "expectations": ["includes X"]}]
```

**2. Paired subagents** — batch 2-3 cases (4-6 concurrent):
```
task({ action: "spawn", agent: "general", description: "eval-0-with",
       prompt: "<SKILL.md content>\n\nTask: <prompt>" })
task({ action: "spawn", agent: "general", description: "eval-0-without",
       prompt: "Solve this task without any external instructions.\n\nTask: <same prompt>" })
```

**3. Persist on notification** — immediately write responses:
```
evals/iter-N/eval-<ID>/with_skill.md
evals/iter-N/eval-<ID>/without_skill.md
```

**4. Grade** — `run` blocking grader per case:
```json
{"expectations": [{"text": "...", "with_skill": "pass", "without_skill": "fail", "evidence": "..."}]}
```

**5. Aggregate** via `bash` + Python → `benchmark.md`:
```
| Metric | with_skill | without_skill | Delta |
| Pass rate | 85% ± 5% | 35% ± 8% | +50% |
```

**6. Analyze** — non-discriminating (always pass), flaky (high variance), broken (always fail both).

### Metrics

| Metric | Target |
|--------|--------|
| Routing accuracy | > 90% |
| Output usability | > 80% |
| Redundant tokens | < 20% |

## Description Optimization

1. Create 20 realistic eval queries (should-trigger + should-not-trigger near-misses)
2. User reviews
3. Spawn subagent per query to test triggering — 3 runs each
4. Analyze failures → improve description → re-run (up to 5 iterations)
5. Select by **test score** (not train) to avoid overfitting
6. Apply to frontmatter

## Bulletproofing Discipline Skills

Close loopholes explicitly. Build rationalization table from testing:

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. 30 seconds to test. |
| "I'll test after" | Tests-after = what it does. Tests-first = what it should do. |

Red Flags list → easy self-check:
```
## Red Flags — STOP
- Code before test
- "This is different because..."
**All = Delete. Start over.**
```

## Problem Classification

| Class | Meaning | Fix |
|-------|---------|-----|
| A — Functional | Broken | Quick scan |
| B — Efficiency | Wastes tokens | Quant analysis |
| C — Architecture | Structural | Deep diagnosis |
| D — Trigger | Wrong trigger | Classifier cal |

P0 (blocking) → P1 (noticeable) → P2 (nice).

## Compose Integration

Skills can reference compose skills: `compose:ask`, `compose:tdd`, `compose:verify`, `compose:plan`.
Use `task` tool for subagent dispatch, `skill` tool for loading skills.

**Key:** Compose skills do NOT appear in subagents' `available_skills`. Pass SKILL.md content directly in subagent prompt.

## Packaging

1. Validate frontmatter  
2. **Prove:** `python3 scripts/prove_skill.py <skill> --strict`  
3. Package only if ship_ready:

```bash
cd <root> && zip -r my-skill.skill my-skill/ \
  -x "my-skill/evals/*" -x "my-skill/iter-*/*" -x "*__pycache__*"
```

## 5 Common Failures

| # | Failure | Fix |
|---|---------|-----|
| 1 | Description too vague | 5+ trigger phrases |
| 2 | SKILL.md dumping ground (800+ lines) | < 500 lines, split to references/ |
| 3 | ALWAYS/NEVER caps | Explain reasoning |
| 4 | No smoke test | Run Step 6 before shipping |
| 5 | Description summarizes workflow | Triggering conditions ONLY |
| 6 | No live proof (F-NO-LIVE) | Step 8 prove + verify.sh/tests |

## Meta-Advice

1. **Description is everything.** Great skill + bad description = invisible.
2. **Explain why.** Model generalizes better with reasoning.
3. **Draft then look fresh.** First draft: too detailed or too vague.
4. **Generalize from feedback.** Encode the principle, not the fix.
5. **Context window is shared.** Every token earns its place.
6. **Test before deploying.** 15 min testing saves hours debugging.
