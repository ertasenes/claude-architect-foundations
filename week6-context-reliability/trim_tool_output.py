"""Lesson 6.1c - Trimming verbose tool results before they enter context.

A realistic order record carries ~40 fields. A returns conversation needs ~6 of
them. In an agentic loop every tool_result is re-sent on every subsequent
request, so irrelevant fields are not paid for once - they are paid for again
on every turn.

Arm A: full tool_result goes into context.
Arm B: a projection function keeps only the return-relevant fields, and also
       normalizes heterogeneous formats (unix epoch / ISO date / numeric status
       code) into one shape. In the Agent SDK this function is a PostToolUse
       hook.

Measured: cumulative input_tokens across the conversation, plus whether the
trimmed arm can still answer the same questions correctly.
"""

import json
from datetime import datetime, timezone
from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-4-5"  # keep in sync with earlier weeks

STATUS_CODES = {1: "pending", 2: "shipped", 3: "delivered", 4: "returned"}


def make_order(order_id: str, sku: str, price: float, epoch: int, code: int) -> dict:
    """A record shaped like a real backend response: everything the DB has."""
    return {
        "order_id": order_id,
        "internal_pk": 8827341 + code,
        "customer_id": "C-5521",
        "customer_email_hash": "9f2b1c7ae4d0",
        "billing_address_line1": "1 Example Street",
        "billing_address_line2": "Suite 400",
        "billing_city": "Istanbul",
        "billing_postcode": "34000",
        "billing_country_iso": "TR",
        "shipping_address_line1": "1 Example Street",
        "shipping_city": "Istanbul",
        "shipping_carrier": "EXP-CARGO",
        "shipping_tracking": "EX99" + order_id[-3:],
        "shipping_service_level": "standard-48h",
        "warehouse_code": "WH-EU-03",
        "picker_id": "P-118",
        "packer_id": "P-402",
        "sku": sku,
        "product_title_localized": "Espresso Machine EM series",
        "product_category_path": "home/kitchen/coffee/espresso",
        "unit_price": price,
        "quantity": 1,
        "currency": "USD",
        "tax_rate": 0.18,
        "tax_amount": round(price * 0.18, 2),
        "shipping_fee": 14.99,
        "discount_code": None,
        "discount_amount": 0.0,
        "payment_method": "card",
        "payment_processor": "proc-a",
        "payment_auth_code": "AUTH-" + order_id[-4:],
        "created_at_epoch": epoch,            # unix seconds
        "updated_at_iso": "2026-06-20T09:14:00Z",  # ISO 8601
        "status_code": code,                  # numeric
        "fulfilment_batch": "B-2026-24",
        "gift_wrap": False,
        "marketing_opt_in": True,
        "loyalty_points_earned": 42,
        "review_submitted": False,
        "internal_notes": "no flags",
    }


ORDERS = {
    "A-40917": make_order("A-40917", "EM-220", 429.00, 1781395200, 3),
    "A-41055": make_order("A-41055", "GR-110", 189.50, 1782000000, 2),
    "A-41190": make_order("A-41190", "MK-005", 64.00, 1782604800, 4),
}

# The only fields a returns conversation actually needs.
KEEP = ["order_id", "sku", "unit_price", "shipping_fee", "currency"]


def trim(record: dict) -> dict:
    """PostToolUse-equivalent: project and normalize before the model sees it."""
    out = {k: record[k] for k in KEEP}
    # Normalize three different time/status encodings into one shape.
    out["purchase_date"] = datetime.fromtimestamp(
        record["created_at_epoch"], tz=timezone.utc
    ).date().isoformat()
    out["last_update"] = record["updated_at_iso"][:10]
    out["status"] = STATUS_CODES[record["status_code"]]
    return out


TOOL = {
    "name": "lookup_order",
    "description": (
        "Look up one order by its order id (format A-NNNNN). Returns the order's "
        "item, price, fees and current status. Use this for questions about a "
        "specific order; use get_customer for account-level questions."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"order_id": {"type": "string"}},
        "required": ["order_id"],
    },
}

TURNS = [
    "Order A-40917 arrived damaged. What did I pay for the item itself?",
    "Also check A-41055 - what is its status and what did it cost?",
    "And A-41190, was that one returned already? What was the price?",
    "Across all three orders, what is the total of the item prices, and how much "
    "shipping did I pay in total?",
]

SYSTEM = (
    "You are a returns support agent. Use lookup_order for order questions. "
    "Answer with exact figures from tool results. Keep answers to two sentences."
)


def run(label: str, use_trim: bool) -> None:
    messages: list[dict] = []
    cumulative_input = 0
    print("\n" + "=" * 70)
    print(f"{label}")
    print("=" * 70)

    for turn_no, user_text in enumerate(TURNS, start=1):
        messages.append({"role": "user", "content": user_text})

        # Inner agentic loop: keep going while the model asks for tools.
        while True:
            r = client.messages.create(
                model=MODEL, max_tokens=700, system=SYSTEM,
                tools=[TOOL], messages=messages,
            )
            cumulative_input += r.usage.input_tokens
            messages.append({"role": "assistant", "content": r.content})

            if r.stop_reason != "tool_use":
                break

            results = []
            for block in r.content:
                if block.type != "tool_use":
                    continue
                record = ORDERS.get(block.input["order_id"])
                payload = {} if record is None else (
                    trim(record) if use_trim else record
                )
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(payload),
                })
            # tool_result travels with role "user" - Week 1 rule.
            messages.append({"role": "user", "content": results})

        text = "".join(b.text for b in r.content if b.type == "text")
        print(f"\n[turn {turn_no}] {text.strip()}")
        print(f"  cumulative input_tokens so far: {cumulative_input}")

    print(f"\n  TOTAL input_tokens for {label}: {cumulative_input}")


if __name__ == "__main__":
    raw_size = len(json.dumps(ORDERS["A-40917"]))
    trim_size = len(json.dumps(trim(ORDERS["A-40917"])))
    print(f"one record: raw {raw_size} chars -> trimmed {trim_size} chars "
          f"({100 - round(trim_size / raw_size * 100)}% smaller)")
    print("\ntrimmed shape:")
    print(json.dumps(trim(ORDERS["A-40917"]), indent=2))

    run("ARM A - full tool results in context", use_trim=False)
    run("ARM B - trimmed + normalized tool results", use_trim=True)
