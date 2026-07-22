# Week 1 — Claude API, Tool Use & the Agentic Loop

## What was built
- `first_tool.py` — first tool definition, observed a raw tool_use block
- `single_round_trip.py` — one full round trip: tool_use → run tool → tool_result → final answer
- `agentic_loop.py` — while-loop agent; observed parallel tool calls (2 tickets in 1 response)
- `order_assistant.py` — 5-tool support agent (get_customer, lookup_order, process_refund, escalate_to_human, close_session), interactive chat

## Key concepts
- **Tools:** Claude never executes tools. It writes a structured request (a "ticket"); OUR code executes and returns the result.
- **stop_reason drives everything:** loop continues while "tool_use", exits on "end_turn". Anti-patterns: arbitrary iteration caps, parsing text for completion keywords, exiting only when a text block exists.
- **Conversation chain:** each turn appends assistant(tool_use) then user(tool_result). tool_result travels with role "user" and must reference tool_use_id.
- **Parallel tool calls:** one response can contain multiple tool_use blocks; collect all results into a single user message.
- **Programmatic prerequisite:** process_refund is BLOCKED in code unless get_customer verified identity this session. Prompt = guidance (probabilistic), code = lock (deterministic). For money/security, rely on the lock.
- **Structured handoff:** escalate_to_human requires a summary (customer ID, issue, what was attempted, recommended action) because the human cannot see the transcript.
- **Session close pattern:** the model decides (close_session tool), our code executes (flag + break). Authority in the model, enforcement in code.

## Bug found & fixed
`run_agent` originally returned only if a text block existed on end_turn → silent infinite loop risk when a response has no text. Fix: exit unconditionally on end_turn (`return ""` fallback). Rule: tie loop exit ONLY to stop_reason, never to content.

## Exam-relevant observation
On "I want to talk to a human right now", the agent asked for context before escalating. Guide's rule: escalate IMMEDIATELY on explicit request. Production fix: explicit escalation criteria + few-shot examples in the system prompt (Week 6 topic).
