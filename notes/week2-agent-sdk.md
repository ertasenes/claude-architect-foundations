# Week 2 — Claude Agent SDK & Multi-Agent Orchestration

## What was built
- `hello_agent.py` / `hello_agent_v2.py` — first SDK queries; raw message stream, then filtered output with model selection via ClaudeAgentOptions
- `first_subagent.py` — one subagent (AgentDefinition), observed the Task/Agent tool ticket carrying explicit context
- `parallel_subagents.py` — two subagents spawned in ONE coordinator response; matched tickets via tool_use_id; overlapping duration_ms proved parallelism
- `refund_guard.py` — custom tool via @tool + create_sdk_mcp_server; PreToolUse hook blocking refunds > $500 and redirecting to human escalation
- `sessions_demo.py` — 4-act proof: fresh session amnesia, resume (same id, memory intact), fork (new id, original untouched)
- `research_pipeline.py` — Exercise 4: coordinator + 2 parallel web-researchers + tool-less synthesizer; structured findings (claim/source/url/date); attribution survived synthesis

## Key concepts
- **SDK vs raw API:** SDK runs the agentic loop for you (same engine as Claude Code); raw API = full manual control. query() for one-off, ClaudeSDKClient for multi-turn.
- **Task tool = subagent spawn mechanism.** Coordinator must have Task available. (Newer CLI names it "Agent" in the stream; exam says Task.)
- **Context isolation:** subagents inherit NOTHING automatically. Context travels only inside the Task prompt — coordinator wrote "Enes" into the ticket by hand.
- **Parallel spawn:** multiple Task calls in a single coordinator response; results correlated by tool_use_id.
- **Scoped tools per agent:** synthesizer got tools=[] on purpose — agents with out-of-role tools tend to misuse them.
- **Hooks = deterministic enforcement.** PreToolUse fires after the ticket is written, before execution. Deny reason is fed back to the model so it can communicate (escalation message). Prompt = guidance (probabilistic), hook = lock (deterministic). Money/security → always the lock.
- **Sessions:** resume = continue same context; fork_session=True = branch from shared baseline; stale tool results → prefer NEW session + structured summary injection.
- **Prompt caching:** infra tokens cached ~5 min (ephemeral_5m); cache read ≈ 10x cheaper than write; any prefix change (options/tools) invalidates.

## Gotchas
- New terminal tab = venv NOT active → `source venv/bin/activate` first, or `python`/SDK imports fail.
- Pico/nano "Cannot open file for writing" = target directory missing or wrong cwd; heredoc (`cat > file << 'EOF'`) avoids editor pitfalls.
- AgentDefinition fields are camelCase (maxTurns, disallowedTools) unlike snake_case ClaudeAgentOptions.
- Coordinator may embellish the synthesizer's report during final presentation — handoff fidelity risk; pin it with "present verbatim" if fidelity matters.

## Exam hooks
- "allowedTools must include Task" / parallel = multiple Task calls in ONE response
- Sample Q7: too-narrow coordinator decomposition = root cause lives at the coordinator, not subagents
- Hook vs prompt enforcement: financial/compliance rules → programmatic (non-zero prompt failure rate)
- resume vs fork vs fresh-session-with-summary (stale context)
