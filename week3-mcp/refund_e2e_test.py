"""End-to-end test of Exercise 1: a refund request ABOVE the $500 limit.
Expected choreography: lookup -> refund attempt -> business error ->
escalate_to_human with a structured handoff."""

import asyncio
from claude_agent_sdk import (
    query, ClaudeAgentOptions, AssistantMessage, TextBlock, ToolUseBlock,
    ResultMessage,
)

options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    mcp_servers={
        "order-support": {
            "type": "stdio",
            "command": "python",
            "args": ["week3-mcp/order_server.py"],
        }
    },
    allowed_tools=[
        "mcp__order-support__lookup_order",
        "mcp__order-support__process_refund",
        "mcp__order-support__escalate_to_human",
    ],
)


async def main():
    prompt = ("Customer maria.lopez@example.com says order 7002 arrived "
              "damaged and demands a full refund of the order amount. "
              "Handle this case.")
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[TOOL CALL] {block.name}")
                    print(f"            input={block.input}")
                elif isinstance(block, TextBlock):
                    print(f"[AGENT] {block.text[:300]}")
        elif isinstance(message, ResultMessage):
            print(f"[RESULT] cost=${message.total_cost_usd:.4f}")


asyncio.run(main())
