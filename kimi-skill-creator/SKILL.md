---
name: kimi-skill-creator
description: >
  Create, test, and optimize Kimi Code skills.
  Use when creating a skill, editing one, testing if a skill works,
  optimizing triggering, or packaging a .skill file.
  Triggers: "create skill", "new skill", "edit skill", "test skill",
  "skill not triggering", "optimize description", "package skill",
  "SKILL.md", "whenToUse", "verify skill", "skill ready to ship".
  NOT for: AGENTS.md rules, one-off prompts, project conventions.
---

# Skill Creator — Kimi Code

Create skills that extend Kimi Code with specialized workflows. Leverages native `Agent`, `AgentSwarm`, `Bash`, `Read`, `Write`, `Edit`, `Skill`, `AskUserQuestion` tools.

## Three Gates (Pre-flight)

All must pass. If any is no → stop.

1. **Kimi can't already do this well?** → Skill is overhead.
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

**Frontmatter** — Kimi Code reads these fields:

```yaml
name: kebab-case              # Required (dir type). Case-insensitive.
description: >                # Required (dir type). Model uses this to decide when to load.
  Use when [trigger], [trigger], or [symptom].
type: prompt                  # prompt (default) | inline (same) | flow (manual only)
whenToUse: >                  # Trigger scenario. Also accepts when-to-use / when_to_use.
  当用户让我 [场景] 时
disableModelInvocation: false # true = block auto-invocation (only /skill: manual)
arguments:                    # Named params: $name in body. Also: $ARGUMENTS, $0, $1
  - target
  - mode
```

**Placeholders in body:** `$ARGUMENTS`, `$0`/`$1`/`$<name>`, `${KIMI_SKILL_DIR}`

**Discovery** — priority: Project > User > Extra > Built-in
- Project: `.kimi-code/skills/`, `.agents/skills/`
- User: `~/.kimi-code/skills/`, `~/.agents/skills/`
- Extra: `extra_skill_dirs` in config.toml

**Invocation:** `/skill:name args` (slash) or auto via description + whenToUse (unless `disableModelInvocation: true` or `type: flow`). Max nesting: 3 levels.

## The #1 Mistake: Description Trap

When description summarizes the workflow, the model follows the description and skips the body.

```yaml
# ❌ BAD: Summarizes workflow → model takes shortcut
description: Use for TDD — write test first, watch it fail, write minimal code

# ✅ GOOD: Triggering conditions only → forces model to read the body
description: Use when implementing features or bugfixes, before writing code
```

**Formula:** `[Action verb] + [value]. Use when [trigger 1], [trigger 2], ...`
Include 5+ triggers. Add exclusions. Be slightly "pushy". Use `whenToUse` for scenario description (Chinese-friendly).

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

**Kimi-specific patterns:**
- Use `arguments` for parameterized skills: `$target`, `$mode` in body
- Use `type: flow` for skills that should ONLY be invoked manually (no auto-trigger)
- Use `disableModelInvocation: true` to force explicit `/skill:` invocation

### 5. Validate

- YAML valid, `name` + `description` present
- `whenToUse` provides clear scenario
- No placeholders, referenced paths exist

### 6. Smoke Test

Spawn 2 subagents via `Agent` tool — one WITH skill, one WITHOUT:

```
Agent({
  prompt: "Follow these instructions:\n\n## Skill: <name>\n<paste SKILL.md>\n\n## Task\n<test task>",
  description: "smoke-test-with-skill",
  subagent_type: "coder"
})
```

Verify baseline differs. Do NOT tell subagent it's being tested. Use `AgentSwarm` for batch parallel testing.

### 7. Iterate

Improve → re-test → repeat until user satisfied or progress stalls.

### 8. Verify before package

```bash
# skill-optimizer 仓库根目录
python3 scripts/prove_skill.py <path-to-target-skill>
python3 scripts/prove_skill.py <path-to-target-skill> --strict
```

检查的是通用质量原则：触发是否像意图、description 是否只做门控、路径是否可移植、有没有可重复的自动检查。  
有脚本的 skill 优先提供 `scripts/verify.sh` 或 `tests/`；改动前后可用 `baseline_gate.py` 对比报告。  
详见 `../references/verification.md`、`../references/quality-principles.md`。

## Evaluation Pipeline

### Architecture

Subagents return results in response but do NOT reliably write to disk. **Controller persists all results.** Use `Agent` (foreground) or `AgentSwarm` (batch parallel) for eval runs.

### Flow

**1. Test cases** — 10-20 prompts, 7:2:1 ratio (common/edge/anomalous):
```json
[{"id": 0, "prompt": "user task", "expectations": ["includes X"]}]
```

**2. Paired subagents** — use `AgentSwarm` for batch parallel:
```
AgentSwarm({
  prompt_template: "## Skill: <name>\n<SKILL.md content>\n\nTask: <ITEM>",
  items: ["eval-0: <prompt0>", "eval-1: <prompt1>", ...],
  subagent_type: "coder"
})
```

Baseline: same prompts without skill content.

**3. Persist results** — write responses to:
```
evals/iter-N/eval-<ID>/with_skill.md
evals/iter-N/eval-<ID>/without_skill.md
```

**4. Grade** — `Agent` per case:
```json
{"expectations": [{"text": "...", "with_skill": "pass", "without_skill": "fail", "evidence": "..."}]}
```

**5. Aggregate** via `Bash` + Python → `benchmark.md`:
```
| Metric | with_skill | without_skill | Delta |
| Pass rate | 85% ± 5% | 35% ± 8% | +50% |
```

**6. Analyze** — non-discriminating, flaky, broken assertions.

**7. Present** — use `AskUserQuestion` for structured feedback collection.

### Metrics

| Metric | Target |
|--------|--------|
| Routing accuracy | > 90% |
| Output usability | > 80% |
| Redundant tokens | < 20% |

## Description Optimization

1. Create 20 realistic eval queries (should-trigger + should-not-trigger near-misses)
2. User reviews via `AskUserQuestion`
3. Spawn `Agent` per query to test triggering — 3 runs each
4. Analyze failures → improve description + `whenToUse` → re-run (up to 5 iterations)
5. Select by **test score** (not train) to avoid overfitting
6. Apply to frontmatter

## Bulletproofing Discipline Skills

Close loopholes explicitly. Build rationalization table from testing:

| Excuse | Reality |
|--------|---------|
| "Too simple to test" | Simple code breaks. 30 seconds to test. |
| "I'll test after" | Tests-after = what it does. Tests-first = what it should do. |

Red Flags list:
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

## Packaging

1. Validate frontmatter (name, description, whenToUse)
2. `python3 scripts/prove_skill.py <skill> --strict`
3. Package only when verification passes:

```bash
cd <root> && zip -r my-skill.skill my-skill/ \
  -x "my-skill/evals/*" -x "my-skill/iter-*/*" -x "*__pycache__*"
```

## 5 Common Failures

| # | Failure | Fix |
|---|---------|-----|
| 1 | Description too vague | 5+ trigger phrases + whenToUse |
| 2 | SKILL.md dumping ground (800+ lines) | < 500 lines, split to references/ |
| 3 | ALWAYS/NEVER caps | Explain reasoning |
| 4 | No smoke test | Run Step 6 before shipping |
| 5 | Description summarizes workflow | Triggering conditions ONLY |
| 6 | No way to re-check after edits | Step 8 + verify.sh/tests |

## Meta-Advice

1. **Description is everything.** Great skill + bad description = invisible.
2. **Explain why.** Model generalizes better with reasoning.
3. **Draft then look fresh.** First draft: too detailed or too vague.
4. **Generalize from feedback.** Encode the principle, not the fix.
5. **Context window is shared.** Every token earns its place.
6. **Test before deploying.** 15 min testing saves hours debugging.
7. **Use Kimi-native tools.** `AgentSwarm` for parallel eval, `AskUserQuestion` for structured feedback, `TodoList` for progress tracking.
