---
name: new-skill
description: >
  Create new skills, edit existing ones, and verify skills work before deployment.
  Covers skill anatomy, TDD-based authoring, evaluation pipeline, and packaging.
  Use when the user wants to create a skill from scratch, edit or improve an existing skill,
  run evals to test a skill, benchmark skill performance, or optimize a skill's description
  for better triggering accuracy.
---

# New Skill (MiMo Code)

Create skills that extend your agent's capabilities with specialized workflows, tools, and domain knowledge. Optimized for MiMo Code's compose ecosystem with native `actor` tool integration.

**Core principle:** Writing skills IS Test-Driven Development applied to process documentation. If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

## Skill Anatomy

```
skill-name/
├── SKILL.md              # Required — frontmatter + instructions
├── scripts/              # Optional — executable code
├── references/           # Optional — loaded into context on demand
└── assets/               # Optional — used in output (templates, icons)
```

### SKILL.md Structure

**Frontmatter (YAML):**
- `name` (required): Skill identifier, kebab-case
- `description` (required): Triggering conditions only — "Use when..." format, max 500 chars
- `hidden` (optional): true if this skill is internal/infrastructure (not user-facing)

**Body:** Instructions and guidance. Only loaded after the skill triggers.

### Progressive Disclosure

1. **Frontmatter** — always in context (~100 words)
2. **SKILL.md body** — loaded when skill triggers (<500 lines)
3. **scripts/references/assets** — loaded on demand

Keep SKILL.md lean. Move details to `references/` files when approaching 500 lines.

## Skill Creation Process

### Step 1: Pre-flight — Three Gates

Before any design work, answer three questions. If any answer is no, stop.

1. **Without this skill, would the outcome be worse?** If MiMo Code can already handle it well enough, the skill is unnecessary overhead.
2. **Will the user use this skill more than five times?** One-shot automations are better served by a direct prompt.
3. **Can MiMo Code already do this natively?** If the model has the built-in capability, a skill adds complexity without value.

### Step 2: Determine Complexity Tier

| Tier | When to use | SKILL.md size | Directories |
|------|-------------|---------------|-------------|
| **Simple** | Pure instructions, no executable code | < 150 lines | None |
| **Medium** | Needs scripts or deep reference docs | 100-300 lines | `scripts/` or `references/` |
| **Complex** | Multiple workflows + cross-platform | 200-650 lines | Multiple subdirs |

When uncertain, start Simple. It is easier to add complexity than remove it.

### Step 3: Capture Intent

Extract from conversation history first — tools used, steps, corrections, input/output formats. Then fill gaps with the user: what should the skill do, when should it trigger, what's the expected output.

### Step 4: Choose Freedom Level

Match specificity to task fragility:
- **High freedom** (text instructions): many approaches are valid
- **Medium freedom** (parameterized scripts): a preferred pattern exists
- **Low freedom** (specific scripts): operations are fragile, consistency is critical

### Step 5: Write the SKILL.md

**Frontmatter description:** Start with "Use when...", describe triggering conditions only (NOT what the skill does). Formula: `[Action verb] + [value]. Use when [trigger 1], [trigger 2], ...`

**Body structure:**
1. Overview — what is this, core principle in 1-2 sentences
2. When to Use — bullet list of triggers, plus when NOT to use
3. Core workflow — numbered steps or flowchart for non-obvious decisions
4. Integration — how this skill connects to other compose skills
5. Red Flags — what NOT to do

**Style rules:**
- Use imperative form, explain the *why*
- Concise examples over verbose explanations
- One excellent example beats many mediocre ones
- No narrative storytelling
- No README.md, CHANGELOG.md, or other auxiliary files

### Step 6: Validate

Check the skill:
1. YAML frontmatter is valid
2. `name` and `description` fields present
3. Description is under 500 chars and starts with "Use when..."
4. No placeholder content ("TBD", "TODO", "implement later")
5. File paths referenced actually exist

### Step 7: Quick Smoke Test

Before running the full evaluation pipeline, do a quick smoke test with 1-2 subagents:

1. Spawn a subagent WITH the skill — verify it follows the instructions
2. Spawn a subagent WITHOUT the skill — verify baseline behavior
3. If the skill doesn't trigger or the output is wrong, fix it before investing in full evaluation

**Subagent prompt format:**
```
operation:
  action: "spawn"
  description: "smoke-test-with-skill"
  subagent_type: "general"
  prompt: |
    Follow the skill instructions below.

    ## Skill: <skill-name>
    <paste full SKILL.md content>

    ## Task
    <a simple test task that should trigger this skill>

    Solve the task using the skill's instructions.
```

Do NOT tell the subagent it's being tested.

## Evaluation Pipeline

This is the key differentiator: a systematic, automated evaluation that proves the skill actually works.

### Overview

The evaluation pipeline uses MiMo Code's existing tools (`actor` with `spawn`, `bash`, `read`, `write`) to run a full with-skill vs without-skill comparison — no new tools needed.

**Critical architecture decision:** Subagents return results in their response but do NOT reliably write files to disk. The controller (main agent) is responsible for persisting all results to disk. This avoids the flaky file-write problem entirely.

### Actor Tool Schema

The actor tool accepts a single `operation` object with these fields:

```
operation.action: "run" | "spawn"
operation.description: string (short label for this subagent)
operation.subagent_type: "general" | "explore"
operation.prompt: string (full instructions for the subagent)
```

- `"run"` — blocking, returns result inline
- `"spawn"` — non-blocking, returns `actor_id` immediately, result delivered via `actor-notification`

Use `"spawn"` for all evaluation subagents so they run in parallel.

### Step 1: Create Test Cases

Create 10-20 test prompts at 7:2:1 ratio (common / edge / anomalous). Each case: what the user says, what the skill should do, what it should NOT do.

Save to `evals/evals.json`:
```json
[
  {"id": 0, "prompt": "user's task prompt", "expectations": ["output includes X", "used script Y"]},
  {"id": 1, "prompt": "another prompt", "expectations": []}
]
```

### Step 2: Run Evaluations in Batches

For each test case, spawn TWO subagents using `action: "spawn"`:

**With-skill run:**
```
operation:
  action: "spawn"
  description: "eval-<ID>-with-skill"
  subagent_type: "general"
  prompt: |
    Follow the skill instructions below to solve the task.

    ## Skill: <skill-name>
    <paste full SKILL.md content>

    ## Task
    <eval prompt>

    Solve the task using the skill's instructions. Return your complete answer.
```

**Baseline run** (same prompt, no skill):
```
operation:
  action: "spawn"
  description: "eval-<ID>-without-skill"
  subagent_type: "general"
  prompt: |
    Solve this task to the best of your ability. Do NOT use any skill or external instructions.

    ## Task
    <eval prompt> (same as above)

    Return your complete answer.
```

**Batch size:** Run 2-3 test cases at a time (4-6 subagents concurrently via `spawn`). Do NOT launch all 10-20 cases at once. After each batch completes, review results before proceeding. This catches fundamental issues early without wasting compute.

### Step 3: Collect Results (Controller Responsibility)

When each subagent completes, you receive an `actor-notification` with its result. The result is in the notification message — NOT on disk.

**Immediately write each result to disk when the notification arrives:**

```
evals/iteration-1/eval-<ID>/with_skill/response.md
evals/iteration-1/eval-<ID>/without_skill/response.md
```

Also create `eval_metadata.json` for each test case:
```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name",
  "prompt": "the user's task prompt",
  "assertions": ["output includes X", "uses formula Y"]
}
```

### Step 4: Grade Each Run

After all subagents in a batch complete and results are persisted, spawn a grader subagent:

```
operation:
  action: "run"
  description: "grader-eval-<ID>"
  subagent_type: "general"
  prompt: |
    You are a Grader. Evaluate the execution result against expectations.

    Task prompt: <the eval prompt>
    Expectations:
    - <expectation 1>
    - <expectation 2>

    ## With-skill result (read from disk):
    <path-to-with-skill-response>

    ## Without-skill result (read from disk):
    <path-to-without-skill-response>

    For each expectation:
    1. Search for evidence in both results
    2. Determine PASS or FAIL for each configuration
    3. Cite specific evidence (quote text)

    Also critique: are the expectations discriminating? Would a trivially wrong answer pass?

    Save results to: evals/iteration-1/eval-<ID>/grading.json
```

Use `"run"` (blocking) for graders since you need their results before aggregating.

Grading format:
```json
{
  "eval_id": 0,
  "expectations": [
    {"text": "...", "with_skill": "pass", "without_skill": "fail", "evidence": "..."}
  ],
  "with_skill_summary": {"passed": 2, "failed": 0, "total": 2, "pass_rate": 1.0},
  "without_skill_summary": {"passed": 1, "failed": 1, "total": 2, "pass_rate": 0.5}
}
```

### Step 5: Aggregate Benchmark

After all graders complete, aggregate results with a Python script via `bash`:

```python
# Read all grading.json files from evals/iteration-1/eval-*/
# Compute per-configuration: pass_rate mean ± stddev
# Compute delta: with_skill vs without_skill
# Save to evals/iteration-1/benchmark.json and benchmark.md
```

Present results as a markdown table:

```
| Metric | with_skill | without_skill | Delta |
|--------|-----------|---------------|-------|
| Pass rate | 85% ± 5% | 35% ± 8% | +50% |
| Cases tested | 10 | 10 | — |
```

### Step 6: Analyze and Improve

Read the benchmark data and surface patterns:
- Which expectations always pass in both? (non-discriminating — skill doesn't help here)
- Which always fail in both? (broken or beyond capability)
- Which show high variance? (flaky)
- Where does the skill help most?

Based on findings, improve the skill's SKILL.md and re-run into `iteration-2/`. Stop when the user is happy or progress stalls.

## Description Optimization

The description field in SKILL.md frontmatter determines whether MiMo Code invokes the skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

### How to Test Triggering

Create 20 eval queries — a mix of should-trigger and should-not-trigger. Save as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

The queries must be realistic. Bad: `"Format this data"`. Good: `"ok so my boss just sent me this xlsx file and she wants me to add a column that shows the profit margin as a percentage"`.

For the should-trigger queries (8-10): different phrasings of the same intent, some formal, some casual. Include cases where the user doesn't explicitly name the skill but clearly needs it.

For the should-not-trigger queries (8-10): near-misses — queries that share keywords but actually need something different.

### Optimization Loop

1. Present the eval set to the user for review
2. For each query, spawn a subagent to test triggering (does MiMo Code load the skill?)
3. Analyze failures, propose a better description
4. Re-run up to 5 iterations, select by test score
5. Apply the best description to SKILL.md frontmatter

## Integration with Compose Ecosystem

Skills can reference other compose skills:
- Use `compose:ask` for user interaction decisions
- Use `compose:tdd` discipline for verification steps
- Use `compose:verify` before claiming completion
- Use `task` tool for progress tracking
- Use `actor` tool for subagent dispatch

**Important:** Compose skills do NOT appear in subagents' `available_skills` list. When a subagent needs a compose skill, pass the relevant SKILL.md content directly in the subagent's prompt. Include this note: "The skills listed below are NOT in your available_skills — this is by design. You can invoke them by name using the skill tool."

## What NOT to Create

- One-off solutions (hardcode in the task)
- Standard practices well-documented elsewhere
- Project-specific conventions (put in CLAUDE.md)
- Mechanical constraints enforceable with regex/validation (automate it)

## Red Flags

**Never:**
- Skip testing because "it's obvious"
- Create multiple skills without testing each
- Include narrative examples
- Summarize workflow in the description field
- Create auxiliary files (README, CHANGELOG, etc.)
- Tell subagents they're being tested (contaminates results)
- Rely on subagents to write files to disk (they are unreliable at this — the controller must persist results)
- Use `action: "run"` for eval subagents (blocks the main agent — use `"spawn"` instead)
- Launch more than 6 subagents concurrently (4-6 is the sweet spot)

**Always:**
- Test with subagents before deploying
- Keep SKILL.md under 500 lines
- Use "Use when..." format for description
- Reference compose skills by name, not by @link
- Launch eval subagents with `action: "spawn"` for parallelism
- Persist subagent results to disk immediately upon receiving actor-notification
- Use `action: "run"` only for graders (blocking is fine since you need their output)
- Grade both with-skill and baseline before drawing conclusions
- Call the actor tool with `operation: {action, description, subagent_type, prompt}` — all four fields required
