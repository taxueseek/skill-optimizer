---
name: grok-skill-creator
description: >
  Create new Grok skills, improve existing ones, and optimize skill descriptions for better triggering.
  Use when the user wants to create a skill from scratch, edit or improve an existing skill,
  run evals to test a skill, benchmark skill performance, or optimize a skill's description
  for better triggering accuracy.
---

# Create Skill

This skill helps you create new Grok skills and iteratively improve existing ones.

Figure out where the user is in the process — they might have a vague idea, a draft, or a finished skill that needs testing — and jump in to help them progress. Offer to optimize the skill's description for better triggering after the skill is done.

## Communicating with the user

Match the user's technical level. "Evaluation" and "benchmark" are fine; for deeper jargon, wait for cues that the user knows it. Briefly explain when in doubt.

## Creating a skill

### Pre-flight: Three Gates

Before any design work, answer three questions. If any answer is no, stop or rethink.

1. **Without this skill, would the outcome be worse?** If Grok can already handle it well enough, the skill is unnecessary overhead.
2. **Will the user use this skill more than five times?** One-shot automations are better served by a direct prompt or script.
3. **Can Grok already do this natively?** If the model has the built-in capability, a skill adds complexity without value.

All three must pass before proceeding.

### Determine Complexity Tier

| Tier | When to use | SKILL.md size | Directories |
|------|-------------|---------------|-------------|
| **Simple** | Pure instructions, no executable code | < 150 lines | None |
| **Medium** | Needs scripts or deep reference docs | 100-300 lines | `scripts/` or `references/` |
| **Complex** | Multiple workflows + hooks + cross-platform | 200-650 lines | Multiple subdirs |

When uncertain, start Simple. It is easier to add complexity than remove it.

### Capture Intent

Extract from conversation history first — tools used, steps, corrections, input/output formats. Then fill gaps with the user: what should the skill do, when should it trigger, what's the expected output, and whether test cases are needed (objectively verifiable outputs benefit from tests; subjective ones don't).

### Choose Freedom Level

Match specificity to task fragility: **high freedom** (text instructions) when many approaches are valid; **medium freedom** (parameterized scripts) when a preferred pattern exists; **low freedom** (specific scripts) when operations are fragile and consistency is critical.

### Write the SKILL.md

Based on the user interview, fill in these components:

- **name**: kebab-case, max 64 chars, verb-led (`deploy-k8s` not `k8s-deployment`). Namespace by tool when it helps (`gh-address-comments`). Folder name must match.
- **description**: primary triggering mechanism — include what the skill does AND specific trigger contexts. Make it slightly "pushy" to combat undertriggering. Formula: `[Action verb] + [value]. Use when [trigger 1], [trigger 2], ...`
- **paths** (optional): glob patterns for automatic discovery (e.g., `src/**/*.tsx`). User can always invoke via `/<skill-name>` regardless.

### Skill Writing Guide

**Anatomy:** `SKILL.md` (required) + optional `scripts/`, `references/`, `assets/`.

**Progressive disclosure:** metadata always in context → SKILL.md body on trigger → bundled resources on demand. Keep SKILL.md under 500 lines; add hierarchy when approaching the limit. Reference files one level deep, with TOC when >100 lines.

**Context window is a shared resource.** Grok is already very smart — only add what it doesn't have. Challenge every paragraph: "Does this justify its token cost?"

**Writing patterns:** use imperative form, explain the *why*, avoid rigid ALWAYS/NEVER structures. Start with a draft, revise with fresh eyes, aim for generality. Explain the *why* behind everything — Grok has good theory of mind and when given a good harness can go beyond rote instructions. Even if the user's feedback is terse or frustrated, try to understand what they actually want and need, then transmit that understanding into the instructions.

**Output format template:** `# [Title]` → `## Executive summary / Key findings / Recommendations`

**No extraneous files** — no README, INSTALLATION_GUIDE, CHANGELOG, etc. Only what the agent needs to do the job. Skills must not contain malware or exploit code. A skill's contents should not surprise the user in their intent — don't create misleading skills or skills designed to facilitate unauthorized access. Things like "roleplay as an XYZ" are OK.

### Test Cases

Create 10-20 test prompts at 7:2:1 ratio (common / edge / anomalous). Each case: what the user says, what the skill should do, what it should NOT do.

Measure: routing accuracy (>90%), output usability (>80%), token consumption (redundant <20%). Save to `evals/evals.json`.

## Running and evaluating test cases

This section is one continuous sequence — don't stop partway through.

Organize results by iteration (`iteration-1/`, `iteration-2/`, etc.) and within that, each test case gets a directory (`eval-0/`, `eval-1/`, etc.).

### Spawn all runs (with-skill AND baseline) in the same turn

For each test case, spawn two subagents in the same turn — one with the skill, one without. This is important: don't spawn the with-skill runs first and then come back for baselines later. Launch everything at once so they all finish around the same time.

**With-skill run:**
```
Execute this task:
- Skill path: <path-to-skill>
- Task: <eval prompt>
- Input files: <eval files if any, or "none">
- Save outputs to: <workspace>/iteration-<N>/eval-<ID>/with_skill/outputs/
- Outputs to save: <what the user cares about>
```

**Baseline run** (same prompt, but the baseline depends on context):
- **Creating a new skill**: no skill at all. Same prompt, no skill path, save to `without_skill/outputs/`.
- **Improving an existing skill**: the old version. Before editing, snapshot the skill (`cp -r <skill-path> <workspace>/skill-snapshot/`), then point the baseline subagent at the snapshot. Save to `old_skill/outputs/`.

Write an `eval_metadata.json` for each test case (assertions can be empty for now). Give each eval a descriptive name based on what it's testing — not just "eval-0". Use this name for the directory too.

```json
{
  "eval_id": 0,
  "eval_name": "descriptive-name-here",
  "prompt": "The user's task prompt",
  "assertions": []
}
```

### While runs are in progress, draft assertions

Don't just wait for the runs to finish — use this time productively. Draft quantitative assertions for each test case and explain them to the user. If assertions already exist in `evals/evals.json`, review them and explain what they check.

Good assertions are objectively verifiable and have descriptive names — they should read clearly so someone glancing at the results immediately understands what each one checks. Subjective skills (writing style, design quality) are better evaluated qualitatively — don't force assertions onto things that need human judgment.

Update the `eval_metadata.json` files and `evals/evals.json` with the assertions once drafted. Also explain to the user what they'll see — both the qualitative outputs and the quantitative benchmark.

### As runs complete, capture timing data

When each subagent task completes, you receive a notification containing timing data. Save this immediately to `timing.json` in the run directory:

```json
{
  "total_tokens": 84852,
  "duration_ms": 23332,
  "total_duration_seconds": 23.3
}
```

This is the only opportunity to capture this data — process each notification as it arrives rather than trying to batch them.

### Grade, aggregate, and present results

Once all runs are done:

1. **Grade each run** — spawn a grader subagent that evaluates each assertion against the outputs. The grader follows the instructions in `agents/grader.md`. Save results to `grading.json` in each run directory. Use this grading format:

```json
{
  "expectations": [
    {
      "text": "The output includes the name 'John Smith'",
      "passed": true,
      "evidence": "Found in transcript Step 3: 'Extracted names: John Smith, Sarah Johnson'"
    }
  ],
  "summary": {
    "passed": 2,
    "failed": 1,
    "total": 3,
    "pass_rate": 0.67
  }
}
```

2. **Aggregate into benchmark** — collect all grading results into a `benchmark.json` with pass_rate, time, and tokens for each configuration, with mean ± stddev and the delta. You can use the `scripts/aggregate_benchmark.py` script:

```bash
python -m scripts.aggregate_benchmark <workspace>/iteration-T --skill-name <name>
```

This produces `benchmark.json` and `benchmark.md` with pass_rate, time, and tokens for each configuration, with mean ± stddev and the delta.

3. **Do an analyst pass** — read the benchmark data and surface patterns the aggregate stats might hide. Look for assertions that always pass regardless of skill (non-discriminating), high-variance evals (possibly flaky), and time/token tradeoffs. The analyst follows the instructions in `agents/analyzer.md`.

4. **Present results to the user** — show both qualitative outputs and quantitative data directly in the conversation. For each test case, show the prompt, the output from with-skill and without-skill, the grading results, and ask for the user's feedback.

**Optional: Visual review with eval-viewer.** If the eval outputs include files the user needs to inspect (images, documents, spreadsheets), generate a self-contained HTML review page:

```bash
python <skill-creator-path>/eval-viewer/generate_review.py \
  <workspace>/iteration-T \
  --skill-name "my-skill" \
  --benchmark <workspace>/iteration-T/benchmark.json
```

This opens a browser with two tabs: "Outputs" (each test case with inline-rendered files and feedback textboxes) and "Benchmark" (quantitative comparison). The user can click through each test case, leave feedback, and submit all reviews at once. Feedback is saved to `feedback.json` in the workspace.

For headless environments without a browser, use `--static <output_path>` to write a standalone HTML file instead of starting a server.

### Read the feedback

When the user tells you they're done reviewing, collect their feedback. If you used the eval-viewer, read `feedback.json`:

```json
{
  "reviews": [
    {"run_id": "eval-0-with_skill", "feedback": "the chart is missing axis labels", "timestamp": "..."},
    {"run_id": "eval-1-with_skill", "feedback": "", "timestamp": "..."},
    {"run_id": "eval-2-with_skill", "feedback": "perfect, love this", "timestamp": "..."}
  ],
  "status": "complete"
}
```

Empty feedback means the user thought it was fine. Focus your improvements on the test cases where the user had specific complaints.

## Improving the skill

This is the heart of the loop. You've run the test cases, the user has reviewed the results, and now you need to make the skill better based on their feedback.

### Diagnose and Improve

Classify issues by nature: **functional defects** (quick scan), **efficiency issues** (quantitative analysis), **architecture issues** (deep diagnosis), **trigger issues** (classifier calibration). Fix functional defects first.

For every improvement, quantify token impact: necessary / optional / redundant. Target: redundant <20%. Move reference files to `references/` and load on demand.

### How to think about improvements

- **Generalize** from feedback — don't overfit to specific examples. If stubborn, try different metaphors.
- **Stay lean** — read transcripts, not just outputs. Cut what isn't pulling its weight.
- **Explain the why** — ALWAYS/NEVER in all caps is a yellow flag.
- **Bundle repeated work** — if subagents independently write similar scripts, put it in `scripts/`.

### The iteration loop

Apply improvements → rerun into `iteration-<N+1>/` (including baselines) → collect feedback → repeat. Stop when the user is happy, feedback is all positive, or progress stalls.

## Forward-testing

Stress-test the skill by launching subagents that don't know they're testing. Use real task prompts ("Use skill-x at /path to solve y"), never meta-prompts ("Review the skill..."). Use fresh threads, pass raw artifacts, clean up between iterations. If it only succeeds with leaked context, tighten the skill.

## Advanced: Blind comparison

For situations where you want a more rigorous comparison between two versions of a skill (e.g., the user asks "is the new version actually better?"), there's a blind comparison system. The basic idea is: give two outputs to an independent grader subagent without telling it which is which, and let it judge quality. Then analyze why the winner won. The grader follows `agents/comparator.md` and the analyzer follows `agents/analyzer.md`.

This is optional and most users won't need it. The human review loop is usually sufficient.

## Description Optimization

The description field in SKILL.md frontmatter is the primary mechanism that determines whether Grok invokes a skill. After creating or improving a skill, offer to optimize the description for better triggering accuracy.

### How Skill Triggering Works

Grok sees name + description in system-reminder and decides whether to consult the skill. Simple queries may not trigger even with a perfect match (Grok handles them directly); complex/multi-step queries reliably trigger when the description matches. Use substantive eval queries — simple ones like "read file X" won't trigger regardless.

### Generate trigger eval queries

Create 20 eval queries — a mix of should-trigger and should-not-trigger. Save as JSON:

```json
[
  {"query": "the user prompt", "should_trigger": true},
  {"query": "another prompt", "should_trigger": false}
]
```

The queries must be realistic and something a Grok user would actually type. Not abstract requests, but concrete and specific with a good amount of detail.

Bad: `"Format this data"`, `"Search the web"`, `"Create a chart"`
Good: `"ok so my boss just sent me this xlsx file (it's in my downloads, called something like 'Q4 sales final FINAL v2.xlsx') and she wants me to add a column that shows the profit margin as a percentage. The revenue is in column C and costs are in column D I think"`

For the **should-trigger** queries (8-10), think about coverage — different phrasings of the same intent, some formal, some casual. Include cases where the user doesn't explicitly name the skill or file type but clearly needs it. For the **should-not-trigger** queries (8-10), the most valuable ones are the near-misses — queries that share keywords or concepts with the skill but actually need something different. Think adjacent domains, ambiguous phrasing where a naive keyword match would trigger but shouldn't. Avoid obviously irrelevant negatives ("Write a fibonacci function" for a PDF skill tests nothing).

### Review the eval set with the user

Present the eval set for review. They can edit, toggle, add/remove entries.

**Optional: Visual eval review.** Generate an HTML review page from `assets/eval_review.html` — replace `__EVAL_DATA_PLACEHOLDER__`, `__SKILL_NAME_PLACEHOLDER__`, `__SKILL_DESCRIPTION_PLACEHOLDER__`, write to `/tmp/eval_review_<name>.html`, and open it. User edits, then clicks "Export Eval Set" to download to `~/Downloads/eval_set.json`.

### Run the optimization loop

All subagents use `LongCat-2.0-Preview` (best balance of context efficiency, error rate, sample size for this task type).

For each query, spawn a subagent to test triggering. Run each query 3 times. Use 60% training / 40% held-out test. Analyze failures, then spawn an improver subagent to propose a better description — generalize from failures, keep it 100-200 words, focus on intent, make it distinctive. Run up to 5 iterations, select by test score.

### Apply the result

Take the best description and update the skill's SKILL.md frontmatter. Show the user before/after and report the scores.

## Continuous Evolution

Capture patterns across cycles: recurring fix patterns → `references/engineering-patterns.md`, new anti-patterns → document them, token baseline shifts >20% → re-calibrate. When this skill itself is updated, run a self-diagnosis pass.

## Reference files

The agents/ directory contains instructions for specialized subagents. Read them when you need to spawn the relevant subagent.

- `agents/grader.md` — How to evaluate assertions against outputs
- `agents/comparator.md` — How to do blind A/B comparison between two outputs
- `agents/analyzer.md` — How to analyze why one version beat another

The references/ directory has additional documentation:
- `references/schemas.md` — JSON structures for evals.json, grading.json, benchmark.json, etc.

---

## Packaging

Run `python <skill-creator-path>/scripts/quick_validate.py <skill-folder>` first. Fix any errors.

Build `.skill` file (zip archive):
```bash
cd <skill-dir>/..
zip -r <skill-name>.skill <skill-name>/ \
  -x "<skill-name>/evals/*" \
  -x "<skill-name>/iteration-*/*" \
  -x "<skill-name>/workspace/*" \
  -x "<skill-name>/__pycache__/*" \
  -x "<skill-name>/.DS_Store"
```
Include `SKILL.md` + `scripts/`, `references/`, `assets/`. Exclude evals, iterations, workspace, pycache, .DS_Store.

Also generate `<skill-name>-summary.md` with: description, what it does, when to use, file structure, usage (`/<skill-name>`), requirements.

---
