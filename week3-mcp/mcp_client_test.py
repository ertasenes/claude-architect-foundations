"""Plug the Agent SDK into our standalone MCP server.
The SDK will LAUNCH order_server.py as a subprocess and talk stdio."""

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
        "mcp__order-support__cancel_order",
    ],
)


async def main():
    prompt = ("Check the status of order 7001, and then cancel it "
              "because the customer changed their mind.")
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[TOOL CALL] {block.name}  input={block.input}")
                elif isinstance(block, TextBlock):
                    print(f"[AGENT] {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"[RESULT] cost=${message.total_cost_usd:.4f}")


asyncio.run(main())
