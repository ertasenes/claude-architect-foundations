import asyncio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AssistantMessage,
    ResultMessage,
    TextBlock,
)


async def run(prompt, options=None):
    """Run one query, print the agent's text, return the session id."""
    if options is None:
        options = ClaudeAgentOptions(model="claude-sonnet-4-6")
    session_id = None
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"[AGENT] {block.text}")
        elif isinstance(message, ResultMessage):
            session_id = message.session_id
            print(f"[SESSION] ...{session_id[-8:]}")
    return session_id


async def main():
    print("=== ACT 1: fresh session, we share a fact")
    sid = await run("Remember this: my name is Enes and my favorite color is teal. Just confirm briefly.")

    print("\n=== ACT 2: a BRAND NEW session asks the same thing")
    await run("What is my name and favorite color? Answer briefly.")

    print("\n=== ACT 3: RESUME Act 1's session and ask again")
    await run(
        "What is my name and favorite color? Answer briefly.",
        ClaudeAgentOptions(model="claude-sonnet-4-6", resume=sid),
    )

    print("\n=== ACT 4: FORK from Act 1 (original stays untouched)")
    fork_sid = await run(
        "From now on, call me 'Captain Enes'. Confirm briefly.",
        ClaudeAgentOptions(model="claude-sonnet-4-6", resume=sid, fork_session=True),
    )
    print(f"\noriginal session: ...{sid[-8:]}")
    print(f"forked session:   ...{fork_sid[-8:]}  (different id = a real copy)")


asyncio.run(main())
