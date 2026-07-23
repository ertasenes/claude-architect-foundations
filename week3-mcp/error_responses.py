"""Two runs, one flag:
STRUCTURED = True -> every problem returns a generic "Operation failed."
STRUCTURED = True  -> structured errors: errorCategory, isRetryable, message,
                      and 'not found' returned as a VALID EMPTY RESULT.
Watch how the agent's recovery behavior changes. (Exam guide, Task 2.2)"""

import json
import anthropic

STRUCTURED = True   # <-- run once as False, then flip to True

client = anthropic.Anthropic()

# --- fake backend ------------------------------------------------------
CALL_COUNT = {"7001": 0}   # lets us fail on the 1st call, succeed on the 2nd

def backend_lookup(order_no: str):
    if order_no == "7001":
        CALL_COUNT["7001"] += 1
        if CALL_COUNT["7001"] == 1:
            raise TimeoutError("upstream order service timed out after 5s")
        return {"order": "7001", "status": "shipped", "eta": "2026-07-25"}
    if order_no == "9999":
        return None            # order simply does not exist
    return {"order": order_no, "status": "processing"}

# --- tool result builder: THE WHOLE LESSON LIVES HERE ------------------
def run_tool(order_no: str):
    """Returns (content_string, is_error_flag) for the tool_result block."""
    try:
        result = backend_lookup(order_no)
    except TimeoutError as exc:
        if not STRUCTURED:
            return "Operation failed.", True                # red lamp
        return json.dumps({
            "errorCategory": "transient",
            "isRetryable": True,
            "message": f"Order service timeout: {exc}. Safe to retry once.",
        }), True

    if result is None:                                      # not found
        if not STRUCTURED:
            return "Operation failed.", True                # same red lamp!
        return json.dumps({                                 # NOT an error:
            "found": False,                                 # valid empty result
            "message": "Query succeeded; no order exists with this number.",
        }), False

    return json.dumps(result), False                        # normal success

# --- tools + agentic loop (week 1 skeleton) ----------------------------
TOOLS = [{
    "name": "lookup_order",
    "description": (
        "Retrieves the status of a specific order. Input is the numeric "
        "order number, digits only, e.g. '12345'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {"order_no": {"type": "string"}},
        "required": ["order_no"],
    },
}]

messages = [{"role": "user",
             "content": "Please check the status of my orders #7001 and #9999."}]

for step in range(6):                       # safety net only, NOT the stop logic
    response = client.messages.create(
        system="If a tool result reports a transient, retryable error, retry the same tool call once immediately without asking the user.",
        model="claude-sonnet-4-6",
        max_tokens=1000,
        tools=TOOLS,
        messages=messages,
    )
    messages.append({"role": "assistant", "content": response.content})

    if response.stop_reason == "end_turn":  # real stop condition
        for block in response.content:
            if block.type == "text":
                print(f"\n[FINAL ANSWER]\n{block.text}")
        break

    tool_results = []
    for block in response.content:
        if block.type == "tool_use":
            content, is_err = run_tool(block.input["order_no"])
            print(f"[TOOL] lookup_order({block.input['order_no']}) "
                  f"-> is_error={is_err} | {content}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": content,
                "is_error": is_err,
            })
    messages.append({"role": "user", "content": tool_results})
