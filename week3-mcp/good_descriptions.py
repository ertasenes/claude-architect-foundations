"""Rematch: same two-arm experiment, but with RICH tool descriptions
following the exam guide recipe: purpose + input format + example
queries + boundaries pointing to the neighbor tool."""

import anthropic

client = anthropic.Anthropic()

TOOLS = [
    {
        "name": "get_customer",
        "description": (
            "Retrieves a customer's account profile (name, email, address, "
            "loyalty status). Use ONLY when the request is about the account "
            "itself, e.g. 'update my email' or 'what is my loyalty tier?'. "
            "Input must be a customer ID in the form CUST-XXXX or a verified "
            "email address. Do NOT use for order/package/delivery questions — "
            "use lookup_order for those, even if the customer says 'my account'."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Customer ID (CUST-XXXX) or email address.",
                }
            },
            "required": ["identifier"],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Retrieves the status and details of a specific order: shipping "
            "state, expected delivery date, items, amounts. Use for any "
            "question about an order or package, e.g. 'where is my package "
            "#12345?' or 'has order 98765 shipped?'. Input is the numeric "
            "order number (digits only, strip any leading #). Do NOT use for "
            "account/profile questions — use get_customer for those."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Order number, digits only, e.g. '12345'.",
                }
            },
            "required": ["identifier"],
        },
    },
]

PROMPT = "Hi, can you check on my account? My package #12345 still hasn't arrived."


def run_arm(label, tool_choice, runs=5):
    print(f"\n=== Arm {label} | tool_choice={tool_choice} ===")
    counts = {"get_customer": 0, "lookup_order": 0, "no_tool": 0}
    for i in range(runs):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=500,
            tools=TOOLS,
            tool_choice=tool_choice,
            messages=[{"role": "user", "content": PROMPT}],
        )
        chosen = "no_tool"
        for block in response.content:
            if block.type == "tool_use":
                chosen = block.name
                print(f"run {i+1}: {chosen}  input={block.input}")
                break
            elif block.type == "text":
                print(f"run {i+1}: no_tool | model said: {block.text[:120]!r}")
        counts[chosen] += 1
    print("Totals:", counts)


run_arm("A", {"type": "auto"})
run_arm("B", {"type": "any"})
