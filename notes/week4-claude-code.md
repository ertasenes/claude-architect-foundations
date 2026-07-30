# Week 4 — Claude Code Configuration & Workflows (Domain 3, 20%)

## Memory hierarchy (TS 3.1)
- Layers: ~/.claude/CLAUDE.md (user, personal, NOT in version control), root/.claude CLAUDE.md (project, shared via git), subdirectory CLAUDE.md (loads when files there are touched).
- Classic exam trap: "new teammate doesn't get the rules" → rules were user-level; move to project-level.
- @import (@path/to/file): organization only — imported files still load at startup, NO token savings.
- CLAUDE.md is context, not enforcement: prompt = guidance (probabilistic), hooks/CI = lock (deterministic).
- Diagnostics: /memory (startup inventory) + "Loaded <file>" lines (in-session triggers).
- Live case: found a pre-existing power-user template in user memory distorting behavior — backed up and trimmed.

## Path-scoped rules (TS 3.3)
- .claude/rules/*.md with YAML frontmatter paths: [globs] → loads ONLY when matching files are touched → real token savings.
- No paths field → loads unconditionally.
- * = one level; ** = any depth (matched zero intermediate dirs in our test).
- A/B proof: .py in a folder triggered the rule; .md in the SAME folder did not — rules bind to file patterns, not folders.
- Debugging story: rule added mid-session was not picked up → stale session inventory; fix = fresh session.
- Config applies forward, not retroactively (21 pre-rule files needed a retrofit).

## Commands & skills (TS 3.2)
- .claude/commands/<name>.md → /name; $ARGUMENTS placeholder; argument-hint frontmatter for UX.
- Skills: .claude/skills/<name>/SKILL.md; context: fork = output isolation (verbose work in a side room, summary returns); allowed-tools = a LOCK (read-only auditor cannot write, by construction).
- Team scope (.claude/...) vs personal (~/.claude/...); personal variant of a team skill → different name.
- Placement table: universal standards → CLAUDE.md; folder rules → directory CLAUDE.md; file-type rules → paths rules; on-demand workflows → commands/skills.
- Drill: paths = loading condition (rules) vs context: fork = output isolation (skills).
- Audit → fix → re-audit loop: auditor finds, main session fixes.

## Plan mode vs direct execution (TS 3.4)
- Plan mode: large-scale, multiple valid approaches, architectural decisions, multi-file. Direct: small, clear scope, single file.
- Stated complexity is an input, not a surprise — "start direct, switch if complex" is wrong when complexity is in the task description.
- Plan mode = zero-file-change exploration; approval gate; Esc → git status clean.
- Explore subagent: isolates verbose discovery, returns summaries (fork's built-in cousin); can run in parallel.
- Observed: missing info flagged as blocker + targeted questions instead of fabrication.

## Iterative refinement (TS 3.5)
- Prose is interpreted inconsistently → 2-3 concrete input/output examples win.
- Test-first: failing output is objective feedback; red → root cause → fix → green (= validation-retry loop, pytest edition).
- Vague prompt experiment: silent assumptions (ValueError vs None contract) surfaced only when tests made them a countable conflict.
- Interview pattern: have Claude ask before implementing in unfamiliar domains.
- Chef rule: interacting fixes in ONE detailed message; independent fixes sequentially.

## CI/CD (TS 3.6)
- -p / --print: non-interactive; no such thing as CLAUDE_HEADLESS or --batch.
- --output-format json (envelope: result, cost, num_turns...) + --json-schema (inline JSON, not a file path) → machine-parseable findings.
- Independent reviewer: fresh instance carries no generation reasoning; caught a docstring-vs-code contract gap AND missing EXAM TAKEAWAY lines the producing session left behind. Guidance fails silently; verification layers catch it.
- Re-review: feed prior findings, report only new/unresolved. Test gen: feed existing tests. Same principle: show the past to prevent repeats.
- CI gets context because CLAUDE.md is committed — clone brings the handbook.
- Real-world note: -p still reads local memory files (reviewer answered in Turkish!); pin output language/format in the CI prompt. Reviewer run cost $0.44 — refine on samples before scaling.
