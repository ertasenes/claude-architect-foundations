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

response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1000,
    tools=tools,
    messages=[{"role": "user", "content": "Where is my order ORD-1001?"}],
)

print("STOP REASON:", response.stop_reason)
print("---")
for block in response.content:
    print(block)
