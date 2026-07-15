# Quality principles for skills

Reusable design rules for writing and verifying agent skills.  
They stay useful after any single bug is gone.

## 1. Trigger on intent

The skill should open when the user wants the **job**, not when they casually mention a related word.

- Prefer scenario phrases and exclusions  
- Avoid one-word or ultra-broad triggers  

## 2. Description is a gate

Frontmatter `description` answers: **when should this skill load?**  
The body answers: **how do we do it?**

If the description already walks through the whole workflow, models often skip the body.

## 3. Defaults must not mask reality

Placeholders and default labels exist so empty fields have a value — not so they override real configuration forever.

## 4. Checks need realistic inputs

A validator that only works on idealized examples will miss production shapes. Prefer samples that look like real user content.

## 5. Portable over personal

Skills travel. Prefer `$HOME`, env vars, and placeholders over absolute machine paths.

## 6. Structure is not proof

Valid frontmatter and a clean tree are necessary, not sufficient.  
Ship with at least one of:

- `scripts/verify.sh` (or equivalent) that exits 0 on success  
- automated tests  
- a short, repeatable smoke protocol (with skill vs without)

## 7. Measure direction of change

Before a meaningful edit, save a verification report. After the edit, compare.  
Improvements should not rely on memory alone.

## 8. One install source of truth

If the same skill exists in several directories, make clear which path the agent loads — or use a single shared install.

## 9. Signal over noise

Wrappers, system shells, and meta boilerplate are not the user’s real request.  
Design extraction and evaluation around the signal.

---

These principles power `scripts/skill_audit.py` and `scripts/prove_skill.py`.  
They are meant to transfer across platforms and projects.
