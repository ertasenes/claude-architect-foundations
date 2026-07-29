"""order-support MCP server, final version for Exercise 1:
- structured errors (errorCategory / isRetryable)
- valid empty results
- resource catalog (now consistent: cancel updates the data)
- process_refund with a $500 business-rule gate
- escalate_to_human with a structured handoff summary"""

import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("order-support")

REFUND_LIMIT = 500.00

ORDERS = {
    "7001": {"order": "7001", "status": "shipped", "eta": "2026-07-25",
             "amount": 129.90},
    "7002": {"order": "7002", "status": "processing", "eta": None,
             "amount": 899.00},
}


@mcp.tool()
def lookup_order(order_no: str) -> str:
    """Retrieves the status and amount of a specific order. Input is the
    numeric order number, digits only, e.g. '7001'. Do NOT use for
    account questions or refunds."""
    order = ORDERS.get(order_no)
    if order is None:
        return json.dumps({"found": False,
                           "message": "Query succeeded; no order exists."})
    return json.dumps(order)


@mcp.tool()
def cancel_order(order_no: str) -> str:
    """Cancels an order that has not shipped yet. Input is the numeric
    order number. Shipped orders cannot be cancelled (business rule)."""
    order = ORDERS.get(order_no)
    if order is None:
        return json.dumps({"found": False,
                           "message": "No order exists with this number."})
    if order["status"] == "shipped":
        raise ValueError(json.dumps({
            "errorCategory": "business", "isRetryable": False,
            "message": ("Order already shipped and cannot be cancelled. "
                        "Offer the customer a return instead."),
        }))
    order["status"] = "cancelled"          # fix: keep catalog consistent!
    return json.dumps({"cancelled": True, "order": order_no})


@mcp.tool()
def process_refund(order_no: str, amount: float, reason: str) -> str:
    """Issues a refund for an order. Inputs: numeric order number, refund
    amount in USD, and a short reason. Refunds above 500 USD are NOT
    permitted through this tool (company policy) — for those, use
    escalate_to_human instead."""
    order = ORDERS.get(order_no)
    if order is None:
        return json.dumps({"found": False,
                           "message": "No order exists with this number."})
    if amount > REFUND_LIMIT:
        # server-side lock: holds even if a client connects without hooks
        raise ValueError(json.dumps({
            "errorCategory": "business", "isRetryable": False,
            "message": (f"Refund of ${amount:.2f} exceeds the ${REFUND_LIMIT:.0f} "
                        "autonomous limit. Escalate to a human agent with a "
                        "structured handoff summary."),
        }))
    return json.dumps({"refunded": True, "order": order_no,
                       "amount": amount, "reason": reason})


@mcp.tool()
def escalate_to_human(customer_summary: str, root_cause: str,
                      recommended_action: str) -> str:
    """Hands the case to a human support agent. The human has NO access
    to this conversation, so provide a complete structured handoff:
    customer_summary (who/what order/amounts), root_cause (why the agent
    cannot resolve it), recommended_action (what the human should do)."""
    ticket = {"escalated": True, "ticket_id": "ESC-2201",
              "customer_summary": customer_summary,
              "root_cause": root_cause,
              "recommended_action": recommended_action}
    return json.dumps(ticket)


@mcp.resource("orders://catalog")
def order_catalog() -> str:
    """Catalog of all known orders (IDs and statuses only)."""
    return json.dumps([{"order": o["order"], "status": o["status"]}
                       for o in ORDERS.values()])


if __name__ == "__main__":
    mcp.run()
