# Week 3 Cheat Sheet — Tool Design & MCP Integration (Domain 2, 18%)

Quick-reference before the exam. Organized by task statement, ending with trap pairs and decision rules.

---

## 1. Tool Descriptions (Task 2.1)

**Core truth: the description is the ONLY thing the model sees about a tool.** It cannot see your code, backend, or database.

The 4-part recipe for every description:
1. **Purpose** — what it does, what it returns ("shipping state, ETA, amounts")
2. **Input format** — exact shape: "customer ID in the form CUST-XXXX", "digits only, strip any leading #"
3. **Example queries** — "e.g. 'where is my package #12345?'" (cheapest form of few-shot)
4. **Boundaries + neighbor pointer** — "Do NOT use for account questions — use get_customer for those, EVEN IF the customer says 'my account'"

Symptoms of minimal descriptions (measured live):
- `auto` mode: model asks needless clarifying questions instead of acting (wasted turns)
- `any` mode: model picks the wrong tool AND fabricates inputs (we saw `'<UNKNOWN>'`)

**Misrouting between similar tools — fix ladder (exam favorite):**
1. FIRST: enrich descriptions (low effort, high leverage) ← correct "first step" answer
2. Rename tools to kill overlap (`analyze_content` → `extract_web_results`)
3. Split generic tools into purpose-specific ones (`analyze_document` → `extract_data_points` / `summarize_content` / `verify_claim_against_source`)
- Few-shot examples, routing layers, tool consolidation = wrong answers for "first step"

**Hidden trap:** keyword-sensitive SYSTEM PROMPT instructions can override good descriptions ("always understand the customer first" → model drifts to get_customer). When selection breaks, audit the system prompt too.

Field-level descriptions inside input_schema are the little sibling of tool descriptions — use both.

---

## 2. Structured Error Responses (Task 2.2)

**Generic "Operation failed" = anti-pattern.** The agent cannot choose a recovery action it cannot see.

Error envelope recipe:
```json
{"errorCategory": "transient|validation|business|permission",
 "isRetryable": true|false,
 "message": "human-readable, next-step included"}
```

| Category | Example | Correct agent reaction |
|---|---|---|
| transient | timeout, service busy | retry |
| validation | wrong input format | fix input, retry |
| business | refund limit, already shipped | NO retry; explain / escalate; include customer-friendly alternative ("offer a return instead") |
| permission | no access to record | NO retry; escalate |

**THE trap distinction — "not found" is NOT an error:**
- Access failure (timeout) → `is_error=true`, category transient
- Valid empty result ("no order with this number") → `is_error=FALSE` + `{"found": false, "message": "Query succeeded; no order exists"}`
- Mixing them = customer told to "try again later" for an order that never existed

**Information ≠ authority:** `isRetryable: true` alone does NOT make the model retry — it politely asks. Either:
- give a retry POLICY in the system prompt ("retry transient errors once without asking"), or
- better: handle transient retries IN CODE (local recovery), surface only unresolvable errors to the model
- Guide wording: "subagents implement local recovery for transient failures, propagating only errors they cannot resolve, with partial results and what was attempted"

In MCP: raising an exception inside a tool auto-sets `isError: true`. Put the structured JSON inside the exception message.

---

## 3. tool_choice — Three Gears (Task 2.3)

| Gear | Meaning | When |
|---|---|---|
| `{"type": "auto"}` | may call tools, may just talk | default, conversational agents |
| `{"type": "any"}` | MUST call some tool, model picks which | "output must be structured / a tool call, but the right tool varies" |
| `{"type": "tool", "name": "X"}` | MUST call tool X | deterministic first step (extract_metadata before anything else) |

Decision rule (two questions):
1. Is a tool call mandatory? NO → auto. YES → q2.
2. Is the SPECIFIC tool known? YES → forced. NO → any.

Critical mechanics:
- In `any`/forced turns the model CANNOT produce text blocks — pure tool_use.
- **Forcing + missing info = fabrication.** any/forced guarantee A call, not the RIGHT call.
- **Turnstile pattern:** force on the first request, then RELEASE to auto on follow-up turns — otherwise the model is obliged to call the same tool forever.
- Description-based ordering ("company policy: run FIRST") usually works but is probabilistic. Guarantee needed → forced tool_choice or hook (code lock).

---

## 4. Tool Distribution (Task 2.3)

- **4-5 tools per agent = reliable selection; 18 = degraded.** Every extra tool adds decision complexity.
- Fix is NOT deleting tools — it's distributing them by role across agents.
- **Out-of-specialization tools WILL get misused** (synthesis agent with web search will eventually search).
- **Scoped-tool exception:** high-frequency simple need (85% simple fact checks) → give a narrow tool (`verify_fact`) to the agent; complex cases (15%) keep flowing through the coordinator. Least privilege, not zero privilege.
- Replace generic tools with constrained ones: `fetch_url` → `load_document` (validates document URLs).

---

## 5. MCP Servers & Configuration (Task 2.4)

**MCP = USB-C:** write tools once behind a standard socket; every MCP client (Claude Code, Agent SDK, Desktop...) plugs in. M×N integrations → M+N.

Actors: **server** (hosts tools + resources) / **client-host** (plugs in) / at **connection time** the client discovers ALL tools of ALL configured servers simultaneously (tray crowding risk applies!).

**Scope table (classic exam question):**

| File | Scope | Who sees it | Use for |
|---|---|---|---|
| `.mcp.json` (repo root) | project | everyone who clones (travels via git) | team tooling: Jira, company DB |
| `~/.claude.json` | user | only you, all your projects | personal / experimental servers |

Decision question: "Would my teammate need this too?"

**Secrets:** `"env": {"TOKEN": "${TOKEN}"}` — env variable EXPANSION. File is committed; real value lives in each developer's environment. Never commit plaintext tokens, even in private repos.

**Tools vs Resources:**
- Tool = ACTION ("do") — lookup, cancel, refund
- Resource = readable CATALOG ("read") — `orders://catalog`
- Purpose: give agents visibility into available data WITHOUT exploratory tool calls
- In Claude Code, resources attach via `@server:uri`

**Community vs custom:** standard integration (Jira, GitHub) → existing community server. Custom servers ONLY for team-specific workflows. "Write your own Jira server" is a wrong answer.

Also remember:
- Tool naming from client side: `mcp__<server>__<tool>`
- Enhance MCP tool descriptions or the agent may prefer built-ins (Grep) over your more capable MCP tool
- Claude Code asks for approval before trusting a project .mcp.json (it runs commands on your machine)

---

## 6. Built-in Tools (Task 2.5)

| Question shape | Tool |
|---|---|
| "which files CONTAIN X / who CALLS X / where is this error message" | **Grep** (content) |
| "files NAMED like `**/*.test.tsx`" | **Glob** (path pattern) |
| load a full file | **Read** |
| write/overwrite a full file | **Write** |
| targeted change via unique text match | **Edit** |
| RUN things: tests, git, scripts, installs | **Bash** |

**Grep vs Glob litmus test:** is the thing searched in the file's NAME or its CONTENTS? Contents → Grep, always. Trap format: the wrong option shows a plausible-looking glob like `**/*payment*` for a "who calls processPayment" question.

**Edit's Achilles heel:** old_string must be UNIQUE in the file.
- Fails with "matches multiple locations" → fix ladder:
  1. widen the anchor (include neighboring lines that make it unique — e.g. anchor on `return total * 0.1`)
  2. guaranteed fallback: **Read + Write** (guide's canonical answer)
- Why Edit first anyway: Write rewrites the whole file → more tokens + risk of accidental changes elsewhere. Edit is surgery, Write is transplant.

**Bash trap:** "works but wrong" — `ls`/`find` can list files, but the exam's correct answer for find/read/write jobs is the special-purpose tool (safety surface, portability, structured output). Bash's legitimate zone = "do" verbs.

**Exploration strategy:** incremental, never read-everything-upfront. Grep entry points → Read that file → follow imports. Wrapper-module tracing: list exported names first, then Grep each name across the codebase.

---

## 7. Defense in Depth (cross-cutting, exam loves it)

Three layers for one business rule ($500 refund limit):
1. **Description warning** ("above 500 USD not permitted — use escalate_to_human") → cheap pre-check; the model may skip the doomed call entirely (observed live)
2. **Client-side hook** (PreToolUse) → blocks the call before it leaves
3. **Server-side raise** (business error) → last line of defense; holds even for clients without hooks

Rule of thumb: description/prompt = lowers probability; code lock = impossibility. "We wrote it in the description, can we remove the code check?" → always NO.

Escalation handoff structure (the human has NO conversation access):
`customer_summary` (who/order/amounts) + `root_cause` (why the agent can't resolve) + `recommended_action` (what the human should do).

---

## 8. Trap Pairs — drill these
- **any vs forced** (tool required, WHICH varies → any)
- **Grep vs Glob** (contents vs names)
- **transient vs business** (retry vs never-retry)
- **error vs valid empty result** (is_error true vs false)
- **project vs user scope** (.mcp.json vs ~/.claude.json)
- **tool vs resource** (do vs read)
- **description warning vs code lock** (probability vs guarantee)
- **Edit vs Read+Write** (surgery vs guaranteed fallback)

## 9. Live-observed gotchas (not in the guide, but real)
- Summarization can inject inference (20min ×2 → "40 minutes") — handoff fidelity
- Agents may recommend options your system doesn't offer — constrain suggestions to tool outputs
- Stale snapshots: if a tool mutates state, keep resources/catalogs consistent; agents will (rightly) flag the conflict instead of resolving it
- macOS: `sed -i ''` (BSD), venv provides `python`, ANTHROPIC_API_KEY overrides claude.ai login
