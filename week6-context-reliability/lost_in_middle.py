"""Lesson 6.1c - Position effects in long aggregated inputs.

Twelve subagent findings, each carrying one numeric statistic buried in filler
prose. The coordinator is asked to report every statistic.

Arm A: findings concatenated as-is.
Arm B: same findings, but a key-findings index is placed FIRST and every
       section gets an explicit header.

Scored by position bucket (head / middle / tail) to expose the
"lost in the middle" effect rather than just a total.
"""

from anthropic import Anthropic

client = Anthropic()
MODEL = "claude-sonnet-4-5"  # keep in sync with earlier weeks
RUNS = 3

# (finding id, topic, the statistic that must be reported)
FINDINGS = [
    ("F-01", "generative music tools adoption",        "31.4%"),
    ("F-02", "session musician booking volume",        "18,207 sessions"),
    ("F-03", "stock photography licensing revenue",    "412.9 million USD"),
    ("F-04", "voice actor contract duration",          "7.6 weeks"),
    ("F-05", "screenwriting software subscriptions",   "2,846,000 seats"),
    ("F-06", "film post-production turnaround",        "23.8 days"),
    ("F-07", "concept artist hourly rates",            "84.25 USD"),
    ("F-08", "audiobook narration output",             "63,540 hours"),
    ("F-09", "game asset outsourcing spend",           "1.07 billion USD"),
    ("F-10", "editorial illustration commissions",     "9,318 commissions"),
    ("F-11", "translation and localization volume",    "5.4 million words"),
    ("F-12", "advertising storyboard lead time",       "11.2 days"),
]

FILLER = (
    "The analyst reviewed submissions from participating studios and independent "
    "practitioners across several regional markets, noting that methodology "
    "differed between respondents and that self-reported figures were "
    "cross-checked against public filings where available. Interview notes "
    "describe a mixed picture: some respondents welcomed the shift while others "
    "reported pressure on rates and timelines. Commentary in this section is "
    "narrative and should be read alongside the accompanying tables. Additional "
    "context on sampling, response rates and definitional boundaries is recorded "
    "in the appendix material retained by the research team. "
)


def build_finding(fid: str, topic: str, stat: str) -> str:
    return (
        f"{FILLER * 3}"
        f"On {topic}, the measured value for the reporting period was {stat}. "
        f"{FILLER * 3}"
    )


def arm_a() -> str:
    parts = ["AGGREGATED SUBAGENT OUTPUT\n"]
    for fid, topic, stat in FINDINGS:
        parts.append(build_finding(fid, topic, stat))
    return "\n".join(parts)


def arm_b() -> str:
    index = ["KEY FINDINGS INDEX (read this first, one line per finding):"]
    for fid, topic, stat in FINDINGS:
        index.append(f"- {fid} | {topic} | {stat}")
    body = ["", "DETAILED SECTIONS", ""]
    for fid, topic, stat in FINDINGS:
        body.append(f"### {fid} - {topic}")
        body.append(build_finding(fid, topic, stat))
        body.append("")
    return "\n".join(index + body)


QUESTION = (
    "\n\nList every numeric statistic reported above. One line per finding, "
    "formatted as: <finding id or topic> - <statistic>. Do not summarize, do "
    "not skip any, do not add commentary."
)


def ask(payload: str) -> str:
    r = client.messages.create(
        model=MODEL,
        max_tokens=1200,
        messages=[{"role": "user", "content": payload + QUESTION}],
    )
    return r.content[0].text


def score(label: str, texts: list[str]) -> None:
    buckets = {"head (F01-04)": range(0, 4),
               "middle (F05-08)": range(4, 8),
               "tail (F09-12)": range(8, 12)}
    print(f"\n--- {label} ({len(texts)} runs) ---")
    per_finding = []
    for i, (fid, topic, stat) in enumerate(FINDINGS):
        hits = sum(1 for t in texts if stat.lower() in t.lower())
        per_finding.append(hits)
        mark = "OK  " if hits == len(texts) else ("MISS" if hits == 0 else "FLAK")
        print(f"  {mark} {fid} {stat:<22} found in {hits}/{len(texts)} runs")
    for name, rng in buckets.items():
        got = sum(per_finding[i] for i in rng)
        total = len(rng) * len(texts)
        print(f"  {name}: {got}/{total}")
    print(f"  TOTAL: {sum(per_finding)}/{len(FINDINGS) * len(texts)}")


if __name__ == "__main__":
    pa, pb = arm_a(), arm_b()
    print(f"payload sizes: arm A ~{len(pa)} chars, arm B ~{len(pb)} chars")

    a_texts = [ask(pa) for _ in range(RUNS)]
    b_texts = [ask(pb) for _ in range(RUNS)]

    score("ARM A - flat concatenation", a_texts)
    score("ARM B - index first + section headers", b_texts)

    print("\n--- ARM A, run 1 output ---")
    print(a_texts[0])

# ---------------------------------------------------------------------------
# RESULT (recorded 2026-08): NEGATIVE. Arm A 36/36, Arm B 36/36.
# No position effect appeared, so the mitigation had nothing to fix.
#
# Why the experiment failed to reproduce the effect:
#   1. Scale: ~47k chars is ~12k tokens, roughly 6% of the context window.
#      Attention degradation is a function of how full the window is.
#   2. Task type: this asked for RETRIEVAL ("list every statistic"), which is
#      the most robust task type - the target is unambiguous and the signal
#      contrasts sharply with filler. The guide's wording is "may OMIT findings
#      from middle sections", i.e. failure shows up in SYNTHESIS output, where
#      the model reads a section but leaves it out of its conclusion.
#
# The exam answer is unchanged: place a key-findings summary FIRST and use
# explicit section headers. "Switch to a model with a larger context window"
# remains the wrong answer - window size does not fix attention quality.
# ---------------------------------------------------------------------------
