"""A trap file for the Edit tool: two IDENTICAL lines."""

def calculate_total(items):
    total = 0
    for item in items:
        total = total + item.price      # TODO: apply discount
    return total

def calculate_shipping(items):
    total = 0
    for item in items:
        total = total + item.price * 0.9      # TODO: apply discount
    return total * 0.1

# EXAM TAKEAWAY: The Edit tool needs a unique old_string — identical lines force you to add surrounding context (or replace_all) or the edit is ambiguous and fails.
