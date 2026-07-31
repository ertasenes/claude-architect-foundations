# 📌 Week 1 Cheat Sheet — Claude API & Agentic Loop

## 1. API Fundamentals
- Messages API: `client.messages.create(model=..., max_tokens=..., system=..., tools=..., messages=[...])`
- The `messages` list alternates between two roles: `user` and `assistant`. **The system prompt is NOT a message** — it is a separate `system` parameter.
- `max_tokens` is **required**; it caps the response length.
- The response (`response.content`) is a **list of blocks**: `text` and `tool_use` blocks can coexist in one response. Never assume "response = a single text".
- **stop_reason values:** `end_turn` (model is done), `tool_use` (model waits for tool execution), `max_tokens` (hit the cap — response is truncated!), `stop_sequence`. The first two are the heart of the exam.

## 2. Tool Definition
- Three parts: `name`, `description`, `input_schema` (JSON Schema: `type`, `properties`, `required`).
- **Description = the model's compass for tool selection.** The model picks tools by reading descriptions, not code.
- **The model NEVER executes tools.** It only writes a structured request — a "ticket". YOU take the ticket to the kitchen and run the code. On the exam, any option containing "Claude executes the tool" is automatically wrong.

## 3. The tool_use Round Trip
- `stop_reason == "tool_use"` → the response contains `ToolUseBlock(id, name, input)`.
- Returning the result:

~~~python
{"role": "user", "content": [
    {"type": "tool_result", "tool_use_id": "<ticket_id>", "content": result}
]}
~~~

- ⚠️ **BIGGEST EXAM TRAP: tool_result travels with role `user`.** Not `assistant`, and there is no `tool` role.
- The `tool_use_id` match is mandatory: it tells which result belongs to which ticket.
- The conversation chain grows each turn: `assistant(tool_use)` → `user(tool_result)` → call the API again. Tool results are appended to history so the model reasons with fresh information.

## 4. Agentic Loop — Correct Design
- Skeleton:

~~~text
loop:
  response = API call
  append assistant message to history
  if stop_reason == "end_turn": EXIT (unconditionally!)
  execute ALL tool_use blocks
  append ALL results to history in ONE user message
~~~

- **Exit is tied ONLY to stop_reason.** Our live bug: the loop exited only "if a text block exists" → a text-less end_turn response caused a **silent infinite loop**. Lesson: tie the exit to the signal, not the content.
- **The anti-pattern trio** (the exam offers these as options):
  1. Parsing natural-language signals ("does it say task complete?")
  2. Using an arbitrary iteration cap as the **primary** stop mechanism (`range(N)` as a safety net is OK, as main logic NEVER)
  3. Treating "is there a text block?" as a completion indicator
- Model-driven decisions: the **model** decides which tool to call and when, based on context; pre-coded decision trees / fixed tool sequences are the opposite of the agentic approach.

## 5. Parallel Tool Calls
- **A single assistant response can contain multiple tool_use blocks** ("check ORD-1001 and ORD-1002" → two tickets at once).
- Correct handling: **execute all of them, return ALL results in ONE user message** — each with its own `tool_use_id`.
- Wrong: executing only the first; sending each result as a separate message; rejecting the response because "one response should have one tool".
- Result order doesn't matter — ID matching does.

## 6. Guidance vs Lock ⭐ (the most important principle of the week)
- **System prompt instruction = guidance (probabilistic).** The model complies 98% of the time, but the 2% is a disaster when money/security is involved.
- **Code enforcement = lock (deterministic).** Our example: `process_refund` is **blocked in code** unless `get_customer` verified identity in this session — no matter what the model writes, it won't run.
- Exam pattern: "the rule is in the prompt but violations continue" → the correct option is always **programmatic enforcement** (prerequisite gate, hook).
- **The temperature trap:** temperature controls **randomness**, NOT rule compliance. In "how do we guarantee this?" questions, the `temperature=0` option is **always wrong**.

## 7. Escalation & Handoff
- **Structured handoff:** a structured summary is mandatory when escalating to a human — the human agent **cannot see the transcript**. Contents: customer ID + root cause + amount/what was attempted + recommended action. "Customer needs help, escalating" alone is an anti-pattern.
- **Live observation (exam item):** "I want to talk to a human" → **escalate IMMEDIATELY**, don't investigate first. (Fix: explicit escalation criteria + few-shot examples in the system prompt — Week 6 topic.)
- **The close_session pattern:** the **decision** lives in the model (it calls the close_session tool), the **enforcement** lives in code (flag + break). "Authority in the model, enforcement in code."

## 8. Rapid Trap List (60-second pre-exam review)

| Question pattern | Reflex answer |
|---|---|
| Which role carries tool_result? | **user** (never assistant / "tool") |
| When does the loop stop? | **stop_reason == "end_turn"**, unconditionally |
| Stopping via iteration cap / text checks? | Anti-pattern |
| Multiple tool_use in one response? | Normal — run all, return in ONE user message |
| Who executes tools? | Our code; the model only writes tickets |
| How to guarantee a rule? | Code/lock; prompt = probabilistic, temperature=0 = irrelevant |
| "Talk to a human"? | Escalate immediately, no questions first |
| Handoff format? | Structured summary (ID, root cause, amount, recommendation) |
