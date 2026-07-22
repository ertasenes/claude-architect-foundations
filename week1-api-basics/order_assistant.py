import anthropic

client = anthropic.Anthropic()

tools = [
    {
        "name": "get_customer",
        "description": (
            "Verifies a customer's identity and retrieves their account by email address. "
            "MUST be called first, before any order or refund operation. "
            "Input: the customer's email address. "
            "Returns: customer ID, name, and account status."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "Customer's email address, e.g. 'jane@example.com'",
                }
            },
            "required": ["email"],
        },
    },
    {
        "name": "lookup_order",
        "description": (
            "Retrieves the details of a specific order: status, items, total amount, delivery date. "
            "Use when the customer asks about an order's status or contents. "
            "Input: an order ID like 'ORD-1001'. Do NOT use for refunds — use process_refund for that."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID, e.g. 'ORD-1001'",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "process_refund",
        "description": (
            "Issues a refund for a delivered or shipped order. "
            "Use ONLY when the customer explicitly requests a refund and the order exists. "
            "Requires prior identity verification via get_customer. "
            "Input: the order ID and the reason for the refund."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to refund, e.g. 'ORD-1001'",
                },
                "reason": {
                    "type": "string",
                    "description": "Short reason for the refund, e.g. 'item arrived damaged'",
                },
            },
            "required": ["order_id", "reason"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": (
            "Hands the conversation over to a human support agent. "
            "Use when: the customer explicitly asks for a human, the request falls outside "
            "known policy, or you cannot make meaningful progress. "
            "Input: a structured summary so the human agent has full context "
            "(they cannot see this conversation)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": (
                        "Structured handoff summary: customer ID (if known), the issue, "
                        "what was attempted, and the recommended action."
                    ),
                }
            },
            "required": ["summary"],
        },
    },
    {
        "name": "close_session",
        "description": (
            "Ends the support session. Use ONLY when the customer indicates they are done "
            "(says goodbye, thanks you with no pending request) AND all their issues are resolved. "
            "Do not use if any request is still in progress. Input: a one-line resolution summary."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "resolution_summary": {
                    "type": "string",
                    "description": "One line describing how the session ended, e.g. 'refund issued for ORD-1001'",
                }
            },
            "required": ["resolution_summary"],
        },
    },
]

CUSTOMERS = {
    "jane@example.com": {"customer_id": "CUST-42", "name": "Jane Doe", "account_status": "active"},
}

ORDERS = {
    "ORD-1001": {"status": "shipped", "total": 89.90, "items": ["wireless mouse"], "estimated_delivery": "2026-07-24"},
    "ORD-1002": {"status": "processing", "total": 249.00, "items": ["mechanical keyboard"], "estimated_delivery": "2026-07-28"},
}

# --- Session state for the programmatic prerequisite ---
session = {"verified_customer_id": None, "closed": False}


def get_customer(email):
    customer = CUSTOMERS.get(email)
    if customer is None:
        return f"No customer found with email '{email}'."
    session["verified_customer_id"] = customer["customer_id"]
    return (
        f"Customer verified. ID: {customer['customer_id']}, "
        f"Name: {customer['name']}, Account: {customer['account_status']}."
    )


def lookup_order(order_id):
    order = ORDERS.get(order_id)
    if order is None:
        return f"No order found with ID '{order_id}'."
    return (
        f"Order {order_id}: status={order['status']}, items={order['items']}, "
        f"total=${order['total']}, estimated delivery: {order['estimated_delivery']}."
    )


def process_refund(order_id, reason):
    # PROGRAMMATIC PREREQUISITE: refuse unless identity was verified in this session.
    # This is enforced in CODE, not in the prompt — deterministic, not probabilistic.
    if session["verified_customer_id"] is None:
        return (
            "BLOCKED: identity not verified. "
            "Call get_customer with the customer's email before processing any refund."
        )
    order = ORDERS.get(order_id)
    if order is None:
        return f"No order found with ID '{order_id}'."
    return (
        f"Refund of ${order['total']} issued for {order_id} "
        f"(customer {session['verified_customer_id']}). Reason: {reason}."
    )


def escalate_to_human(summary):
    return f"Escalation ticket created. Handoff summary delivered to human agent: {summary}"

def close_session(resolution_summary):
    session["closed"] = True
    return f"Session closed. Resolution: {resolution_summary}"

TOOL_FUNCTIONS = {
    "get_customer": get_customer,
    "lookup_order": lookup_order,
    "process_refund": process_refund,
    "escalate_to_human": escalate_to_human,
    "close_session": close_session,
}

SYSTEM_PROMPT = (
    "You are a customer support agent for an online electronics store. "
    "Verify the customer's identity with get_customer before order or refund operations. "
    "Escalate to a human when the customer explicitly asks for one, when policy does not "
    "cover their request, or when you cannot make progress. Be concise and friendly."
)


def run_agent(messages):
    while True:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1000,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            # Exit unconditionally: end_turn means the turn is over,
            # whether or not the response contains a text block.
            for block in response.content:
                if block.type == "text":
                    return block.text
            return ""  # no text block — return empty instead of looping forever

        if response.stop_reason == "tool_use":
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    print(f"[loop] {block.name}({block.input})")
                    function = TOOL_FUNCTIONS[block.name]
                    result = function(**block.input)
                    print(f"[loop]   -> {result}")
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})


# --- Interactive chat: type messages, 'quit' to exit ---
messages = []
print("Order Assistant ready. Type 'quit' to exit.")
while True:
    user_input = input("\nYou: ")
    if user_input.strip().lower() == "quit":
        break
    messages.append({"role": "user", "content": user_input})
    answer = run_agent(messages)
    if answer:    
        print(f"\nAssistant: {answer}")
    if session["closed"]:
        print("\n[session ended by assistant]")
        break
