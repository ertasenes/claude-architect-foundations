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
    "web-researcher": AgentDefinition(
        description=(
            "Searches the web for ONE specific subtopic and returns findings. "
            "Use one instance per subtopic; instances can run in parallel."
        ),
        prompt=(
            "You are a web researcher. Search the web for the subtopic given to you. "
            "Return exactly 2-3 findings as a structured list. Each finding MUST have: "
            "claim, source_title, source_url, publication_date (or 'unknown'). "
            "Report only what sources say; no analysis of your own."
        ),
        tools=["WebSearch"],
        model="sonnet",
    ),
    "synthesizer": AgentDefinition(
        description=(
            "Combines research findings into a short cited report. Has NO research "
            "tools; works only with findings provided in its prompt."
        ),
        prompt=(
            "You are a synthesis writer. You will receive research findings in your prompt. "
            "Write a short report (max 200 words). Rules: every claim keeps its source "
            "attribution; if findings conflict, present BOTH with sources - never pick one "
            "arbitrarily; do NOT add information beyond the findings given to you."
        ),
        tools=[],
        model="sonnet",
    ),
}

options = ClaudeAgentOptions(
    model="claude-sonnet-4-6",
    system_prompt=(
        "You are a research coordinator. Workflow: "
        "1) Split the topic into exactly 2 distinct subtopics that together cover it well. "
        "2) Spawn one web-researcher per subtopic IN PARALLEL (both Task calls in one response). "
        "3) Pass ALL findings, complete with sources and dates, into the synthesizer's prompt - "
        "it cannot see anything you don't include. "
        "4) Present the synthesizer's report as the final answer."
    ),
    agents=subagents,
    allowed_tools=["Task", "WebSearch"],
)


async def main():
    topic = "the pros and cons of remote work for software teams"
    async for message in query(prompt=f"Research this topic: {topic}", options=options):
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, ToolUseBlock):
                    who = block.input.get("subagent_type", block.name)
                    task = str(block.input.get("prompt", ""))[:120]
                    print(f"[SPAWN] {who}  (ticket ...{block.id[-8:]})")
                    print(f"    task: {task}...")
                elif isinstance(block, TextBlock) and not message.parent_tool_use_id:
                    print(f"[COORDINATOR]\n{block.text}")
        elif isinstance(message, UserMessage):
            blocks = message.content if isinstance(message.content, list) else []
            for block in blocks:
                if isinstance(block, ToolResultBlock):
                    print(f"[RETURN ...{block.tool_use_id[-8:]}] {str(block.content)[:150]}...")
        elif isinstance(message, ResultMessage):
            print(f"\n[RESULT] cost=${message.total_cost_usd:.4f} | turns={message.num_turns}")


asyncio.run(main())
