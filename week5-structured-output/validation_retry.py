"""Lesson 5.4 - Validation-retry loops and their ceiling.

Arm A: a v1 schema plus a Pydantic validator, wrapped in a retry loop that
feeds the exact validation errors back to the model (max 3 attempts).

Three documents, three intended outcomes:
  doc1: format-only violation      -> retry SHOULD fix it
  doc2: source data conflicts      -> retry CANNOT fix it (document is wrong)
  doc3: required info is absent    -> retry CANNOT fix it (nothing to find)

Arm B: a v2 schema that renders retries unnecessary for doc2 and doc3 by
capturing stated vs calculated values, a conflict flag, and nullable dates.
"""

import json
import os
from datetime import date

from anthropic import Anthropic
from pydantic import BaseModel, ValidationError, field_validator, model_validator

client = Anthropic()
MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")
MAX_ATTEMPTS = 3

DOCS = [
    (
        "doc1_format_only",
        """Fatura No: FTR-2026-0201
ACME Teknoloji Ltd. Sti.
Duzenlenme: 05.02.2026 - Vade: 07.03.2026
Kalemler:
  Bulut depolama aboneligi ......... 800,00 TL
  Teknik destek paketi ............. 200,00 TL
GENEL TOPLAM: 1.000,00 TL""",
    ),
    (
        "doc2_source_conflict",
        """Fatura No: FTR-2026-0202
ACME Teknoloji Ltd. Sti.
Duzenlenme: 06.02.2026 - Vade: 08.03.2026
Kalemler:
  Lisans yenileme .................. 450,00 TL
  Kurulum hizmeti .................. 300,00 TL
GENEL TOPLAM: 800,00 TL""",
    ),
    (
        "doc3_no_due_date",
        """Fatura No: FTR-2026-0203
ACME Teknoloji Ltd. Sti.
Duzenlenme: 07.02.2026
Kalemler:
  Danismanlik hizmeti .............. 600,00 TL
GENEL TOPLAM: 600,00 TL""",
    ),
]


# ----- The auditor: Pydantic model with semantic rules -----

class LineItem(BaseModel):
    """A single billed line with its own amount."""

    name: str
    amount: float


class InvoiceV1(BaseModel):
    """Validated invoice. Enforces rules a JSON schema cannot express."""

    invoice_number: str
    description_slug: str
    line_items: list[LineItem]
    total_amount: float
    issue_date: date
    due_date: date

    @field_validator("description_slug")
    @classmethod
    def slug_must_be_kebab_case(cls, value: str) -> str:
        """Reject anything other than lowercase letters, digits and hyphens."""
        if not all(char.islower() or char.isdigit() or char == "-" for char in value):
            raise ValueError(
                "must be lowercase kebab-case: only a-z, 0-9 and '-' are allowed"
            )
        return value

    @model_validator(mode="after")
    def line_items_must_sum_to_total(self) -> "InvoiceV1":
        """Semantic rule: the parts must add up to the whole."""
        computed = round(sum(item.amount for item in self.line_items), 2)
        if abs(computed - self.total_amount) > 0.01:
            raise ValueError(
                f"line items sum to {computed} but total_amount is "
                f"{self.total_amount}"
            )
        return self

    @model_validator(mode="after")
    def due_date_must_follow_issue_date(self) -> "InvoiceV1":
        """Semantic rule: a due date copied from the issue date is not a due date."""
        if self.due_date <= self.issue_date:
            raise ValueError("due_date must be strictly later than issue_date")
        return self


TOOL_V1 = {
    "name": "record_invoice_v1",
    "description": "Record invoice fields for validation.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "description_slug": {
                "type": "string",
                "description": "Short identifier derived from the billed service.",
            },
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "amount": {"type": "number"},
                    },
                    "required": ["name", "amount"],
                },
            },
            "total_amount": {
                "type": "number",
                "description": "Grand total (1.000,00 -> 1000.00).",
            },
            "issue_date": {"type": "string", "description": "ISO 8601 YYYY-MM-DD."},
            "due_date": {"type": "string", "description": "ISO 8601 YYYY-MM-DD."},
        },
        "required": [
            "invoice_number",
            "description_slug",
            "line_items",
            "total_amount",
            "issue_date",
            "due_date",
        ],
    },
}


def demo_extract_with_retry(doc: str) -> InvoiceV1 | None:
    """Extract, validate, and on failure re-ask with the exact error text."""
    messages: list[dict] = [{"role": "user", "content": f"Invoice:\n{doc}"}]

    for attempt in range(1, MAX_ATTEMPTS + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=900,
            tools=[TOOL_V1],
            tool_choice={"type": "tool", "name": "record_invoice_v1"},
            messages=messages,
        )
        block = next(b for b in resp.content if b.type == "tool_use")
        try:
            validated = InvoiceV1.model_validate(block.input)
            print(f"  attempt {attempt}: VALID -> {json.dumps(block.input, ensure_ascii=False)}")
            return validated
        except ValidationError as err:
            problems = "; ".join(
                f"{'.'.join(str(part) for part in item['loc']) or 'root'}: {item['msg']}"
                for item in err.errors()
            )
            print(f"  attempt {attempt}: INVALID -> {problems}")
            print(f"    got: {json.dumps(block.input, ensure_ascii=False)}")
            # The failed call and the error travel back as a tool_result (role user).
            messages.append({"role": "assistant", "content": resp.content})
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": (
                                f"Validation failed: {problems}. "
                                "Re-read the source document and call the tool "
                                "again with a corrected extraction."
                            ),
                        }
                    ],
                }
            )

    print(f"  gave up after {MAX_ATTEMPTS} attempts")
    return None


# ----- Arm B: a schema that does not need the retry -----

TOOL_V2 = {
    "name": "record_invoice_v2",
    "description": "Record invoice fields, reporting conflicts instead of hiding them.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {"type": "string"},
            "description_slug": {
                "type": "string",
                "description": (
                    "Lowercase kebab-case identifier from the billed service "
                    "(only a-z, 0-9, '-'). Example: 'bulut-depolama-aboneligi'."
                ),
            },
            "line_items": TOOL_V1["input_schema"]["properties"]["line_items"],
            "stated_total": {
                "type": "number",
                "description": "The grand total exactly as printed in the document.",
            },
            "calculated_total": {
                "type": "number",
                "description": "The sum of the line item amounts you extracted.",
            },
            "conflict_detected": {
                "type": "boolean",
                "description": (
                    "True when stated_total and calculated_total disagree, or when "
                    "the document contradicts itself in any other way."
                ),
            },
            "issue_date": {"type": "string", "description": "ISO 8601 YYYY-MM-DD."},
            "due_date": {
                "type": ["string", "null"],
                "description": (
                    "ISO 8601 YYYY-MM-DD, ONLY if the document states a due date. "
                    "Return null otherwise. Never estimate and never reuse "
                    "issue_date."
                ),
            },
        },
        "required": [
            "invoice_number",
            "description_slug",
            "line_items",
            "stated_total",
            "calculated_total",
            "conflict_detected",
            "issue_date",
            "due_date",
        ],
    },
}


def demo_single_pass_v2(doc: str) -> dict:
    """Extract once with the v2 schema and report the routing decision."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=900,
        tools=[TOOL_V2],
        tool_choice={"type": "tool", "name": "record_invoice_v2"},
        messages=[{"role": "user", "content": f"Invoice:\n{doc}"}],
    )
    data = next(b for b in resp.content if b.type == "tool_use").input

    flags = []
    if data["conflict_detected"] or abs(
        data["stated_total"] - data["calculated_total"]
    ) > 0.01:
        flags.append("TOTALS_CONFLICT -> human review")
    if data["due_date"] is None:
        flags.append("DUE_DATE_ABSENT -> downstream default, not a retry")
    verdict = " | ".join(flags) if flags else "CLEAN -> automatic processing"

    print(f"  slug={data['description_slug']}")
    print(f"  stated={data['stated_total']} calculated={data['calculated_total']} "
          f"conflict={data['conflict_detected']} due_date={data['due_date']}")
    print(f"  VERDICT: {verdict}")
    return data


if __name__ == "__main__":
    print("=" * 70)
    print("ARM A - v1 schema + Pydantic validator + retry loop")
    print("=" * 70)
    for name, doc in DOCS:
        print(f"\n[{name}]")
        demo_extract_with_retry(doc)

    print("\n" + "=" * 70)
    print("ARM B - v2 schema, single pass, no retry")
    print("=" * 70)
    for name, doc in DOCS:
        print(f"\n[{name}]")
        demo_single_pass_v2(doc)

# EXAM TAKEAWAY: retry with specific error feedback fixes FORMAT and STRUCTURAL
# errors. It cannot fix information that is absent from the source, and it must
# not be used to "resolve" a document that contradicts itself - capture stated
# vs calculated values plus a conflict flag and route to human review instead.
