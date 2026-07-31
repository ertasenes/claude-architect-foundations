"""Lesson 5.3 - Few-shot examples for ambiguous classification.

Same schema, same documents, two arms:
  Arm 1: schema + a short prose instruction.
  Arm 2: schema + three few-shot examples that carry the REASONING for the
         call, not just the answer.

Each document is run twice per arm: the metric is consistency, not just
correctness. Documents are deliberately borderline.
"""

import json
import os

from anthropic import Anthropic

client = Anthropic()
MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")
RUNS = 2

DOCS = [
    (
        "A_proforma",
        """TEKLIF / PROFORMA FATURA
Belge No: TKF-2026-0111
ACME Teknoloji Ltd. Sti.
Gecerlilik: 30 gun
Toplam: 12.500,00 TL
Bu belge odeme yukumlulugu dogurmaz.""",
    ),
    (
        "B_no_header",
        """ACME Teknoloji Ltd. Sti.
Belge No: 2026/0112
Tarih: 22.01.2026 - Vade: 21.02.2026
Bulut depolama aboneligi
KDV dahil toplam: 3.400,00 TL
Odeme icin banka bilgileri asagidadir.""",
    ),
    (
        "C_receipt_with_invoice_no",
        """ODEME BILDIRIMI
Ilgili fatura: FTR-2026-0098
ACME Teknoloji Ltd. Sti.
22.01.2026 tarihinde 3.400,00 TL tahsil edilmistir.
Bakiye: 0,00 TL""",
    ),
]

CLASSIFY_TOOL = {
    "name": "classify_document",
    "description": "Classify a financial document and record why.",
    "input_schema": {
        "type": "object",
        "properties": {
            "document_type": {
                "type": "string",
                "enum": ["invoice", "quote", "receipt", "other"],
            },
            "document_type_detail": {
                "type": ["string", "null"],
                "description": "Verbatim wording when document_type is 'other'.",
            },
            "reasoning": {
                "type": "string",
                "description": "One sentence: the decisive signal for this call.",
            },
        },
        "required": ["document_type", "document_type_detail", "reasoning"],
    },
}

PROSE_ONLY = (
    "Classify the document type accurately. Be careful with ambiguous documents."
)

FEW_SHOT = """Classify the document type. Decide on PAYMENT OBLIGATION, not on the title.

Example 1
Document: "SIPARIS ONAYI - Belge No SO-88 - Toplam 5.000 TL - Sevkiyat sonrasi
fatura duzenlenecektir."
Call: document_type="quote", detail=null,
reasoning="States an invoice will be issued later, so no payment obligation exists yet; the title is irrelevant."

Example 2
Document: "ACME Ltd. - Belge No 2026/044 - Vade 15.03.2026 - Toplam 900 TL -
Odeme banka hesabina yapilacaktir."
Call: document_type="invoice", detail=null,
reasoning="A due date plus payment instructions create a payment obligation, even with no 'fatura' heading."

Example 3
Document: "TAHSILAT MAKBUZU - Ilgili belge 2026/031 - 900 TL alinmistir -
Bakiye 0 TL."
Call: document_type="receipt", detail=null,
reasoning="Confirms money already collected and a zero balance; the referenced number belongs to another document."
"""


def demo_classify(system_prompt: str, doc: str) -> dict:
    """Force the classification tool once under a given system prompt."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=400,
        system=system_prompt,
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_document"},
        messages=[{"role": "user", "content": f"Document:\n{doc}"}],
    )
    return next(b for b in resp.content if b.type == "tool_use").input


def demo_compare_arms() -> None:
    """Run both prompting strategies over every document, twice each."""
    for name, doc in DOCS:
        print("\n" + "=" * 68)
        print(name)
        print("=" * 68)
        for label, system_prompt in (("prose   ", PROSE_ONLY), ("few-shot", FEW_SHOT)):
            for i in range(1, RUNS + 1):
                data = demo_classify(system_prompt, doc)
                print(
                    f"{label} r{i}: {data['document_type']:<8} "
                    f"| {data['reasoning']}"
                )


if __name__ == "__main__":
    demo_compare_arms()

# EXAM TAKEAWAY: few-shot examples are the strongest tool for AMBIGUOUS cases
# and format consistency - not for schema compliance (that is the schema's job).
# Examples must show the reasoning behind the call so the model generalizes to
# novel patterns instead of pattern-matching the listed cases.
