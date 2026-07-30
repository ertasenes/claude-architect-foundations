import asyncio
from claude_agent_sdk import query


async def main():
    # query() sends a prompt to the agent and streams back messages
    # as they are produced (async iterator = messages arrive one by one).
    async for message in query(prompt="What is 2 + 2?"):
        print(message)


asyncio.run(main())

# EXAM TAKEAWAY: The Agent SDK's query() is an async iterator — you await messages as they stream in, rather than getting one blocking response.
