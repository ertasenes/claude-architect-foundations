"""Borderline review input for lesson 5.5 round 2.

One unambiguous defect (SQL injection) as a control, plus six patterns that sit
on the boundary: defensible in context, reportable if the reviewer is fishing.
"""

import os
import sqlite3
import time


def find_orders(conn: sqlite3.Connection, status: str) -> list[tuple]:
    """CONTROL DEFECT: interpolated SQL."""
    return conn.execute(f"SELECT * FROM orders WHERE status = '{status}'").fetchall()


def load_config(path: str, defaults: dict = {}) -> dict:
    """BORDERLINE 1: mutable default argument, never mutated in this body."""
    config = dict(defaults)
    if os.path.exists(path):
        with open(path) as handle:
            for line in handle:
                key, _, value = line.partition("=")
                config[key.strip()] = value.strip()
    return config


def retry_fetch(fetcher, attempts: int = 3) -> dict:
    """BORDERLINE 2: bare except swallows everything, but returns a fallback."""
    for _ in range(attempts):
        try:
            return fetcher()
        except:
            time.sleep(1)
    return {"status": "unavailable"}


def totals_match(a: float, b: float) -> bool:
    """BORDERLINE 3: float equality via subtraction with a hardcoded epsilon."""
    return abs(a - b) < 0.01


def build_report_path(base: str, name: str) -> str:
    """BORDERLINE 4: string concat for a path instead of os.path.join."""
    return base + "/" + name + ".csv"


def parse_amount(raw: str) -> float:
    """BORDERLINE 5: silent 0.0 fallback hides malformed input."""
    try:
        return float(raw.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def notify(user_id: str, message: str) -> None:
    """BORDERLINE 6: TODO left in place; function is a documented no-op."""
    # TODO: wire this to the notification service before launch
    print(f"[notify:{user_id}] {message}")

# EXAM TAKEAWAY: borderline patterns are where vague and categorical criteria
# diverge - unambiguous defects are caught by either prompt.
