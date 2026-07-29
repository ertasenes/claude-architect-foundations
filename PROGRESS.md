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
