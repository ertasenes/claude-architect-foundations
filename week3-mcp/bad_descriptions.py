"""Experiment: how often does Claude pick the wrong tool
when tool descriptions are minimal? (Exam guide, Task 2.1)"""

import anthropic

client = anthropic.Anthropic()

# Two tools with deliberately POOR, near-identical descriptions
TOOLS = [
    {
        "name": "get_customer",
        "description": "Retrieves customer information.",   # minimal!
        "input_schema": {
            "type": "object",
            "properties": {"identifier": {"type": "string"}},
            "required": ["identifier"],
        },
    },
    {
        "name": "lookup_order",
        "description": "Retrieves order details.",          # minimal!
        "input_schema": {
            "type": "object",
            "properties": {"identifier": {"type": "string"}},
            "required": ["identifier"],
        },
    },
]

# An ambiguous request: mentions "my account" but the real need is an order
PROMPT = "Hi, can you check on my account? My package #12345 still hasn't arrived."

counts = {"get_customer": 0, "lookup_order": 0, "no_tool": 0}

for i in range(5):
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=500,
        tools=TOOLS,
        messages=[{"role": "user", "content": PROMPT}],
    )
    # find the FIRST tool the model reached for in this run
    chosen = "no_tool"
    for block in response.content:
        if block.type == "tool_use":
            chosen = block.name
            break
    counts[chosen] += 1
    print(f"run {i+1}: {chosen}")

print("\nTotals:", counts)
