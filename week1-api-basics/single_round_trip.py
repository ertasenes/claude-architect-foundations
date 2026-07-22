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

# Fake database: in real life this would be a SQL query or an HTTP request
ORDERS = {
    "ORD-1001": {"status": "shipped", "estimated_delivery": "2026-07-24"},
    "ORD-1002": {"status": "processing", "estimated_delivery": "2026-07-28"},
}


def get_order_status(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return f"No order found with ID '{order_id}'."
    return f"Status: {order['status']}. Estimated delivery: {order['estimated_delivery']}."


# --- Step 1: user asks, Claude writes the tool_use "ticket" ---
messages = [{"role": "user", "content": "Where is my order ORD-1001?"}]

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    tools=tools,
    messages=messages,
)

# --- Step 2: append Claude's reply (the ticket) to the conversation history ---
messages.append({"role": "assistant", "content": response.content})

# --- Step 3: find the tool_use block and run the tool OURSELVES ---
tool_use_block = None
for block in response.content:
    if block.type == "tool_use":
        tool_use_block = block

result = get_order_status(tool_use_block.input["order_id"])
print("TOOL RESULT (what our code produced):", result)

# --- Step 4: send the result back, matched to the ticket by its id ---
messages.append(
    {
        "role": "user",
        "content": [
            {
                "type": "tool_result",
                "tool_use_id": tool_use_block.id,
                "content": result,
            }
        ],
    }
)

# --- Step 5: second API call — Claude now has the info and can answer ---
final_response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    tools=tools,
    messages=messages,
)

print("STOP REASON:", final_response.stop_reason)
print("FINAL ANSWER:", final_response.content[0].text)
