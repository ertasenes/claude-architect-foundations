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
