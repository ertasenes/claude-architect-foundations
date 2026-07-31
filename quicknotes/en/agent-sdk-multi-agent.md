# 📌 Week 2 Cheat Sheet — Agent SDK & Multi-Agent Orchestration

## 1. What is the Agent SDK? (vs the raw API)
- **Raw API (Week 1):** YOU write the agentic loop — full control, one-off calls.
- **Agent SDK:** the SDK runs the same loop; it's literally Claude Code's engine. Built-in tool arsenal (Read, Write, Bash, Grep, Glob, WebSearch, **Task**), hooks, sessions, subagent orchestration out of the box.
- **`query()` vs `ClaudeSDKClient`:** query() = a NEW session per call, for one-off tasks. ClaudeSDKClient = multi-turn conversation in the same session, interrupt support. Exam pattern: "one-off task" → query(), "continuing conversation" → client.
- The SDK is **async**: `async def` (define), `await` (wait without blocking), `asyncio.run(main())` (entry point), `async for` (catch streamed messages one by one).
- Message stream types: `SystemMessage(init)` (hardware list: tools, agents, model), `AssistantMessage` (content blocks), `UserMessage` (tool_results return here — the Week 1 rule lives on!), `ResultMessage` (summary: stop_reason, num_turns, total_cost_usd, session_id).

## 2. Subagents — Hub-and-Spoke (Head Chef & Stations)
- **Architecture:** the coordinator (hub) manages all communication, error handling, and information routing; subagents (spokes) NEVER talk to each other directly. Orchestration stays central.
- **Task tool = the spawn mechanism.** Invoking a subagent is an ordinary tool call (a ticket!). If the coordinator has no access to the Task tool, spawning is PHYSICALLY impossible. Exam line: *"allowedTools must include 'Task'."*
- (Field note: newer CLIs may show this tool as `Agent` in the stream — same mechanism; on the exam it's **Task**.)
- **Definition:**

~~~python
subagents = {
    "web-researcher": AgentDefinition(
        description="When to give me work - the COORDINATOR reads this to choose",
        prompt="The subagent's own system prompt (its identity)",
        tools=["WebSearch"],   # [] = no tools; if OMITTED it inherits ALL tools!
        model="haiku",         # each station can run a different engine
    ),
}
options = ClaudeAgentOptions(model="claude-sonnet-4-6", agents=subagents, allowed_tools=["Task"])
~~~

- ⚠️ **AgentDefinition fields are camelCase** (`maxTurns`, `disallowedTools`, `permissionMode`) — ClaudeAgentOptions is snake_case (`max_turns`). Mixing them raises TypeError.
- **The coordinator picks stations by reading `description`** — the tool-description-quality principle, at the agent level.

## 3. Context Isolation ⭐ (the exam's favorite fact)
- **A subagent does NOT automatically inherit the parent's conversation history.** It is born into an isolated context; its universe is the `prompt` field of the Task ticket.
- Context travels ONE way: **the coordinator writes it into the ticket by hand.** (Our live proof: the name "Enes" reached the subagent only because the coordinator wrote it into the Task prompt.)
- Symptom matching (exam tactic): output **completely unrelated** → context wasn't written into the ticket. Output relevant but **messy** → format/schema problem.
- Advanced: writing it isn't enough, **structure** must survive → use a **structured format** separating content from metadata (source URL, document name, date); synthesis must preserve claim-source mappings. A flat text blob = attribution dies.

## 4. Parallel Spawn
- Definition: the coordinator emits **multiple Task tool calls in a SINGLE response.** (NOT threads/subprocesses — that breaks hub-and-spoke.)
- Results are correlated via `tool_use_id` (ticket tracking number). Returns arrive as `ToolResultBlock`s inside `UserMessage`s.
- Evidence markers: two SPAWNs back-to-back (no RETURN in between) = parallel; overlapping duration_ms → total wait ≈ the slowest one.
- `parent_tool_use_id`: tells who is speaking — None = coordinator, set = the subagent born from that ticket.

## 5. Scoped Tools (role-based tool restriction)
- Principle: **each agent gets only the tools its role requires.** An agent holding out-of-role tools tends to MISUSE them (classic: a synthesis agent doing its own web searches and adding unverified content).
- Fix ranking: writing "never search" in the prompt = a request (probabilistic). `tools=[]` = a lock (deterministic). **It cannot misuse what it cannot do.**
- Too many tools is also poison: giving one agent 15-18 tools degrades selection reliability. Ideal: 4-5 per role.
- For high-frequency simple needs, a **scoped cross-role tool** is acceptable (e.g., a narrow verify_fact for synthesis); complex cases route through the coordinator.

## 6. Hooks — The Food Inspector in the Kitchen ⭐
- A hook = an official interception point in the SDK loop; **it lives in code, the model cannot talk its way past it.** Prompt = guidance (probabilistic), hook = lock (deterministic). Money/security/compliance → ALWAYS the lock.
- **PreToolUse:** fires AFTER the ticket is written, BEFORE execution. Use: block policy violations (e.g., refund > $500 → deny + human escalation).
- **PostToolUse:** the tool ran; fires BEFORE the result reaches the model. Use: normalize heterogeneous data (Unix timestamp / ISO 8601 / "07/23/2026" chaos → one format).
- Pre/Post decision logic: "must never happen" → Pre (prevention); "let it happen but fix it" → Post (transformation). Reversing money with PostToolUse = remediation, NOT prevention — a wrong option on the exam.
- Registration and return shapes:

~~~python
async def refund_guard(input_data, tool_use_id, context):
    amount = input_data["tool_input"].get("amount", 0)
    if amount > 500:
        return {"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Policy: >$500 needs a human. Tell the customer it's escalated.",
        }}
    return {}  # empty dict = no objection, proceed

options = ClaudeAgentOptions(hooks={
    "PreToolUse": [HookMatcher(matcher="mcp__support__process_refund", hooks=[refund_guard])],
})
~~~

- **The deny reason is FED BACK to the model** → it learns why it was blocked and writes a proper escalation message. Lock in code, communication in the model.
- Defining your own tool (Week 3 preview): `@tool("name", "description", {"param": type})` + `create_sdk_mcp_server(name="support", tools=[...])`. The tool name becomes three-part: **`mcp__<server>__<tool>`**.

## 7. Sessions — resume / fork / fresh start ⭐
- Every query() opens a new session; the SDK persists conversations to disk (`session_id`).
- **Decision tree (memorize):**
  - Context VALID + continue where you left off → **resume** (`resume=sid`; CLI: `--resume`). Same session_id comes back, memory intact.
  - Context VALID + exploring DIVERGENT directions from the same baseline → **fork** (`resume=sid, fork_session=True`). NEW session_id; the original stays untouched. Use: comparing two strategies independently (don't discuss both in one conversation — the first contaminates the second).
  - Context STALE (files changed, tool results outdated) → **neither resume nor fork**: NEW session + inject a structured summary into the first prompt. Don't trust stale tool results; a "be careful" warning doesn't fix it.
  - Scale nuance: if only a few specific files changed, resume + "re-analyze these files" is defensible; a large refactor (30+ files) → fresh start.
- Persistent memory (CLAUDE.md, memory) is a SEPARATE mechanism from session history (Week 4 topic).

## 8. Coordinator Design
- Write **goals + quality criteria** into the prompt, NOT a step-by-step recipe. A fixed pipeline ("always search→analysis→synthesis") = waste on simple queries, rigidity on complex ones. Correct: the coordinator analyzes the query and decides **dynamically** which subagents are needed.
- **Too-narrow decomposition risk:** if the coordinator slices the topic too thin, coverage gets holes (example: "creative industries" → only visual arts). Root cause lives at the coordinator, not the subagents (sample exam Q7).
- Distributing decision authority to subagents is also wrong — orchestration stays central.
- **Handoff fidelity:** the coordinator may embellish the synthesis output during final presentation → unverified-addition risk. If fidelity matters, add a "present the report VERBATIM" rule.
- Structured findings format: each finding = claim + source_title + source_url + publication_date. Dates must travel so temporal differences aren't mistaken for contradictions (Week 6 provenance foundation).

## 9. Cost & Prompt Caching (exam won't ask details; "it exists and what it does" is enough)
- Agent infrastructure (system prompt + tool definitions, ~19K tokens) is WRITTEN to cache on the first call (`ephemeral_5m` = 5-min lifetime). Write ≈ 1.25x, read ≈ 0.1x normal price → a repeat within 5 min ≈ 10x cheaper.
- If ANY part of the prefix changes (options, tools, model), the cache misses.
- Architect reflex: the expensive model coordinates (sonnet), cheap models do the legwork (haiku).

## 10. Rapid Trap List (60-second review)

| Question pattern | Reflex answer |
|---|---|
| How are subagents spawned? | Via the **Task tool**; the coordinator MUST have Task access |
| Coordinator never spawns? | Mechanical layer FIRST: is the Task tool available? (description quality comes second) |
| Does a subagent know the parent context? | NO — only what's written into the Task prompt |
| How to parallelize subagents? | Multiple Task calls in ONE response (not threads!) |
| Synthesis doing its own searches? | Restrict its tool set (tools=[]) — a prompt request isn't enough |
| Operations over $X must never run? | Block with a **PreToolUse hook** + escalate (reversing via PostToolUse = wrong) |
| Mixed date/data formats confusing the agent? | Normalize with a **PostToolUse hook** before results reach the model |
| Continue / branch / stale context? | resume / fork_session=True / NEW session + summary injection |
| Fixed pipeline or dynamic selection? | Dynamic: the coordinator picks subagents per query |
| Report with lost/mismatched sources? | Structured claim-source mapping; separate content from metadata |
