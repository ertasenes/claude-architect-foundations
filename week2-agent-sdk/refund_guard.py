import asyncio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    tool,
    create_sdk_mcp_server,
    HookMatcher,
)

REFUND_LIMIT_USD = 500


# --- 1) Our own tool (Week 1's JSON schema, now in one line) ---
@tool(
    "process_refund",
    "Processes a refund for a customer order. Requires the order id and the refund amount in USD.",
    {"order_id": str, "amount": float},
)
async def process_refund(args):
    # In real life this would hit a payment system; we fake it.
    return {
        "content": [
            {"type": "text", "text": f"Refund of ${args['amount']} for {args['order_id']} processed."}
        ]
    }


# Package the tool into an in-process MCP server named "support"
support_server = create_sdk_mcp_server(name="support", tools=[process_refund])


# --- 2) The inspector: a PreToolUse hook ---
async def refund_guard(input_data, tool_use_id, context):
    amount = input_data["tool_input"].get("amount", 0)
    if amount > REFUND_LIMIT_USD:
        print(f"    [HOOK] BLOCKED: ${amount} > ${REFUND_LIMIT_USD} limit")
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Company policy: refunds above ${REFUND_LIMIT_USD} must be "
                    "handled by a human agent. Inform the customer that this "
                    "case is being escalated."
                ),
            }
        }
    print(f"    [HOOK] allowed: ${amount}")
    return {}  # empty dict = no objection, let it run


options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    system_prompt="You are a customer support agent. Use the refund tool to process refunds.",
    mcp_servers={"support": support_server},
    allowed_tools=["mcp__support__process_refund"],
    hooks={
        "PreToolUse": [
            HookMatcher(matcher="mcp__support__process_refund", hooks=[refund_guard]),
        ],
    },
)


async def run_case(prompt):
    print(f"\n=== CASE: {prompt}")
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[TOOL CALL] {block.name} {block.input}")
                elif isinstance(block, TextBlock):
                    print(f"[AGENT] {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"[RESULT] cost=${message.total_cost_usd:.4f}")


async def main():
    await run_case("Please refund order ORD-1001 for $200.")
    await run_case("Please refund order ORD-2002 for $800.")


asyncio.run(main())
