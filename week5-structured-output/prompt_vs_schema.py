"""Lesson 5.1 - Prompt-only JSON vs schema-enforced JSON via tool_use.

Same messy invoice, two arms, three runs each:
  Arm A: ask for JSON in the prompt, then json.loads() the text block.
  Arm B: define an extraction tool whose input_schema IS the target shape,
         force it with tool_choice, read the dict from tool_use.input.
"""

import json
import os

from anthropic import Anthropic

client = Anthropic()
MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")
RUNS = 3

# Deliberately messy: mixed languages, TR decimal comma, prose date, noise lines.
INVOICE = """
ACME Teknoloji Ltd. Sti.
Musteri Hizmetleri: 0212 555 00 00

Fatura No: FTR-2026-0042
Duzenlenme: 15 Ocak 2026 - Son odeme tarihi 30 gun sonra

Aciklama: Bulut depolama aboneligi (yillik)
Ara toplam ......... 1.059,32 TL
KDV (%18) .......... 190,68 TL
GENEL TOPLAM ....... 1.250,00 TL

Odeme yapilmadigi takdirde hizmet askiya alinir.
"""

FIELDS = "invoice_number, vendor_name, total_amount, currency, due_date"


def demo_prompt_only(doc: str) -> None:
    """Arm A: request JSON in natural language and parse the text response."""
    prompt = (
        f"Extract the following fields from this invoice: {FIELDS}.\n"
        "Return the result as JSON.\n\n"
        f"Invoice:\n{doc}"
    )
    for i in range(1, RUNS + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = resp.content[0].text
        print(f"\n--- Arm A / run {i} | stop_reason={resp.stop_reason} ---")
        print("RAW:", repr(raw[:300]))
        try:
            parsed = json.loads(raw)
            print("PARSE: ok")
            print("TYPES:", {k: type(v).__name__ for k, v in parsed.items()})
        except json.JSONDecodeError as err:
            print("PARSE: FAILED ->", err)


# The tool never executes. Its only job is to be a form the model must fill in.
EXTRACT_TOOL = {
    "name": "record_invoice",
    "description": "Record the structured fields of a single invoice.",
    "input_schema": {
        "type": "object",
        "properties": {
            "invoice_number": {
                "type": "string",
                "description": "Invoice identifier exactly as printed.",
            },
            "vendor_name": {
                "type": "string",
                "description": "Legal name of the issuing company.",
            },
            "total_amount": {
                "type": "number",
                "description": (
                    "Grand total as a decimal number. Source may use a comma "
                    "decimal separator and dot thousands separator "
                    "(1.250,00 -> 1250.00). No currency symbol."
                ),
            },
            "currency": {
                "type": "string",
                "enum": ["TRY", "USD", "EUR"],
                "description": "ISO 4217 code inferred from the document.",
            },
            "due_date": {
                "type": "string",
                "description": "Payment due date normalized to ISO 8601 YYYY-MM-DD.",
            },
        },
        "required": ["invoice_number", "vendor_name", "total_amount", "currency", "due_date"],
    },
}


def demo_schema_tool(doc: str) -> None:
    """Arm B: force the extraction tool so the schema constrains the output."""
    for i in range(1, RUNS + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=500,
            tools=[EXTRACT_TOOL],
            tool_choice={"type": "tool", "name": "record_invoice"},
            messages=[{"role": "user", "content": f"Invoice:\n{doc}"}],
        )
        block = next(b for b in resp.content if b.type == "tool_use")
        data = block.input
        print(f"\n--- Arm B / run {i} | stop_reason={resp.stop_reason} ---")
        print("DATA:", json.dumps(data, ensure_ascii=False))
        print("TYPES:", {k: type(v).__name__ for k, v in data.items()})


if __name__ == "__main__":
    print("=" * 60)
    print("ARM A - prompt asks for JSON (guidance)")
    print("=" * 60)
    demo_prompt_only(INVOICE)

    print("\n" + "=" * 60)
    print("ARM B - schema forced via tool_use (lock)")
    print("=" * 60)
    demo_schema_tool(INVOICE)

# EXAM TAKEAWAY: tool_use with a JSON schema is the reliable path to
# schema-compliant output; asking for JSON in the prompt is guidance only.
# Schema eliminates syntax errors, not semantic ones (5.4 handles those).
