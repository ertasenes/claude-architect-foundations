"""Lesson 6.1 - Progressive summarization vs a persistent case-facts block.

Arm A: long support transcript -> 4-sentence summary -> answer 5 precise questions.
Arm B: same summary + a schema-extracted CASE FACTS block -> same 5 questions.

What summarization silently drops is exactly what the business needs:
amounts, dates, order ids and customer-stated expectations.
"""

import json
from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-4-5"  # keep in sync with earlier weeks

TRANSCRIPT = """
[turn 1] Customer: My espresso machine arrived cracked. This is order A-40917.
[turn 2] Agent: I'm sorry about that. I see order A-40917, placed 2026-06-14,
         item SKU EM-220 at 429.00 USD, delivered 2026-06-19.
[turn 3] Customer: I don't want to send it back, it still works. I just want
         something off the price.
[turn 4] Agent: I can offer a partial refund instead of a return. Based on the
         photos, our damage table allows 86.50 USD back on this unit.
[turn 5] Customer: Fine, 86.50 works. But I paid shipping too, is that included?
[turn 6] Agent: The 14.99 USD shipping fee is non-refundable under our policy
         because the item was delivered and is being kept.
[turn 7] Customer: OK. One important thing: the money has to be back before
         2026-08-05, because my card statement closes that day and I don't want
         to pay interest on the full amount.
[turn 8] Agent: Understood, I noted 2026-08-05 as your deadline. I also see an
         active accessory subscription on this account, 9.99 USD per month,
         started 2026-05-02.
[turn 9] Customer: Cancel that too, but I already paid this month, so let it run
         to the end of the cycle.
[turn 10] Agent: Cancellation will be effective 2026-08-02, the end of the
         current billing cycle. No further charges after that date.
"""

QUESTIONS = """Answer these five questions, one line each, numbered:
1. What is the exact partial refund amount that was agreed?
2. What is the order id and its purchase date?
3. What deadline did the customer state, and what reason did they give for it?
4. Which fee is non-refundable, and how much is it?
5. On what date does the subscription cancellation take effect?"""

EXPECTED = {
    "refund amount": "86.50",
    "order id": "A-40917",
    "purchase date": "2026-06-14",
    "customer deadline": "2026-08-05",
    "non-refundable fee": "14.99",
    "cancellation date": "2026-08-02",
}

FACTS_TOOL = {
    "name": "record_case_facts",
    "description": (
        "Record the transactional facts of a support case exactly as stated in "
        "the conversation. Copy every value verbatim: do not round amounts, do "
        "not reformat dates, do not paraphrase what the customer said. Use null "
        "for any field the conversation does not state."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": ["string", "null"]},
            "purchase_date": {"type": ["string", "null"], "description": "ISO 8601"},
            "item_sku": {"type": ["string", "null"]},
            "item_price_usd": {"type": ["number", "null"]},
            "agreed_refund_usd": {"type": ["number", "null"]},
            "non_refundable_fee_usd": {"type": ["number", "null"]},
            "non_refundable_fee_reason": {"type": ["string", "null"]},
            "customer_stated_deadline": {"type": ["string", "null"]},
            "customer_stated_deadline_reason": {
                "type": ["string", "null"],
                "description": "Why the customer needs this date, in their own terms",
            },
            "subscription_monthly_usd": {"type": ["number", "null"]},
            "subscription_cancel_effective": {"type": ["string", "null"]},
        },
        "required": [
            "order_id",
            "agreed_refund_usd",
            "customer_stated_deadline",
            "subscription_cancel_effective",
        ],
    },
}


def summarize(transcript: str) -> str:
    """The naive move: compress history into prose before the next turn."""
    r = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": (
                "Summarize this support conversation in 4 sentences for a "
                "colleague who will take over the case.\n\n" + transcript
            ),
        }],
    )
    return r.content[0].text.strip()


def extract_facts(transcript: str) -> dict:
    """Week 5 technique reused: forced tool_use as a fact-capture form."""
    r = client.messages.create(
        model=MODEL,
        max_tokens=800,
        tools=[FACTS_TOOL],
        tool_choice={"type": "tool", "name": "record_case_facts"},
        messages=[{"role": "user", "content": transcript}],
    )
    block = next(b for b in r.content if b.type == "tool_use")
    return block.input


def answer(context_block: str) -> str:
    """Resume the case using only what we handed over."""
    r = client.messages.create(
        model=MODEL,
        max_tokens=700,
        system=(
            "You are a support agent resuming a case. Answer ONLY from the "
            "context provided. If a value is not present in the context, write "
            "exactly NOT IN CONTEXT for that line. Never guess a number or date."
        ),
        messages=[{"role": "user", "content": context_block + "\n\n" + QUESTIONS}],
    )
    return r.content[0].text.strip()


def score(label: str, text: str) -> None:
    survived = 0
    print(f"\n--- {label}: fact survival ---")
    for name, value in EXPECTED.items():
        hit = value in text
        survived += hit
        print(f"  {'OK  ' if hit else 'LOST'} {name}: {value}")
    print(f"  score: {survived}/{len(EXPECTED)}")


if __name__ == "__main__":
    summary = summarize(TRANSCRIPT)
    print("=" * 70)
    print("SUMMARY HANDED OVER (both arms get this)")
    print("=" * 70)
    print(summary)

    # Arm A: summary only
    arm_a = answer("CASE HISTORY (summarized):\n" + summary)
    print("\n" + "=" * 70)
    print("ARM A - summary only")
    print("=" * 70)
    print(arm_a)
    score("ARM A", arm_a)

    # Arm B: summary + case facts block, facts first (position matters)
    facts = extract_facts(TRANSCRIPT)
    facts_block = (
        "CASE FACTS (verbatim, never summarize this block):\n"
        + json.dumps(facts, indent=2)
        + "\n\nCASE HISTORY (summarized):\n"
        + summary
    )
    arm_b = answer(facts_block)
    print("\n" + "=" * 70)
    print("ARM B - case facts block + summary")
    print("=" * 70)
    print(arm_b)
    score("ARM B", arm_b)

    print("\n--- extracted facts (this is the layer that must survive) ---")
    print(json.dumps(facts, indent=2))
