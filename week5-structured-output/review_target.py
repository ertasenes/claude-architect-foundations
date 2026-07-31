"""Deliberately flawed sample used as review input for lesson 5.5.

Contains three real defects and three innocuous patterns that vague prompts
tend to report as findings. Not imported by anything.
"""

import sqlite3


def get_user_orders(conn: sqlite3.Connection, user_id: str) -> list[tuple]:
    """Return all orders for a user."""
    # REAL DEFECT 1: SQL injection via string interpolation.
    query = f"SELECT * FROM orders WHERE user_id = '{user_id}'"
    return conn.execute(query).fetchall()


def apply_discount(total: float, percent: float) -> float:
    """Apply a percentage discount to a total.

    Caps the discount at 50 percent for safety.
    """
    # REAL DEFECT 2: the docstring promises a 50 percent cap that is not enforced.
    return total - (total * percent / 100)


def get_primary_address(addresses: list[dict]) -> dict:
    """Return the address flagged as primary."""
    # REAL DEFECT 3: IndexError when no address is flagged primary.
    return [a for a in addresses if a.get("is_primary")][0]


def format_currency(amount: float) -> str:
    """Format an amount as Turkish Lira. Innocuous: local helper, no f-string."""
    return "{:,.2f} TL".format(amount)


def summarize_totals(orders: list[dict]) -> dict:
    """Aggregate order totals. Innocuous: single-letter loop var is idiomatic."""
    result = {"count": 0, "sum": 0.0}
    for o in orders:
        result["count"] += 1
        result["sum"] += o["total"]
    return result


def is_weekend(day_index: int) -> bool:
    """Return True for Saturday or Sunday. Innocuous: magic numbers are obvious."""
    return day_index in (5, 6)

# EXAM TAKEAWAY: review input for testing vague vs categorical review criteria.
