"""Third gear of tool_choice: forcing a specific tool.
Arm A: auto        -> does the model bother with extract_metadata?
Arm B: forced      -> extract_metadata is guaranteed first, then we
                      RELEASE the constraint for the follow-up turn.
(Exam guide, Task 2.3 / 4.3)"""

import json
import anthropic

client = anthropic.Anthropic()

TICKET = (
    "Ticket #T-4417 from maria.lopez@example.com (priority: high): "
    "'Your app deleted my draft invoice twice today. I lose 20 minutes "
    "each time. If this happens again we are cancelling our plan.'"
)

TOOLS = [
    {
        "name": "extract_metadata",
        "description": (
            "Extracts structured metadata from a support ticket: ticket_id, "
            "customer_email, priority. Company policy requires this to run "
            "FIRST on every ticket, before any other processing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "customer_email": {"type": "string"},
                "priority": {"type": "string"},
            },
            "required": ["ticket_id", "customer_email", "priority"],
        },
    },
    {
        "name": "summarize_ticket",
        "description": (
            "Produces a one-sentence summary of the ticket body for the "
            "support dashboard."
        ),
        "input_schema": {
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
    },
]

PROMPT = f"Please summarize this support ticket:\n\n{TICKET}"


def run_arm(label, first_choice):
    print(f"\n=== Arm {label} | first tool_choice={first_choice} ===")
    messages = [{"role": "user", "content": PROMPT}]
    tool_choice = first_choice
    for step in range(5):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=800,
            tools=TOOLS,
            tool_choice=tool_choice,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            for block in response.content:
                if block.type == "text":
                    print(f"[FINAL] {block.text[:150]}")
            return

        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                print(f"[step {step+1}] called: {block.name}")
                print(f"          input: {json.dumps(block.input)[:120]}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": "ok, recorded.",
                })
        messages.append({"role": "user", "content": tool_results})

        # CRITICAL: release the turnstile after the first pass.
        # If we kept forcing, the model would be OBLIGED to call
        # extract_metadata again on every single turn, forever.
        tool_choice = {"type": "auto"}


run_arm("A", {"type": "auto"})
run_arm("B", {"type": "tool", "name": "extract_metadata"})
