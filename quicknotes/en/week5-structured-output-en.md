# Week 5 — Cheat Sheet: Prompt Engineering & Structured Output
**Domain 4 · 20% of the exam · Task Statements 4.1–4.6**

---

## 0. THE RELIABILITY PYRAMID (frame for everything)

| # | Layer | What it does | What it does NOT do |
|---|---|---|---|
| 1 | **Schema** (tool_use + input_schema) | **Guarantees** syntax and types | Does not check meaning |
| 2 | **Schema design** (nullable, enum+other) | **Reduces** fabrication pressure | Guarantees nothing |
| 3 | **Few-shot** | **Fixes** judgment on ambiguous cases | Cannot create absent info |
| 4 | **Validation** (Pydantic) | **Catches** semantic errors | Does not repair them |
| 5 | **Retry** | **Repairs** format/structural errors | Cannot fix absence or contradiction |
| 6 | **Human review** | **Decides** on what cannot be repaired | — |

> Exam items usually ask which layer owns a given failure. Picking the wrong layer is the most common mistake.

**Failure → owning layer:**
- Malformed JSON / missing field / wrong type → **Schema**
- Field absent from the source filled with a plausible value → **Schema design (nullable)**
- Inconsistent decisions on ambiguous documents → **Few-shot**
- Line items don't sum / value in the wrong field → **Validation + human**
- Date arrives in the wrong format → **Retry**
- Source contradicts itself → **Flag the conflict + human** (never retry)

---

## 1. TS 4.3 — Structured output via tool_use

### Mechanics
- Define the target shape as a tool's `input_schema` → force it with `tool_choice` → read the data from `tool_use.input`.
- **The tool is never executed.** It is a pre-printed form; the filled form IS the data.
- Asking for JSON in the prompt = **guidance (probabilistic)**. Schema = **lock (deterministic)**.
- Access blocks **by type**: `next(b for b in resp.content if b.type == "tool_use")`. `content[0]` is **wrong** — the model may emit a thinking/text block first.
- `stop_reason`: prompt-only → `end_turn`; forced tool → `tool_use`.

### Anti-pattern
- **Scraping** markdown fences / preambles with string operations. One day the note lands outside the fence, then before it, then as two blocks. **Force the structure; do not clean it up afterwards.**

### tool_choice, three gears (Week 3 recall — exam trap)
| Mode | Meaning | When |
|---|---|---|
| `"auto"` | Model may or may not call a tool | No structured-output guarantee needed |
| `"any"` | A tool call is **required**, the **model picks which** | Multiple schemas, document type **unknown** |
| `{"type":"tool","name":"X"}` | A **specific** tool is required | Single schema; or one tool must run first (e.g. `extract_metadata` before enrichment) |

- **Decision sentence:** *tool required but which one varies → `any`. Specific tool required → forced.*
- Leaving forced on across turns → the model loops indefinitely. Pattern: **force on turn one, then release to `auto` (turnstile).**
- Forcing increases fabrication risk (the model has no exit other than calling the tool).

### What a schema DOES and DOES NOT guarantee
- ✅ Valid JSON, correct types, presence of required keys
- ❌ **Semantic correctness:** line items not summing to total, values placed in the wrong field, nonsensical dates
- `1250.00` is a perfectly valid `number` — it is just the **wrong** number.
- **Changing the type does not fix semantics** (`number` → `integer` is the classic wrong option).

### Schema descriptions = the interpretation layer
- Schema enforces **shape**; `description` steers **interpretation**.
- Put normalization rules in descriptions: `1.250,00 → 1250.00`, ISO 8601 `YYYY-MM-DD`, ISO 4217 currency codes.
- Guide skill: *format normalization rules in prompts alongside strict output schemas.*

### Real-world note (beyond the guide, worth knowing)
- The API now has **structured outputs**: `output_config.format` (JSON outputs) and `strict: true` on tool definitions (guaranteed tool inputs). It **compiles the schema into a grammar** and constrains token generation.
- Limits: 20 strict tools, 24 optional parameters, 16 union-typed parameters per request. Grammars are cached for 24h.
- Enum **capitalization is not guaranteed** → compare case-insensitively; avoid enum values differing only in case.
- With `stop_reason: "refusal"` or `"max_tokens"`, the output may not match the schema.
- **The exam answer remains tool_use + JSON schema.**

---

## 2. TS 4.3 (cont.) — Designing schemas against hallucination

### What `required` actually means
- `required` = **the key must be present**. It does **not** mean the value must be non-null.
- `["string","null"]` + `required` is a **valid and useful** combination: `{"due_date": null}` is valid, `{}` is not.
- Benefit: downstream code can write `data["x"]` (no KeyError) **and** "field never arrived" stays distinguishable from "arrived but empty".

### Nullable = an escape hatch
- With no escape hatch the model **must** fabricate. Fabrication comes not from the model's character but from **the only option the schema left open**.
- Nullable + explicit instruction: *"return null if the document does not state it; never estimate; never reuse issue_date."*
- Nullable costs nothing **when the data exists** (no quality loss).
- **Do not overdo it:** union types are grammar-expensive. Only fields that may **genuinely** be absent from the source should be nullable.

### enum + "other" + detail
- A closed enum forces real-world values **into the nearest wrong slot** → information destroyed.
- Correct pattern: `enum: [..., "other"]` **plus** a nullable `*_detail` string holding the verbatim wording.
- Growing the enum forever is **not** a fix (treadmill). Removing the enum entirely is **not** a fix either (categorization dies).
- **"other" needs a usage criterion**, or it becomes a dumping ground: *"use 'other' ONLY when no listed category matches the document's function — not merely because the heading uses different wording."*

### Live experimental evidence
| Document | Strict schema (v1) | Safe schema (v2) | Error class |
|---|---|---|---|
| Complete | ✅ | ✅ | — |
| No due date | ❌ **copied the issue date into due_date** | ✅ `null` | Value in wrong field (**silent semantic**) |
| Unlisted payment method ("Papara") | ❌ `bank_transfer` | ✅ `other` + verbatim detail | Information loss (**silent category**) |

> Both failures are **silent**: no error, no warning, fully schema-compliant. On the exam, "plausible but wrong values, no errors raised" = look at schema design.

---

## 3. TS 4.2 — Few-shot prompting

### What it fixes / does not fix
| Problem | Few-shot? |
|---|---|
| Inconsistent decisions on ambiguous cases | ✅ |
| Structural variety (inline citations vs bibliographies) | ✅ |
| False positives / acceptable patterns flagged as issues | ✅ |
| Output format inconsistency (free-text fields) | ✅ |
| Malformed JSON / schema compliance | ❌ → **Schema** |
| Information absent from the source | ❌ → **Nullable** |

### Rules
- **2–4 examples.** Increase the **kinds of ambiguity covered**, not the count. 25 examples is the wrong instinct.
- Examples must carry the **reasoning**: why this call, why not the plausible alternative. That is what makes the model **generalize** instead of memorize.
- State the decision **rule** up front: *"Decide on payment obligation, not on the title."*
- Few-shot is the fix for a **measured inconsistency**, not a default first move. (Week 3 ordering: **improve tool descriptions first**, then few-shot.)
- For varied source structures: instead of writing brittle pre-processing code, **show correct extraction from both structures**.

### Live experimental evidence
- On documents with strong signals (the document itself says "creates no payment obligation"): prose == few-shot, **no difference**.
- The gap opened on the borderline case: a receipt titled "PAYMENT NOTICE" → prose chose `"other"` 2/2 while **its own reasoning** stated "money collected + zero balance". The model read enum values as **name labels**, not **semantic categories**. Few-shot chose `"receipt"` 2/2, generalizing the rule from a **differently-titled** example.
- Side effect: few-shot also **tightened the wording** of free-text fields (format consistency).

> **Recurring principle:** prompt-layer improvements (few-shot, explicit criteria) win **under ambiguity**. When the signal is obvious, a simple prompt suffices.

---

## 4. TS 4.1 — Explicit criteria and false-positive reduction

### The core distinction
- ❌ **A stance:** "be conservative", "only report high-confidence findings", "avoid nitpicking"
- ✅ **A specification:** a categorical **REPORT list** plus a categorical **SKIP list**

**Why a stance fails:** the system is currently **confident about its wrong findings**. A high FP rate *is* miscalibration. You cannot use a broken calibration as a filter.

### Writing criteria
- REPORT: testable conditions. Example: *"flag a comment only when the claimed behaviour contradicts the actual code behaviour"* (≠ "check that comments are accurate").
- The SKIP list matters **as much as** REPORT: style, naming, formatting, constants clear from context, type hints, non-hot-path performance, library/idiom preferences.
- **Severity needs concrete definitions plus code examples**: `critical` = exploitable or data-corrupting; `major` = wrong results or crash on realistic input; `minor` = correct but fragile.
- Undefined severity → the same code graded differently across runs → **the "critical" label loses meaning**, and a merge policy built on it becomes a dice roll.

### The `detected_pattern` field
- Records the **code construct** that triggered the finding (`"f-string in SQL"`, `"unguarded list index"`).
- Purpose: when developers dismiss findings, **count which pattern** systematically produces false positives.
- "3 findings dismissed" is useless; "80% of dismissals come from this pattern" is actionable.
- Without a criteria list the model **invents different wording each run** → ungroupable → analysis impossible.

### Trust erosion
- High-FP categories **destroy confidence in the accurate categories too**. If 30 of 40 items are noise, the real SQL injection at item 31 gets skipped as well.
- Guide skill: **temporarily disable the high-FP category**, improve its prompt, then re-enable it.
- A tool that contradicts itself (complains sometimes, stays silent other times) is **worse than** a single wrong finding.

### Live experimental evidence (borderline patterns, 3 runs each)
| | Vague ("be conservative") | Categorical criteria |
|---|---|---|
| Findings per run | 3 / 2 / 3 (**unstable**) | 3 / 3 / 3 (**stable**) |
| Control (SQL injection) | 3/3 ✅ | 3/3 ✅ |
| Unstable finding | yes (2/3, at **two different severities**) | none |
| Silent data corruption (`return 0.0`) | **missed 0/3** ❌ | caught 3/3 ✅ |

> **Biggest finding:** explicit criteria do not merely filter noise — they **direct where the model looks**. A criteria list is not censorship, it is a **search plan**. Recall rose **together with** precision.
> Note: on unambiguous defects both arms were **equal** — the difference is born in ambiguity.

---

## 5. TS 4.4 — Validation, retry, and feedback loops

### Two kinds of Pydantic validator
- `@field_validator` → **a single field** (slug format, length, character set)
- `@model_validator(mode="after")` → **cross-field** (line items sum == total, `due_date > issue_date`)
- **Semantic validation lives here** — the rule class JSON Schema cannot express.
- Rejecting `due_date <= issue_date` **catches red-handed** the "no due date found, so I copied the issue date" failure.

### Feedback mechanics
- Send back: **the original document + the failed extraction + the SPECIFIC validation errors**.
- ❌ "extraction failed, try again" (not specific) · ❌ starting a fresh session from scratch · ❌ putting the error in the system prompt
- The error text goes back **as a `tool_result`**, carried with **`role: "user"`** (the Week 1 trap, doing real work here). From the model's view, the tool is saying "your input was invalid".

### THE THREE-COLUMN TEST (the week's most critical distinction)
| Situation | Retry? | Correct behaviour |
|---|---|---|
| Information **present**, malformed (`"15/03/2026"`, `"<UNKNOWN>"`) | ✅ **YES** | Retry with the specific error |
| Information **absent** (clause not in the document; referenced attachment not provided) | ❌ **NO** | Nullable + policy default |
| Information **present but self-contradictory** | ❌ **NO** | Flag the conflict → human |

> **One question:** "Does the model have the information, or is only its shape wrong?"

### Live evidence — retry applied to the wrong error class
- **Source contradiction** (line items 450+300=750 vs stated total 800): on attempt 2, retry **raised a line item from 300 to 350**. Schema-compliant, passed validation, `total_amount` matched the document exactly — a **falsified record stored as "VALID"**.
- **Absent information** (no due date) → a **surrender curve**:
  1. `"<UNKNOWN>"` (honest; rejected on type)
  2. copy of `issue_date` (rejected on ordering)
  3. **fabricated** `issue_date + 30 days` → VALID
- **Lesson:** an instruction to "correct it" becomes an instruction to **"invent it"** when there is nothing to correct. Every rejection reinforces the signal that honesty was wrong.

### The correct architecture
1. Design the schema so contradiction and absence are **expressible**
2. Add a validation layer to catch semantic errors
3. **Restrict** retry to format/structural errors **and cap the attempt count**
4. Route the rest to a human
- **Branch by error class** (the validation edition of Week 3's `errorCategory`/`isRetryable`): format → retry; semantic conflict → human; absence → policy.

### The self-correcting schema pattern
- `stated_total` (as printed) **+** `calculated_total` (sum of line items) **+** `conflict_detected` (boolean)
- The contradiction becomes a **data point**, not an error. The model stops hiding it because it now has **somewhere to sit**.
- Check the arithmetic in code **in addition** to the flag: the model's flag is a **claim**, the arithmetic is **evidence** (prompt = guidance, code = lock).
- Same idea generalizes: conflict flags are the standard pattern for inconsistent source data.

### Instrumentation lesson
- **Log the success payload too.** If you only print on failure, you will never notice that "green" was a fabrication.

---

## 6. TS 4.6 — Multi-instance and multi-pass review

### Why self-review is weak
- The generating session **carries its own reasoning context** and is less likely to question its own decisions.
- ❌ "review your own code carefully" · ❌ extended thinking · ❌ three reviews in the same session
- ✅ An **independent instance** (no generation context)
- Week 4 live proof: an independent reviewer caught the docstring–code contract gap and the missing lines the producing session had left behind.

### Large PRs (e.g. 14 files)
- Symptoms: detailed comments on some files and superficial ones on others; **the same pattern flagged in one file and approved in another**; obvious bugs missed.
- Root cause: **attention dilution**.
- Fix: **per-file local passes plus a separate cross-file integration pass** (prompt chaining).

### Wrong options and why
| Option | Why it's wrong |
|---|---|
| Move to a larger context window | This is an attention **quality** problem, not a capacity problem |
| Run 3 passes, report findings appearing in ≥2 | **Suppresses** real bugs caught intermittently while **passing** consistently produced noise. (Evidence: the noise appeared 2/3 → would pass consensus; the missed real defect was 0/3 → can never be rescued) |
| Ask developers to split the PR | Shifts the burden to humans without fixing the system |
| Repeat within the same session | Repeats the dilution |

> **General rule:** "run N times and take the majority" is almost always **wrong** in Domain 4. Repetition does not fix a design flaw.

- Related pattern: having the model self-report confidence alongside each finding can support calibrated review routing — but **not as the fix for false positives**.

---

## 7. TS 4.5 — Message Batches API

### Bare facts
- **50% cheaper**
- **Up to 24 hours** processing window
- **NO latency SLA** — "usually finishes faster" is not a guarantee
- `custom_id` correlates request/response pairs
- Completion is tracked by **polling**
- **Multi-turn tool calling within a single request is NOT supported**

### Decision rule: **is anyone waiting?**
| Workload | Answer | API |
|---|---|---|
| Blocking pre-merge check | A developer is waiting | **Synchronous** |
| Overnight technical-debt report | Nobody is waiting | **Batch** |
| Live customer support agent | Customer on the line | **Synchronous** |
| Weekly compliance audit | — | **Batch** |
| Initial load of 5,000 documents | — | **Batch** |
| User uploading a document on screen | Waiting | **Synchronous** |

### What can and cannot run inside a batch
| Can | Cannot |
|---|---|
| Single-turn `tool_use` extraction (the tool is **not executed**, the form is filled) | Agentic loops (multi-turn tool execution) |
| Classification, summarization, translation | Subagent orchestration |
| Structured output with a schema | A validation-retry loop **inside one request** |

- **Validation and retry live OUTSIDE the batch:** batch returns → validate → resubmit failures in a **second batch**.

### Failure handling
- Results come back **unordered** → correlate with `custom_id`. *"We can't use batch because results are unordered" is a WRONG option.*
- **Never resubmit the whole batch.** Identify the failed `custom_id`s and resubmit them **with modifications** (e.g. **chunk** documents that hit `max_tokens` or exceeded context limits).
- `stop_reason: "max_tokens"` = truncated output → chunk and resubmit.

### SLA ARITHMETIC (memorize)
- queue budget = SLA − 24h (worst-case processing)
- submission interval ≤ queue budget
- **Two legs: waiting + processing.** Forgetting the queue leg is the most common mistake.
- Always budget the **worst case** (24h), never the average.

| SLA | Queue budget | Result |
|---|---|---|
| 30h | 6h | Submit every 6h or more often |
| 28h | 4h | Submit every 4h |
| 26h | 2h | Submit every 2h |
| 24h | 0 | **Batch CANNOT meet this SLA** |

- Sanity check: *"if I submit every 24h, a document arriving just after a submission waits 24h then takes up to 24h = 48h."*

### Before scaling up
- Refine the schema and few-shot examples on a **small sample (e.g. 50 documents) with the synchronous API** before going to volume.
- Otherwise: you pay for 5,000 documents, lose 18 hours, and start over.
- Week 4 taught the same: the independent reviewer run cost $0.44 → *"refine on samples before scaling"*.

---

## 8. EXAM TRAPS — RED FLAGS

### Options that are almost always WRONG
1. **Anything relying on the model filtering its own confidence:** "self-reported confidence score", "only report high-confidence findings", "be conservative". → *Miscalibration is the problem; a broken calibration cannot be the filter.*
2. **"Add a retry loop"** — when the root cause is **absence** or **source contradiction**.
3. **"Run N times, take the majority"** (consensus filtering).
4. **"Switch to a model with a larger context window"** — for attention-quality problems.
5. **`temperature=0`** — the "permanent wrong answer" on guarantee/compliance questions.
6. **Changing the type** (`number`→`integer`) — for semantic errors.
7. **Sentiment analysis / sentiment-based routing** — sentiment does not indicate complexity.
8. **Over-engineering:** an ML classifier, a routing layer, or a separately trained model before prompt optimization has been tried.
9. **Shifting the burden to users/developers** ("split your PR") — the system stays broken.
10. **Removing the `enum` entirely** — destroys categorization.
11. **Writing the instruction in caps / more forcefully** — guidance stays guidance.
12. **Cleaning output with string operations** — scraping instead of enforcing structure.

### "First step" questions
- "Most effective **first** step" = the **lowest-effort, highest-leverage** root-cause fix.
- Order: **improve descriptions/criteria → few-shot → schema/architecture change → additional infrastructure.**
- Week 3 example: when similar tools are confused, the **first step is enriching the descriptions**, not adding few-shot examples.

### Question pattern → where to look
| Phrasing | Where to look |
|---|---|
| "Schema compliance is 100% but values are wrong" | Semantics → validation / schema design |
| "Plausible values not present in the document, no errors" | Missing nullable on a `required` field |
| "Inconsistent decisions on ambiguous documents" | Few-shot |
| "High FP rate, the team lost trust" | Categorical REPORT/SKIP + temporarily disable the FP category |
| "14 files in one pass, contradictory findings" | Per-file passes + integration pass |
| "Reviewing code it generated itself" | Independent instance |
| "Reduce cost" + "runs overnight" | Batch |
| "Reduce cost" + "blocking" | Keep synchronous |
| "X-hour SLA + batch" | Queue budget = SLA − 24 |

---

## 9. MULTIPLE-RESPONSE PROCEDURE (personal weak spot — 4 errors)

Each item **states** how many responses to select. There is **no partial credit**.

1. **Read the last line first** → does it say "(Select two)"?
2. Mark each option **independently** true/false (do not hunt for "the best two" in your head).
3. **Count** your trues and compare with the required number.
4. If there are too many: narrow to the ones that meet the criterion **exactly**.
5. Never write the same option twice.

---

## 10. CROSS-WEEK CONNECTIONS

| This week's topic | Where it comes from |
|---|---|
| `tool_result` → `role: "user"` (retry feedback) | Week 1 agentic loop |
| Prompt = guidance, code/schema = lock | Weeks 1–2 (hook vs prompt) |
| `tool_choice` three gears + turnstile pattern | Week 3 |
| Branching by error class (`errorCategory`, `isRetryable`) | Week 3 MCP error responses |
| "Improve descriptions first, then few-shot" | Week 3 tool descriptions |
| Test-first iteration = a validation-retry loop | Week 4 (pytest) |
| The independent reviewer instance | Week 4 lesson 4.6 (live proof) |
| `-p`, `--output-format json`, `--json-schema` (structured output in CI) | Week 4 lesson 4.6 |
| Refine on a sample, then scale | Week 4 ($0.44 reviewer run) |
| `conflict_detected`, annotating conflicts with attribution | **Bridge to Week 6** (provenance, human review) |

---

## 11. ONE-LINE ESSENCES

- If the model **cannot express** something, it says something it can express instead. Schema design is **giving the model the vocabulary it needs to tell the truth**.
- A schema **draws the boxes**; it does not audit which number goes in them.
- An instruction to "correct it" becomes an instruction to **"invent it"** when there is nothing to correct.
- A criteria list is not censorship, it is a **search plan**.
- Prompt-layer work wins **under ambiguity**; obvious signals need no help.
- Batch: **if someone is waiting, synchronous; if nobody is waiting, batch.**
