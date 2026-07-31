# Week 5 — One-Page Summary (Domain 4, 20%)

**The week's question:** how do we make the model's output trustworthy?
**The answer in one sentence:** reliability is not one mechanism — six layers each own a
different failure class, and most exam items ask which layer owns a given failure.

## The pyramid, with owners
| Layer | Owns |
|---|---|
| Schema (tool_use + input_schema) | malformed JSON, wrong types, missing keys |
| Schema design (nullable, enum + "other") | fabrication of absent data, information loss to closed lists |
| Few-shot | inconsistent judgment on ambiguous cases, structural variety |
| Validation (Pydantic) | semantic errors: sums, wrong-field placement, impossible dates |
| Retry | format and structural errors ONLY |
| Human review | source contradictions and low-confidence cases |

## Six lessons, six sentences
- **5.1** Asking for JSON is guidance; forcing a schema as a tool is a lock. Same prompt, three runs, three different envelopes; the schema produced byte-identical output three times.
- **5.2** Fabrication comes from the only option the schema leaves open, not from the model's character. Without an escape hatch (nullable, "other") the model MUST write something.
- **5.3** Few-shot wins under ambiguity and changes nothing against obvious signals. Examples must carry the REASONING so the model generalizes instead of memorizing.
- **5.4** Retry works only in the "information present, shape wrong" column. In the other two columns it pushes the model into fabrication, step by step — caught on tape.
- **5.5** "Be conservative" is a stance; categorical REPORT/SKIP lists are a specification. Criteria are not just a filter, they are a SEARCH PLAN.
- **5.6** Someone waiting → synchronous; nobody waiting → batch. In SLA arithmetic, never forget the queue leg.

## Three most striking live findings
1. **Silent falsification.** With a self-contradictory source (items 750 vs stated total 800), the retry loop raised a line item from 300 to 350. Schema-compliant, passed validation, stored as VALID.
2. **The surrender curve.** On a document with no due date, the model tried honesty twice ("<UNKNOWN>", then the issue date); both were rejected, so attempt 3 fabricated a date. Every rejection reinforced that honesty was wrong.
3. **Criteria raised recall too.** The vague prompt missed parse_amount's silent 0.0 fallback in all three runs; the categorical prompt flagged it critical 3/3. An experiment run for precision demonstrated a recall gain.

## Formulas and rules worth carrying
- required = the key must be present; the value may be null.
- Schema guarantees syntax and types, never semantics.
- tool required but which varies → "any"; specific tool required → forced.
- Three-column retry test: present-but-malformed → retry; absent → nullable + policy; self-contradictory → flag + human.
- stated_total + calculated_total + conflict_detected turns a contradiction into a data point.
- Batch: 50% cheaper, up to 24h, no latency SLA, no multi-turn tool execution; correlate and resubmit by custom_id.
- Queue budget = SLA − 24h. A 24h SLA cannot be met by batch at all.

## Status
- Quizzes: 5.1 4/5 · 5.2 5/5 · 5.3 4.5/6 · 5.4 5/6 · 5.5 4/6 · **final 10/12**
- Closed gaps: retry boundary, consensus-filtering trap, type-tweak fallacy
- Open gaps for Week 7: options relying on model self-reported confidence (chosen three times); multiple-response reading discipline (four format errors); the queue leg in SLA arithmetic
- Exercise 3 from the exam guide: complete
- Files: 9 Python scripts, notes/week5-structured-output.md, quicknotes/tr + quicknotes/en
