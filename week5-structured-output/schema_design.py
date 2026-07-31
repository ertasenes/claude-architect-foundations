"""Lesson 5.2 - Schema design that prevents fabrication.

Same three documents through two schemas:
  v1 STRICT: every field required, closed enum, no escape hatch.
  v2 SAFE:   nullable fields for possibly-absent data, enum + "other" + detail.

Doc 2 has no due date at all. Doc 3 uses a payment method outside the enum.
Watch what v1 invents to satisfy its own required list.
"""

import json
import os

from anthropic import Anthropic

client = Anthropic()
MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")

DOCS = [
    (
        "doc1_complete",
        """Fatura No: FTR-2026-0042
ACME Teknoloji Ltd. Sti.
Duzenlenme: 15 Ocak 2026 - Son odeme tarihi 30 gun sonra
Odeme sekli: Banka havalesi
GENEL TOPLAM: 1.250,00 TL""",
    ),
    (
        "doc2_no_due_date",
        """Fatura No: FTR-2026-0043
ACME Teknoloji Ltd. Sti.
Duzenlenme: 20 Ocak 2026
Odeme sekli: Kredi karti
GENEL TOPLAM: 480,00 TL""",
    ),
    (
        "doc3_unlisted_method",
        """Fatura No: FTR-2026-0044
ACME Teknoloji Ltd. Sti.
Duzenlenme: 22 Ocak 2026 - Vade: 05.02.2026
Odeme sekli: Papara hesabina transfer
GENEL TOPLAM: 95,00 EUR""",
    ),
]

BASE_PROPS = {
    "invoice_number": {"type": "string"},
    "total_amount": {
        "type": "number",
        "description": "Grand total as a decimal number (1.250,00 -> 1250.00).",
    },
    "currency": {"type": "string", "enum": ["TRY", "USD", "EUR"]},
}

SCHEMA_STRICT = {
    "name": "record_invoice_v1",
    "description": "Record invoice fields. Version 1: all fields mandatory.",
    "input_schema": {
        "type": "object",
        "properties": {
            **BASE_PROPS,
            "due_date": {
                "type": "string",
                "description": "Payment due date as ISO 8601 YYYY-MM-DD.",
            },
            "payment_method": {
                "type": "string",
                "enum": ["bank_transfer", "credit_card", "cash"],
            },
        },
        "required": [
            "invoice_number",
            "total_amount",
            "currency",
            "due_date",
            "payment_method",
        ],
    },
}

SCHEMA_SAFE = {
    "name": "record_invoice_v2",
    "description": "Record invoice fields. Version 2: absent data stays absent.",
    "input_schema": {
        "type": "object",
        "properties": {
            **BASE_PROPS,
            "due_date": {
                "type": ["string", "null"],
                "description": (
                    "Payment due date as ISO 8601 YYYY-MM-DD, ONLY if the document "
                    "states or defines it. Return null if the document does not "
                    "state a due date. Never estimate or infer a default term."
                ),
            },
            "payment_method": {
                "type": "string",
                "enum": ["bank_transfer", "credit_card", "cash", "other"],
                "description": (
                    "Use 'other' when the stated method does not match a listed "
                    "value, and put the literal wording in payment_method_detail."
                ),
            },
            "payment_method_detail": {
                "type": ["string", "null"],
                "description": (
                    "Verbatim payment method wording from the document when "
                    "payment_method is 'other'. Otherwise null."
                ),
            },
        },
        "required": [
            "invoice_number",
            "total_amount",
            "currency",
            "due_date",
            "payment_method",
            "payment_method_detail",
        ],
    },
}


def demo_extract(tool: dict, doc: str) -> dict:
    """Force one extraction tool on one document and return its input dict."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=500,
        tools=[tool],
        tool_choice={"type": "tool", "name": tool["name"]},
        messages=[{"role": "user", "content": f"Invoice:\n{doc}"}],
    )
    block = next(b for b in resp.content if b.type == "tool_use")
    return block.input


def demo_compare_schemas() -> None:
    """Run both schemas over every document and print them side by side."""
    for name, doc in DOCS:
        print("\n" + "=" * 64)
        print(name)
        print("=" * 64)
        for label, tool in (("v1 STRICT", SCHEMA_STRICT), ("v2 SAFE  ", SCHEMA_SAFE)):
            data = demo_extract(tool, doc)
            print(f"{label}: {json.dumps(data, ensure_ascii=False)}")


if __name__ == "__main__":
    demo_compare_schemas()

# EXAM TAKEAWAY: mark fields nullable when the source may not contain them -
# a required field with no escape hatch pushes the model to fabricate a
# plausible value. Use enum + "other" + a detail string for extensible
# categories instead of forcing real-world values into a closed list.
