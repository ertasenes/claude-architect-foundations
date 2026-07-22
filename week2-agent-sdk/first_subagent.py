import asyncio
from claude_agent_sdk import (
    query,
    ClaudeAgentOptions,
    AgentDefinition,
    AssistantMessage,
    ResultMessage,
    TextBlock,
    ToolUseBlock,
)

# AgentDefinition = the station's job card:
#   description -> tells the COORDINATOR when to delegate here
#   prompt      -> the subagent's own system prompt (its identity)
#   tools       -> what this station is allowed to use ([] = nothing)
#   model       -> each station can run on a different engine
subagents = {
    "greeting-writer": AgentDefinition(
        description=(
            "Writes short, warm greeting messages. "
            "Use this agent whenever a greeting or welcome text is needed."
        ),
        prompt=(
            "You are a greeting writer. Write exactly one short, warm greeting "
            "sentence. Address the person by name ONLY if a name is given to you."
        ),
        tools=[],
        model="haiku",
    ),
}

options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",   # the coordinator's engine
    agents=subagents,            # register our stations
    allowed_tools=["Task"],      # auto-approve Task calls (spawning)
)


async def main():
    prompt = (
        "My name is Enes. Delegate to the greeting-writer agent "
        "to produce a welcome message for me."
    )
    async for message in query(prompt=prompt, options=options):
        if isinstance(message, AssistantMessage):
            # parent_tool_use_id tells us WHO is speaking:
            # None -> the coordinator; an id -> a subagent spawned by that Task call
            speaker = "SUBAGENT" if message.parent_tool_use_id else "COORDINATOR"
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    print(f"[{speaker} -> TOOL] {block.name}")
                    print(f"    input: {block.input}")
                elif isinstance(block, TextBlock):
                    print(f"[{speaker}] {block.text}")
        elif isinstance(message, ResultMessage):
            print(f"[RESULT] cost=${message.total_cost_usd:.4f} | turns={message.num_turns}")


asyncio.run(main())
