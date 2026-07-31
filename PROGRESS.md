## Status
- **Current week:** Week 2 — COMPLETE ✅ (quiz: 4/6, gaps noted: explicit context passing, stale-session handling)
- **Next:** Week 3 — Tool Design & MCP (new chat: "Week 3 - MCP")

## Log
- 2026-07-22 · Week 0 done: repo, venv (Python 3.12.13), anthropic SDK, API key as env var, first API call.
- 2026-07-22 · Week 1 done: tool_use round trip, agentic loop, parallel tool calls, 5-tool order assistant, programmatic refund prerequisite, escalation handoff. Quiz done.
- 2026-07-23 · Week 2 done: Agent SDK (query/options), subagents via AgentDefinition + Task tool, context isolation proven, parallel spawn, PreToolUse refund-guard hook, sessions (resume/fork), Exercise 4 research pipeline with preserved source attribution. Quiz: pending.

## Week 3 — COMPLETE (Tool Design & MCP, Domain 2)
Files: bad_descriptions(_v2).py, good_descriptions.py, error_responses.py, forced_choice.py, order_server.py (FastMCP: 4 tools + catalog resource + $500 server-side refund gate), mcp_client_test.py, refund_e2e_test.py, edit_trap.py, .mcp.json (project scope, ${ENV} expansion), notes/week3-tool-design-mcp.md
Exercise 1 (exam guide): COMPLETE — differentiated descriptions, structured errors, business-rule gate, structured escalation handoff, multi-concern handling.
Quiz: 10/12. Drill list for week 7: any-vs-forced boundary, Grep-vs-Glob content/name distinction.
Next: Week 4 — Claude Code Configuration & Workflows (Domain 3, 20%). Open a new chat titled "Week 4 - Claude Code".

## Week 4 — IN PROGRESS (Claude Code Configuration, Domain 3)
- 2026-07-30 · Lesson 4.1 done: CLAUDE.md hierarchy (user/project/directory), @import via notes/style-guide.md, /memory diagnostics. Found a pre-existing power-user template in ~/.claude/CLAUDE.md; backed up (CLAUDE.md.backup) and trimmed — a live TS 3.1 case. Verified: directory CLAUDE.md loads on file touch (not at startup); demo_ prefix + docstring + English rules applied from three different layers in one file. Quiz: 6/6.
- Next: Lesson 4.2 — path-scoped rules (.claude/rules/ with glob frontmatter).
- 2026-07-30 · Lesson 4.2 done: path-scoped rules (.claude/rules/ + paths glob frontmatter). A/B test proved pattern-based loading (py triggered, md did not; same folder). Debugging story: rule file added mid-session was not picked up — stale session inventory, fixed by fresh session (Week 2 principle recurs). New diagnostics: /memory for startup inventory, "Loaded <file>" lines for in-session triggers. Observed rule-vs-personal-guideline conflict surfaced by Claude instead of silently resolved. Also fixed instruction-reality drift (.venv reference). Quiz: 6/6 (second in a row).
- Next: Lesson 4.3 — custom slash commands and skills (context: fork, allowed-tools, argument-hint).
- 2026-07-30 · Lesson 4.3 done: custom slash commands (.claude/commands/, $ARGUMENTS, argument-hint) and skills (SKILL.md frontmatter: context: fork, allowed-tools). Built /exam-drill command and read-only repo-audit skill; fork isolation observed live (21-file scan returned as a short summary). Audit caught pre-rule files missing EXAM TAKEAWAY; retrofit done in main session (auditor finds, main session fixes — allowed-tools as a lock). Audit → fix → re-audit loop completed. Quiz: 5/6; drill item: paths = loading condition (rules) vs context: fork = output isolation (skills).
- Next: Lesson 4.4 — plan mode vs direct execution.
- 2026-07-31 · Lesson 4.4 done: plan mode vs direct execution. Task A (single-line edit, direct: read-change-done) vs Task B (Week 7 harness design in plan mode): two parallel Explore agents, critical-finding behavior (missing 6-scenario list flagged as blocker instead of fabricated — interview pattern live), approval gate + Esc → zero file changes (git status clean). Added notes/ccarf-scenarios.md to close the gap for Week 7. Decision rule sealed: stated complexity is an input, not a surprise — start in plan mode. Quiz: 6/6.
- Next: Lesson 4.5 — iterative refinement (input/output examples, test-driven iteration, interview pattern, batch-vs-sequential fixes).
- 2026-07-31 · Lesson 4.5 done: iterative refinement. Experiment A (vague prose): silent assumptions (ValueError, E.164) disclosed only as a trailing note — guidance, not guarantee, again. Experiment B (test-first): 4 given cases + 10 edge cases, first run 8 failed/6 passed, single root cause (ValueError vs None contract), 2-line fix → 14 passed — validation-retry loop live in pytest. Experiment C (interview pattern): surfaced unanticipated design space (validation strictness, 7-digit local, special numbers, output shape). Chef rule sealed: interacting fixes together, independent fixes sequentially. Quiz: 6/6.
- Next: Lesson 4.6 — Claude Code in CI/CD (-p, --output-format json, --json-schema, independent review instance) — closes Week 4.
- 2026-07-31 · Lesson 4.6 done: headless CI reviewer (-p, --output-format json, --json-schema as inline JSON). Independent instance caught docstring-vs-code validation gap + missing EXAM TAKEAWAY lines; findings fixed via find→fix→verify loop. Quiz: 6/6.

## Week 4 — COMPLETE ✅ (Claude Code Configuration, Domain 3)
Quiz total: 35/36. Drill list for week 7: paths (rules) vs context: fork (skills).
Files: CLAUDE.md (root+week4), notes/style-guide.md, .claude/rules/python-demos.md, .claude/commands/exam-drill.md, .claude/skills/repo-audit/SKILL.md, normalize_phone.py + tests, review_schema.json, notes/ccarf-scenarios.md, notes/week4-claude-code.md
Next: Week 5 — Prompt Engineering & Structured Output (Domain 4, 20%). Open a new chat titled "Week 5 - Structured Output".
- 2026-07-31 · Lesson 5.1 done: prompt-only JSON vs forced tool_use extraction. Arm A: 3/3 json.loads failures (markdown fence), total_amount as string, currency as raw 'TL', run 3 appended prose outside the fence - same prompt, different shape. Arm B: 3/3 byte-identical, float type, enum normalized to 'TRY', comma-decimal handled via schema description. stop_reason end_turn vs tool_use. Quiz: 4/5; miss = schema fixes syntax/types, NOT semantics (line items not summing to total -> validation layer, lesson 5.4).
- Next: Lesson 5.2 - schema design against hallucination (nullable fields, enum + "other" + detail).
