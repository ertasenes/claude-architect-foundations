# Week 3 — Tool Design & MCP Integration (Domain 2)

## What was built
- `bad_descriptions.py` / `bad_descriptions_v2.py` — measured tool selection with minimal descriptions; auto arm asked needless questions, any arm picked wrong tool 4/5 and fabricated identifier '<UNKNOWN>'
- `good_descriptions.py` — rich descriptions (purpose + input format + example queries + boundaries pointing to neighbor tool): 5/5 correct tool, clean input, '#' stripped per description
- `error_responses.py` — STRUCTURED flag experiment: generic "Operation failed" killed recovery; errorCategory/isRetryable + system-prompt retry policy produced silent retry and correct per-order answers; "not found" returned as is_error=false valid empty result
- `forced_choice.py` — third tool_choice gear: forced extract_metadata first, then RELEASED constraint to auto (turnstile pattern); forced/any turns produce no text blocks
- `order_server.py` — standalone FastMCP server: lookup/cancel/refund/escalate tools + orders://catalog resource; server-side $500 refund gate as business error; cancel now mutates status (stale-snapshot fix)
- `mcp_client_test.py` / `refund_e2e_test.py` — same server consumed by Agent SDK and Claude Code with zero server changes (USB-C promise); e2e run: lookup -> skipped refund (read the limit from description) -> structured escalation handoff
- `edit_trap.py` — two byte-identical lines; Claude Code read first, anchored old_string on `return total * 0.1`, Edit succeeded first try
- `.mcp.json` — project-scoped server config with ${ORDER_API_TOKEN} env expansion, committed to git

## Key concepts
- **Descriptions are the model's only window into a tool.** Recipe: purpose + input format + example queries + boundary pointing at the neighbor ("Do NOT use for X — use tool_y"). First fix for misrouting is richer descriptions, not few-shot / routing layers / consolidation.
- **any/forced guarantee A tool call, not the RIGHT call.** Forcing + missing info = fabrication. Decision rule: tool mandatory? -> is the specific tool known? yes: forced, no: any. Release forced after first pass.
- **Structured errors:** errorCategory (transient/validation/business/permission) + isRetryable + human-readable message. "Not found" is NOT an error: is_error=false + found:false (valid empty result). Info != authority: isRetryable alone doesn't trigger retry — give a policy (prompt) or handle transient retries in code (local recovery, propagate only what you can't resolve).
- **Description = lowers probability of bad calls; code lock = makes them impossible.** Keep both (defense in depth): agent read the $500 limit from the description and skipped the doomed call, but the server-side raise stays as the last line of defense.
- **MCP:** tools = actions, resources = readable catalogs (cut exploratory calls). .mcp.json (project, shared via git, ${ENV} for secrets) vs ~/.claude.json (user/personal). All connected servers' tools are discovered simultaneously. Community servers for standard integrations; custom only for team-specific workflows.
- **Built-ins:** Grep = content ("who calls X"), Glob = file-name patterns, Edit needs a UNIQUE old_string (fallback: widen anchor, or Read + Write), Bash = "do" verbs (tests/git), not find/read/write. Incremental exploration: Grep entry points -> Read -> follow imports.

## Quiz result
10/12. Misses: any-vs-forced boundary (tool required but WHICH tool varies -> any), and the Grep/Glob trap (searching file CONTENTS -> Grep; plausible-looking glob pattern was the bait). Pattern: strong on concept families, drill the intra-pair distinctions (any/forced, Grep/Glob, resource/tool, project/user scope) in week 7.

## Live observations worth remembering
- Model decomposed a two-concern message and acted on one while asking format-correct question about the other (rich descriptions enabled it)
- Summarization can inject inference (20min x2 -> "40 minutes") — handoff fidelity family
- Agent flagged catalog-vs-tool-result inconsistency (stale snapshot) instead of resolving it silently — Task 5.6 behavior observed in the wild
- Recommendation loyalty gap: agent suggested return options our system doesn't have; constrain suggestions to tool outputs via system prompt
- Environment gotchas: BSD sed needs -i '', venv provides the `python` command, ANTHROPIC_API_KEY overrides claude.ai login
