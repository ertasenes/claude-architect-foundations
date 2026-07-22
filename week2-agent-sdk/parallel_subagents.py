import asyncio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    AssistantMessage,
    UserMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
    ToolResultBlock,
)

subagents = {
    "greeting-writer": AgentDefinition(
        description="Writes short, warm greeting messages.",
        prompt="You are a greeting writer. Write exactly one short, warm greeting sentence.",
        tools=[],
        model="haiku",
    ),
    "slogan-writer": AgentDefinition(
        description="Writes short, punchy slogans for projects and products.",
        prompt="You are a slogan writer. Write exactly one short, punchy slogan.",
        tools=[],
        model="haiku",
    ),
}

options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    agents=subagents,
    allowed_tools=["Task"],
)


async def main():
    prompt = (
        "Two INDEPENDENT jobs - run them in parallel, not one after another: "
        "1) greeting-writer: a welcome for a student named Enes. "
        "2) slogan-writer: a slogan for a project called 'claude-architect-foundations'. "
        "Then present both results together."
    )
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    # block.id = this ticket's tracking number (last 8 chars for readability)
                    print(f"[SPAWN] {block.input.get('subagent_type')}  (ticket ...{block.id[-8:]})")
                elif isinstance(block, TextBlock) and not message.parent_tool_use_id:
                    print(f"[COORDINATOR] {block.text}")
        elif isinstance(message, UserMessage):
            # tool results travel back to the coordinator inside user-role messages
            blocks = message.content if isinstance(message.content, list) else []
            for block in blocks:
                if isinstance(block, ToolResultBlock):
                    print(f"[RETURN ...{block.tool_use_id[-8:]}] {block.content}")
        elif isinstance(message, ResultMessage):
            print(f"[RESULT] cost=${message.total_cost_usd:.4f} | turns={message.num_turns}")


asyncio.run(main())
