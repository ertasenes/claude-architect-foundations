# Week 4 Cheat Sheet — Claude Code Configuration & Workflows (Domain 3, ~20%)

Quick-reference notes for exam prep. Everything here maps to Task Statements 3.1–3.6.

---

## 1. CLAUDE.md memory hierarchy (TS 3.1)

**Three levels:**
- `~/.claude/CLAUDE.md` → **user-level**: personal, applies to ALL your projects, NOT in version control, NEVER shared with teammates.
- Root `CLAUDE.md` (or `.claude/CLAUDE.md`) → **project-level**: committed to git, everyone who clones/pulls gets it automatically.
- `subdir/CLAUDE.md` → **directory-level**: loads when Claude works with files in that subtree (NOT at startup).

**Loading behavior (memorize this table):**

| Mechanism | When it loads | Token savings? |
|---|---|---|
| CLAUDE.md (user/project) | at session startup | — |
| `@import` inside CLAUDE.md | at session startup (expanded inline) | NO — organization only |
| directory CLAUDE.md | when files in that folder are touched | yes (conditional) |
| `.claude/rules/*.md` with `paths:` | when a matching file is touched | YES (this is the point) |
| `.claude/rules/*.md` without `paths:` | at startup, unconditionally | NO |

**@import facts:**
- Syntax: a line containing `@path/to/file.md`; path relative to the CLAUDE.md location.
- Organization tool ONLY. Imported files still load at launch and consume context.

**Diagnostics toolkit:**
- `/memory` → startup inventory: which memory files are loaded right now.
- `Loaded <file>` lines in session output → in-session trigger proof for conditional layers (directory CLAUDE.md, path rules).
- Conditional layers do NOT appear in the startup `/memory` list — their absence there is normal.

**Core principle (recurs across ALL domains):**
- CLAUDE.md is **context, not enforcement**. Prompt/config text = guidance (probabilistic). Hooks, programmatic gates, CI checks, `allowed-tools` = locks (deterministic).
- Any question with "must never / guaranteed / no exceptions" → the answer is a programmatic mechanism, NEVER a CLAUDE.md instruction.

**Exam traps:**
- "New teammate cloned the repo but doesn't get the rules" → rules were written user-level; move them to project-level.
- "Claude behaves inconsistently across sessions" → first step is `/memory`, NOT reinstalling, NOT temperature=0.
- Temperature controls randomness, not rule compliance — permanently wrong answer for guarantee/compliance questions.
- Config applies **forward, not retroactively**: adding a rule does not fix files written before it.
- Config added **mid-session may not be picked up** → stale session inventory; fix = fresh session (same principle as Week 2 stale-context rule).
- Keep CLAUDE.md short (≈ under 200 lines); long files reduce adherence.
- Watch for **instruction-reality drift**: CLAUDE.md referencing things that don't exist (e.g., a missing .venv) erodes trust in the whole file.
- Project-specific workflows (file paths like tasks/todo.md) do NOT belong in user-level memory.

---

## 2. Path-scoped rules (TS 3.3)

**Syntax:**
```markdown
---
paths:
  - "**/*.test.tsx"
  - "terraform/**/*"
---
# Rule content here
```

**Glob semantics:**
- `*` = anything within ONE path level (`*.py` = .py files in that dir only).
- `**` = any depth of directories (`**/*.py` = all .py files anywhere). In practice `**` also matched zero intermediate dirs in our test.
- Combined: `week*/**/*.py` = all .py files under folders starting with "week".

**When to choose what:**
- Conventions for a file TYPE spread across the repo (test files, .tf files) → path-scoped rule. NOT copies of CLAUDE.md in every folder (maintenance nightmare = classic wrong answer).
- Conventions for one folder → directory CLAUDE.md.
- Universal, always-relevant standards → root CLAUDE.md.

**Proven by A/B test:** a rule with `paths: ["week*/**/*.py"]` fired for a .py file but NOT for a .md file in the SAME folder → rules bind to file patterns, not locations.

**Exam phrasing to recognize:** "conventions must apply automatically based on file paths regardless of directory location" → `.claude/rules/` + glob frontmatter.

---

## 3. Custom slash commands & skills (TS 3.2)

**Commands:**
- File `.claude/commands/<name>.md` → invoked as `/<name>`. The FILE NAME is the command name.
- `$ARGUMENTS` placeholder receives everything typed after the command.
- Frontmatter: `description` (what it does), `argument-hint` (shown in UI when invoking — the "what do I type here" hint).
- Project scope `.claude/commands/` = shared via git (answer to "team-wide /review command" questions). Personal scope `~/.claude/commands/` = only you.
- Trap answer that doesn't exist: a `commands` array in `.claude/config.json`. Also: commands do NOT go inside CLAUDE.md.

**Skills:**
- Folder `.claude/skills/<name>/SKILL.md` with frontmatter:
  - `context: fork` → runs in an ISOLATED side context; verbose output stays there, only the summary returns. Use for noisy/exploratory skills (codebase analysis, brainstorming).
  - `allowed-tools` → hard restriction on what the skill can use. Read-only auditor: `Read, Grep, Glob`. This is a LOCK, not a request — Write absent means writing is impossible.
  - `argument-hint` → parameter prompt for invokers.
- Scoped Bash syntax: `Bash(git status:*)` = allow only that command family, not all of Bash.
- Personal variant of a team skill → put in `~/.claude/skills/` under a DIFFERENT NAME (same name would conflict/affect confusion).

**Placement decision table (asked constantly):**

| Need | Mechanism |
|---|---|
| Universal standards, every session | root CLAUDE.md |
| Folder-specific rules | directory CLAUDE.md |
| File-TYPE rules, scattered files | .claude/rules + paths |
| On-demand task/workflow | command or skill |

**Drill item (missed once!):**
- `paths` = **loading condition** (rules): controls when instructions ENTER context.
- `context: fork` = **output isolation** (skills): controls where produced OUTPUT goes.
- "Skill produces verbose output polluting the conversation" → `context: fork`, NOT paths.

**Workflow pattern:** audit → fix → re-audit. Auditor (read-only skill) finds; MAIN session fixes with your approval; auditor verifies. Same family as Domain 4 validation loops.

---

## 4. Plan mode vs direct execution (TS 3.4)

**Choose PLAN MODE when the task states:** large-scale change, 45+ files, multiple valid approaches, architectural decisions, service boundaries, library migration, "choosing between integration approaches".
**Choose DIRECT EXECUTION when:** single file, clear stack trace, well-scoped small change (one validation check, one bug fix).

**Key facts:**
- Plan mode = read-only exploration + structured plan + APPROVAL GATE. Until you approve: zero file changes (Esc/reject → `git status` clean).
- Hybrid is legitimate and guide-endorsed: plan mode to investigate/design → approve → direct execution to implement.
- `Shift+Tab` cycles modes in the CLI.
- **Explore subagent**: isolates verbose discovery output, returns summaries to protect main context; can run in PARALLEL (multiple explore agents at once). It explores — it does NOT fix.
- Good plan-mode behavior when info is missing: flag it as a **blocker + ask targeted questions** — NOT fabricate from training data, NOT silently substitute.

**The killer trap (guide sample Q5):** "Start with direct execution and switch to plan mode if complexity emerges" is WRONG when complexity is already stated in the task. **Stated complexity is an input, not a surprise.** Late discovery = expensive rework.
- Mirror trap: forcing plan mode for a trivial single-file fix is ALSO wrong (over-ceremony).

---

## 5. Iterative refinement (TS 3.5)

**Four patterns:**
1. **Concrete examples > prose.** Transformation requirements: give 2–3 input→output examples (include an invalid-input→None/edge example). Prose descriptions are interpreted inconsistently; making prose longer usually doesn't help.
2. **Test-driven iteration.** Write tests FIRST (expected behavior + edge cases), then iterate by sharing failing test output. Failing tests = objective, countable feedback ("2 tests red") vs subjective ("I don't like it"). Red → root cause → fix → green.
3. **Interview pattern.** In unfamiliar domains, have Claude ASK QUESTIONS before implementing (cache invalidation, failure modes = guide's own examples). Surfaces design decisions you didn't anticipate.
4. **Chef rule (batch vs sequential):** fixes that INTERACT → one single detailed message together. INDEPENDENT fixes → sequential. First classify: "do these issues touch each other?"
   - Example: cache key missing user ID + TTL longer than session = interacting (together); variable typo = independent (separately).

**Observed lesson:** vague prompts get filled with SILENT model assumptions (ValueError vs None contract). Tests convert hidden assumptions into visible conflicts.
- Bridge to Domain 4: sharing failing test output = retry-with-error-feedback (append the specific error to the retry prompt).

---

## 6. Claude Code in CI/CD (TS 3.6)

**CLI flags:**
- `-p` / `--print` → non-interactive mode: process prompt, print to stdout, EXIT. THE answer to "CI job hangs waiting for input" (guide sample Q10).
- Fake flags that DO NOT EXIST (classic distractors): `CLAUDE_HEADLESS=true`, `--batch`.
- `--output-format json` → machine-parseable envelope (fields incl. `result`, `structured_output`, `total_cost_usd`, `num_turns`, `session_id`).
- `--json-schema` → forces findings into YOUR schema (file/severity/issue/fix → bot can post inline PR comments). Takes INLINE JSON, not a file path: use `--json-schema "$(cat schema.json)"`.
- Free-text + regex scraping = wrong answer; enforce structure, don't scrape it.

**Independent review instance (also Domain 4 TS 4.6):**
- A session that generated code RETAINS its generation reasoning → less likely to question its own decisions. Self-review instructions and extended thinking do NOT fix this.
- Independent instance (no prior reasoning context) catches what the producer missed. Every `claude -p` call is naturally a fresh instance.
- Live proof: fresh reviewer caught a docstring-vs-code validation gap + missing convention lines that the producing session left behind.
- Meta-lesson: guidance fails SILENTLY; verification layers (auditor skill, independent reviewer, pytest, CI) catch it.

**Context & dedup principles:**
- CI-Claude gets team standards because **CLAUDE.md is committed** — cloning the repo brings the handbook. (Review criteria, test standards, fixtures → document them there.)
- Re-running review after new commits → feed PRIOR FINDINGS, ask for only new/unresolved issues (no duplicate comments).
- Test generation suggesting duplicates → feed EXISTING TEST FILES.
- One principle, two faces: **show the past to prevent repeats.**

**Real-world notes:**
- `-p` still reads local memory files (our reviewer answered in Turkish because of user-level memory!) → pin output language/format explicitly in CI prompts.
- Reviews cost money per run ($0.44 observed) → refine prompts on samples before scaling (bridge to Domain 4 batch strategy).

---

## 7. Rapid-fire trap list (last-minute review)

- "Guaranteed / must never" → hook/gate/allowed-tools, never prompt text. Temperature is never the answer.
- New teammate missing rules → user-level vs project-level.
- @import saves tokens → FALSE.
- Rules without `paths` → load unconditionally.
- `/memory` doesn't show directory CLAUDE.md / path rules at startup → normal, they're conditional.
- Mid-session config change ignored → fresh session.
- Team /review command → `.claude/commands/` in the repo. `config.json` commands array doesn't exist.
- Skill must not write → `allowed-tools` without Write (lock), not a "please don't" sentence.
- Verbose skill output → `context: fork`. Scattered file-type conventions → `paths` globs. Don't swap these.
- Stated complexity → plan mode from the start.
- Explore subagent explores and summarizes; it does not fix.
- CI hang → `-p`. Structured CI output → `--output-format json` + `--json-schema` (inline).
- Self-review is weak because reasoning context persists → independent instance.
- Duplicate review comments / duplicate test suggestions → provide prior findings / existing tests.
