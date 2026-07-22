import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions, AssistantMessage, ResultMessage, TextBlock

# Options = the agent's configuration panel.
# "model" picks the engine; Sonnet is much cheaper than Opus and plenty for our exercises.
options = ClaudeAgentOptions(model="claude-sonnet-4-6")


async def main():
    async for message in query(prompt="What is 2 + 2?", options=options):
        # This time we don't print raw objects; we pick what we care about.
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"ANSWER: {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"COST: ${message.total_cost_usd:.4f} | turns: {message.num_turns}")


asyncio.run(main())
