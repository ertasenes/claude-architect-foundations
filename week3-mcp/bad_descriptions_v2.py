"""Two-arm experiment on poor tool descriptions:
Arm A: tool_choice auto  -> what does the model SAY instead of acting?
Arm B: tool_choice any   -> when forced to act, which wrong tool does it grab?"""

import anthropic

client = anthropic.Anthropic()

TOOLS = [
    {
        "name": "get_customer",
        "description": "Retrieves customer information.",   # still minimal
        "input_schema": {
            "type": "object",
            "properties": {"identifier": {"type": "string"}},
            "required": ["identifier"],
        },
    },
    {
        "name": "lookup_order",
        "description": "Retrieves order details.",          # still minimal
        "input_schema": {
            "type": "object",
            "properties": {"identifier": {"type": "string"}},
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
                # show only the first 120 chars so output stays readable
                print(f"run {i+1}: no_tool | model said: {block.text[:120]!r}")
        counts[chosen] += 1
    print("Totals:", counts)


run_arm("A", {"type": "auto"})
run_arm("B", {"type": "any"})
