"""Lesson 5.5 - Vague confidence language vs explicit categorical criteria.

Arm A: "be conservative, only report high-confidence issues" - a stance.
Arm B: an explicit REPORT list and an explicit SKIP list - a specification.

Same file, same schema, same model. The metric is precision: how many findings
land on the three planted defects versus the three innocuous patterns.
"""

import json
import os
from pathlib import Path

from anthropic import Anthropic

client = Anthropic()
MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")

TARGET = Path(__file__).with_name("review_target.py")

REVIEW_TOOL = {
    "name": "report_findings",
    "description": "Report code review findings for a single file.",
    "input_schema": {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "function_name": {"type": "string"},
                        "severity": {
                            "type": "string",
                            "enum": ["critical", "major", "minor"],
                        },
                        "issue": {
                            "type": "string",
                            "description": "One sentence describing the problem.",
                        },
                        "detected_pattern": {
                            "type": "string",
                            "description": (
                                "The code construct that triggered this finding, "
                                "e.g. 'f-string in SQL', 'unguarded list index', "
                                "'single-letter variable'. Used to analyse "
                                "dismissal patterns later."
                            ),
                        },
                    },
                    "required": [
                        "function_name",
                        "severity",
                        "issue",
                        "detected_pattern",
                    ],
                },
            }
        },
        "required": ["findings"],
    },
}

VAGUE = """You are a code reviewer. Report issues you find in the file.
Be conservative and only report high-confidence findings.
Avoid nitpicking."""

EXPLICIT = """You are a code reviewer. Apply these criteria literally.

REPORT ONLY these categories:
1. Injection risk: user-controlled values concatenated or interpolated into SQL,
   shell commands, or file paths.
2. Docstring-code contract violation: the docstring states a behaviour the code
   does not implement. Report only when the claim contradicts the code.
3. Unhandled runtime failure on a realistic input: index or key access with no
   guard for the empty or missing case.

DO NOT REPORT, regardless of preference:
- Formatting, naming, or style (variable length, quote style, .format vs f-string)
- Magic numbers whose meaning is clear from the function name or context
- Missing type hints, missing docstrings, or docstring wording
- Performance of code that is not in a hot path
- Suggestions to use a different library or idiom

Severity: critical = exploitable or data-corrupting; major = incorrect results
or crash on realistic input; minor = correct but fragile."""


def demo_review(label: str, system_prompt: str, source: str) -> list[dict]:
    """Run one review arm and print its findings."""
    resp = client.messages.create(
        model=MODEL,
        max_tokens=1500,
        system=system_prompt,
        tools=[REVIEW_TOOL],
        tool_choice={"type": "tool", "name": "report_findings"},
        messages=[{"role": "user", "content": f"Review this file:\n\n{source}"}],
    )
    findings = next(b for b in resp.content if b.type == "tool_use").input["findings"]

    print(f"\n{'=' * 70}\n{label} - {len(findings)} finding(s)\n{'=' * 70}")
    for item in findings:
        print(
            f"  [{item['severity']:<8}] {item['function_name']:<22} "
            f"{item['issue']}"
        )
        print(f"             pattern: {item['detected_pattern']}")
    return findings


REAL_DEFECT_FUNCS = {"get_user_orders", "apply_discount", "get_primary_address"}
INNOCUOUS_FUNCS = {"format_currency", "summarize_totals", "is_weekend"}


def demo_score(label: str, findings: list[dict]) -> None:
    """Score an arm on precision against the planted defects."""
    hits = {f["function_name"] for f in findings} & REAL_DEFECT_FUNCS
    false_pos = [f for f in findings if f["function_name"] in INNOCUOUS_FUNCS]
    print(
        f"\n{label}: caught {len(hits)}/3 real defects "
        f"({', '.join(sorted(hits)) or 'none'}) | "
        f"{len(false_pos)} false positive(s) on innocuous code"
    )
    for item in false_pos:
        print(f"    FP -> {item['function_name']}: {item['detected_pattern']}")


if __name__ == "__main__":
    source = TARGET.read_text()
    vague_findings = demo_review("ARM A - vague ('be conservative')", VAGUE, source)
    explicit_findings = demo_review("ARM B - explicit categorical criteria", EXPLICIT, source)

    print("\n" + "=" * 70)
    print("SCORE")
    print("=" * 70)
    demo_score("Arm A", vague_findings)
    demo_score("Arm B", explicit_findings)

# EXAM TAKEAWAY: "be conservative" and "only high-confidence findings" are a
# stance, not a filter - precision comes from explicit REPORT/SKIP categories.
# detected_pattern makes dismissal patterns analysable so high-FP categories can
# be identified and temporarily disabled while their prompts are improved.
