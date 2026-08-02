"""Lesson 6.1b - Progressive summarization erodes facts across generations.

Each generation compresses (previous summary + newly arrived turns) into a fixed
sentence budget, exactly like a long-running session under a token budget.
We track 11 transactional facts and see which ones survive each pass.
Then: does a re-extracted CASE FACTS layer hold at 100% instead?
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

NEW_TURNS = [
    """
[turn 11] Customer: I'd also like something for the trouble.
[turn 12] Agent: I added a one-time 5.00 USD account credit, code CR-5X9,
          valid until 2026-09-30.
[turn 13] Customer: And the water tank was scratched too, is that covered?
[turn 14] Agent: Yes, that falls under the same damage claim, no extra refund.
""",
    """
[turn 15] Customer: Can you send me written confirmation?
[turn 16] Agent: Confirmation goes to e.ertas@example.com within 24 hours,
          reference ticket TCK-77120.
[turn 17] Customer: And if the refund is late, who do I contact?
[turn 18] Agent: Reply to that same ticket and it routes to the refunds team.
""",
]

# The facts the business actually needs, with the string that must survive.
FACTS = {
    "purchase date": "2026-06-14",
    "item price": "429",
    "refund amount": "86.50",
    "non-refundable fee": "14.99",
    "customer deadline": "2026-08-05",
    "deadline REASON (interest)": "interest",
    "subscription price": "9.99",
    "cancellation date": "2026-08-02",
    "credit code": "CR-5X9",
    "credit expiry": "2026-09-30",
    "ticket id": "TCK-77120",
}

SUMMARY_PROMPT = (
    "You are maintaining a running case summary for a support session that must "
    "fit a strict context budget. Rewrite everything below into at most {n} "
    "sentences of prose. Keep it readable for the next agent.\n\n{body}"
)

FACTS_TOOL = {
    "name": "record_case_facts",
    "description": (
        "Record the transactional facts of a support case exactly as stated. "
        "Copy every value verbatim: do not round amounts, do not reformat dates, "
        "do not paraphrase the customer's own words. Use null for anything the "
        "text does not state."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "order_id": {"type": ["string", "null"]},
            "purchase_date": {"type": ["string", "null"]},
            "item_sku": {"type": ["string", "null"]},
            "item_price_usd": {"type": ["number", "null"]},
            "agreed_refund_usd": {"type": ["number", "null"]},
            "non_refundable_fee_usd": {"type": ["number", "null"]},
            "customer_stated_deadline": {"type": ["string", "null"]},
            "customer_stated_deadline_reason": {"type": ["string", "null"]},
            "subscription_monthly_usd": {"type": ["number", "null"]},
            "subscription_cancel_effective": {"type": ["string", "null"]},
            "account_credit_usd": {"type": ["number", "null"]},
            "account_credit_code": {"type": ["string", "null"]},
            "account_credit_expiry": {"type": ["string", "null"]},
            "ticket_id": {"type": ["string", "null"]},
            "open_promises": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Commitments made to the customer, verbatim",
            },
        },
        "required": ["order_id", "agreed_refund_usd", "customer_stated_deadline"],
    },
}


def summarize(body: str, sentences: int) -> str:
    r = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user",
                   "content": SUMMARY_PROMPT.format(n=sentences, body=body)}],
    )
    return r.content[0].text.strip()


def extract_facts(body: str) -> dict:
    r = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        tools=[FACTS_TOOL],
        tool_choice={"type": "tool", "name": "record_case_facts"},
        messages=[{"role": "user", "content": body}],
    )
    return next(b for b in r.content if b.type == "tool_use").input


def score(label: str, text: str) -> int:
    lost = [k for k, v in FACTS.items() if v.lower() not in text.lower()]
    kept = len(FACTS) - len(lost)
    print(f"\n{label}: {kept}/{len(FACTS)} facts present")
    if lost:
        print("  LOST: " + ", ".join(lost))
    return kept


if __name__ == "__main__":
    # Generation 1: the raw transcript compressed for the first time.
    full_text = TRANSCRIPT
    summary = summarize(full_text, 4)
    print("=" * 70)
    print("GENERATION 1 SUMMARY")
    print("=" * 70)
    print(summary)
    score("gen 1", summary)

    # Generations 2 and 3: previous summary + new turns, compressed again.
    for i, turns in enumerate(NEW_TURNS, start=2):
        full_text = full_text + turns
        body = "RUNNING SUMMARY SO FAR:\n" + summary + "\n\nNEW TURNS:\n" + turns
        summary = summarize(body, 4)
        print("\n" + "=" * 70)
        print(f"GENERATION {i} SUMMARY")
        print("=" * 70)
        print(summary)
        score(f"gen {i}", summary)

    # The other design: a facts layer re-extracted from the full transcript,
    # never compressed, prepended to whatever summary we carry.
    facts = extract_facts(full_text)
    facts_text = json.dumps(facts, indent=2)
    print("\n" + "=" * 70)
    print("CASE FACTS LAYER (rebuilt from full history, never summarized)")
    print("=" * 70)
    print(facts_text)
    score("facts layer", facts_text)
