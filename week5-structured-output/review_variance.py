"""Lesson 5.5 round 2 - consistency of vague vs categorical criteria.

Round 1 used unambiguous defects and both arms scored identically. This round
uses borderline patterns and runs each arm three times. The metric is variance:
finding count per run, which functions get flagged, and severity stability.
"""

import os
from collections import Counter
from pathlib import Path

from anthropic import Anthropic

client = Anthropic()
MODEL = os.environ.get("MODEL", "claude-sonnet-4-5")
RUNS = 3

TARGET = Path(__file__).with_name("review_target_v2.py")

from review_criteria import REVIEW_TOOL  # reuse the schema from round 1

VAGUE = """You are a code reviewer. Report issues you find in the file.
Be conservative and only report high-confidence findings.
Avoid nitpicking."""

EXPLICIT = """You are a code reviewer. Apply these criteria literally.

REPORT ONLY these categories:
1. Injection risk: user-controlled values interpolated into SQL, shell commands,
   or file paths.
2. Silent data corruption: a fallback value that is indistinguishable from a
   legitimate result (e.g. returning 0.0 for unparseable input that a caller
   will treat as a real amount).
3. Unhandled runtime failure on a realistic input.
4. Error suppression that hides a class of failures with no signal to the caller
   or logs.

DO NOT REPORT, regardless of preference:
- Style, naming, formatting, or idiom preferences (os.path.join vs concatenation,
  f-string vs .format)
- Mutable default arguments that are never mutated in the function body
- Hardcoded tolerances or constants whose value is clear from context
- TODO comments in functions that are documented as incomplete
- Missing type hints or docstring wording
- Performance of code that is not in a hot path

Severity: critical = exploitable or data-corrupting; major = incorrect results
or crash on realistic input; minor = correct but fragile."""


def demo_run_arm(label: str, system_prompt: str, source: str) -> None:
    """Run one arm RUNS times and summarise the spread."""
    print(f"\n{'=' * 72}\n{label}\n{'=' * 72}")
    counts: list[int] = []
    flagged = Counter()
    severities: dict[str, set] = {}

    for run in range(1, RUNS + 1):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1800,
            system=system_prompt,
            tools=[REVIEW_TOOL],
            tool_choice={"type": "tool", "name": "report_findings"},
            messages=[{"role": "user", "content": f"Review this file:\n\n{source}"}],
        )
        findings = next(b for b in resp.content if b.type == "tool_use").input["findings"]
        counts.append(len(findings))
        names = []
        for item in findings:
            func = item["function_name"]
            flagged[func] += 1
            severities.setdefault(func, set()).add(item["severity"])
            names.append(f"{func}({item['severity'][:3]})")
        print(f"  run {run}: {len(findings)} -> {', '.join(names)}")

    print(f"\n  finding count per run: {counts} (spread {min(counts)}-{max(counts)})")
    print("  flagged in n/3 runs:")
    for func, hits in flagged.most_common():
        unstable = " <-- SEVERITY UNSTABLE" if len(severities[func]) > 1 else ""
        print(f"    {func:<20} {hits}/3  severities={sorted(severities[func])}{unstable}")


if __name__ == "__main__":
    source = TARGET.read_text()
    demo_run_arm("ARM A - vague ('be conservative')", VAGUE, source)
    demo_run_arm("ARM B - explicit categorical criteria", EXPLICIT, source)

# EXAM TAKEAWAY: with borderline patterns, vague criteria produce run-to-run
# variance in both which findings appear and how they are graded. Categorical
# REPORT/SKIP lists plus concrete severity definitions produce a stable, and
# therefore trustworthy, review surface.
