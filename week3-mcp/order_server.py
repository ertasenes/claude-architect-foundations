"""Our first standalone MCP server: order-support.
Runs as its OWN process, speaks MCP over stdio.
Carries over lesson 3.2: structured errors + valid empty results."""

import json
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("order-support")

# fake backend (same characters as lesson 3.2)
ORDERS = {
    "7001": {"order": "7001", "status": "shipped", "eta": "2026-07-25"},
    "7002": {"order": "7002", "status": "processing", "eta": None},
}


@mcp.tool()
def lookup_order(order_no: str) -> str:
    """Retrieves the status of a specific order: shipping state and
    expected delivery date. Input is the numeric order number, digits
    only, e.g. '7001'. Do NOT use for account questions."""
    if order_no == "5000":
        # simulate an upstream outage -> raising sets MCP's isError flag
        raise TimeoutError(json.dumps({
            "errorCategory": "transient",
            "isRetryable": True,
            "message": "Order service timeout. Safe to retry once.",
        }))
    order = ORDERS.get(order_no)
    if order is None:
        # NOT an error: valid empty result (lesson 3.2!)
        return json.dumps({
            "found": False,
            "message": "Query succeeded; no order exists with this number.",
        })
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
            "errorCategory": "business",
            "isRetryable": False,
            "message": ("Order already shipped and cannot be cancelled. "
                        "Offer the customer a return instead."),
        }))
    return json.dumps({"cancelled": True, "order": order_no})


@mcp.resource("orders://catalog")
def order_catalog() -> str:
    """Catalog of all known orders (IDs and statuses only) so clients
    can see what data exists WITHOUT exploratory tool calls."""
    listing = [{"order": o["order"], "status": o["status"]}
               for o in ORDERS.values()]
    return json.dumps(listing)


if __name__ == "__main__":
    mcp.run()   # speaks MCP over stdio: reads stdin, writes stdout
