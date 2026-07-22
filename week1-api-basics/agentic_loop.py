import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "get_order_status",
        "description": (
            "Looks up the current status of a customer order by its order ID. "
            "Use this when the user asks where their order is or when it will arrive. "
            "Input: an order ID string like 'ORD-1001'. "
            "Returns: order status (processing, shipped, delivered) and estimated delivery date."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID provided by the customer, e.g. 'ORD-1001'",
                }
            },
            "required": ["order_id"],
        },
    }
]

ORDERS = {
    "ORD-1001": {"status": "shipped", "estimated_delivery": "2026-07-24"},
    "ORD-1002": {"status": "processing", "estimated_delivery": "2026-07-28"},
}


def get_order_status(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return f"No order found with ID '{order_id}'."
    return f"Status: {order['status']}. Estimated delivery: {order['estimated_delivery']}."


# Maps tool names to the actual Python functions that implement them
TOOL_FUNCTIONS = {
    "get_order_status": get_order_status,
}


def run_agent(user_message):
    messages = [{"role": "user", "content": user_message}]

    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            tools=tools,
            messages=messages,
        )

        # Always append Claude's reply to the history first
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Claude is done — find the text block and return it
            for block in response.content:
                if block.type == "text":
                    return block.text

        if response.stop_reason == "tool_use":
            # Claude may request SEVERAL tools in one response — handle all of them
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"[loop] Claude requested: {block.name}({block.input})")
                    function = TOOL_FUNCTIONS[block.name]
                    result = function(**block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})


answer = run_agent("Where are my orders ORD-1001 and ORD-1002?")
print("---")
print("FINAL ANSWER:", answer)
