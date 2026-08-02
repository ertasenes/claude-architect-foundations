# Week 6 - Context Management & Reliability (Domain 5, 15%)

## Lesson 6.1 - Preserving critical information across long interactions (TS 5.1)

### The core problem
Summarization preserves narrative and drops the transactional layer: amounts,
dates, ids and customer-stated expectations. The fix is not "summarize better"
but "keep a layer that is never summarized".

### Experiment 1 - case_facts.py
Arm A (4-sentence summary only): 5/6 facts present. Lost `purchase_date`.
Arm B (schema-extracted CASE FACTS block + same summary): 6/6.
The scored miss understated the real damage: Arm A reduced the customer's
stated reason to "card statement closes", dropping "I don't want to pay
interest on the full amount" - the part that determines how the agent should
prioritize and what it owes the customer if the refund is late.
Arm A said NOT IN CONTEXT rather than inventing a date - but only because the
system prompt demanded it. Without that instruction, a required field plus a
missing value produces fabrication (Week 5 lesson).

### Experiment 2 - progressive_loss.py
Three generations of summary-of-summary, tracking 11 facts.
Adjusted for facts that existed at each generation: 6/8, 8/9, 9/11.
Two laws observed:
1. Summary loss is IRREVERSIBLE. `purchase_date` died in generation 1 and no
   later generation recovered it, because later generations read the previous
   summary, not the transcript. Improving the summarizer cannot recover data
   that already left the pipeline.
2. What gets dropped is CATEGORICAL, not random. The same two items died every
   generation: (a) a date that is worthless to the narrative but required for
   business logic (warranty window, 60-day rule, carrier damage claim), and
   (b) the customer's own reason for a deadline.
The facts layer, re-extracted from full history, held everything.

Measurement artifact worth remembering: the scorer reported "LOST: refund
amount" for the facts layer, but the value was there as `86.5` while the
expected string was `86.50`. A float ate the trailing zero. Schema compliance
does not guarantee semantic fidelity - money belongs in a string ("86.50") or
integer cents (8650), not a float. The metric hid a success here and hid a real
loss (the "interest" clause) earlier: the same blind spot that makes aggregate
accuracy numbers untrustworthy (see TS 5.5).

### Experiment 3 - lost_in_middle.py - NEGATIVE RESULT
12 findings, ~47k chars, statistic buried in filler, 3 runs per arm.
Arm A (flat) 36/36. Arm B (index first + section headers) 36/36.
No position effect appeared. Two reasons: the input filled only ~6% of the
context window, and the task was RETRIEVAL, whereas the guide's wording is
"may omit findings from middle sections" - the failure mode belongs to
SYNTHESIS output, where a section is read but excluded from the conclusion.
Exam answer is unchanged: put a key-findings summary FIRST, separate detail
with explicit section headers. "Use a model with a bigger context window" is
still wrong - window size does not fix attention quality.

### Experiment 4 - trim_tool_output.py
A 40-field order record vs the 6 fields a returns conversation needs.
Per record: 1179 chars -> 186 chars (84% smaller).
Across a 4-turn conversation: 11,380 -> 6,876 input tokens (40% saved). The
gap widens with turn count, because every tool_result is re-sent on every
subsequent request.

Two effects beyond token count:
- Arm A told the customer "Order A-41055 has status code 2". The 1..4 -> label
  map existed nowhere in context. On the next turn it guessed "status code 4
  (which indicates it was returned)" - correct, but arrived at by reading the
  customer's question, not the data. Arm B said "shipped" and "returned"
  because normalization happened before the model saw the record.
- Arm A volunteered tax ($77.22) and order totals nobody asked for. Fields
  present in context are treated as relevant. Trimming improves signal-to-noise,
  not just cost.

In the Agent SDK this projection function is a PostToolUse hook. Trimming must
happen BEFORE the result enters context; summarizing it afterwards is the
irreversible-loss path from experiment 2.

Own-goal worth keeping: the first version of the normalizer emitted
`purchase_date: 2025-06-26` from a hand-written epoch that was simply wrong.
Nothing complained, because no turn asked for the date. A trimming/normalizing
layer is code that needs tests, not a pass-through.

### Exam rules from this lesson
- Facts that must survive go in a persistent block outside summarized history,
  re-sent verbatim on every request. Multi-issue sessions get one row per issue.
- Summary loss is irreversible; fix the pipeline, do not retry the summarizer.
- Money as float loses precision that matters. Strings or integer cents.
- Lost-in-the-middle mitigation = key summary first + explicit section headers.
  Bigger context window is the decoy.
- Verbose tool output is trimmed before entering context, via PostToolUse hook.
- Format normalization (epoch / ISO / numeric status codes) belongs in the hook,
  not in a system-prompt instruction telling the model to convert.
- The API is stateless: full conversation history is re-sent every request.
