#!/usr/bin/env python3
"""Render a single-criterion LLM-judge prompt for one golden item.

One judge per criterion, not one prompt that grades everything. A single
prompt asked to check eight things at once tends to blur them together;
dedicated judges are easier to calibrate and debug.

    python scripts/render_judge_prompt.py --criterion factually_grounded --item gs-002
    python scripts/render_judge_prompt.py --criterion concise --item gs-011 --with-examples
"""
from __future__ import annotations

import argparse
import json
import sys

from common import load_golden, load_rubric

TEMPLATE = """You are grading one turn from an AI customer-support agent for a
streaming service. Judge ONE criterion only. Ignore everything else.

## Criterion: {cid}
Question: {question}
PASS: {pass_}
FAIL: {fail}
NA: {na}
Known failure types: {tags}
{examples}
## What the agent could see (context)
{context}

## Conversation
{conversation}

## Instructions
Grade only the FINAL agent turn, using the conversation and context above.
Base your verdict on the context provided, not on what you believe about any
real company's policies. Quote the specific words that drove your verdict.

Respond with JSON only:
{{"criterion": "{cid}", "verdict": "pass" | "fail" | "na", "error_tag": "<one known failure type or null>", "evidence": "<quoted words>", "rationale": "<one sentence>"}}
"""


def format_conversation(turns: list[dict]) -> str:
    return "\n".join(f"{t['role'].upper()}: {t['text']}" for t in turns)


def few_shot(cid: str, golden: list[dict], exclude: str) -> str:
    """One labeled pass and one labeled fail from the golden set, as examples."""
    out = []
    for verdict in ("fail", "pass"):
        match = next((i for i in golden if i["id"] != exclude
                      and i["labels"].get(cid) == verdict), None)
        if match:
            why = match["rationale"].get(cid, "Meets the pass definition.")
            out.append(f"Example ({verdict.upper()}): "
                       f"AGENT: {match['conversation'][-1]['text']}\n  -> {why}")
    return "\n## Labeled examples\n" + "\n\n".join(out) + "\n" if out else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--criterion", required=True)
    parser.add_argument("--item", required=True)
    parser.add_argument("--with-examples", action="store_true")
    args = parser.parse_args()

    rubric = {c["id"]: c for c in load_rubric()["criteria"]}
    golden = load_golden()
    if args.criterion not in rubric:
        sys.exit(f"Unknown criterion. Choose from: {', '.join(rubric)}")
    item = next((i for i in golden if i["id"] == args.item), None)
    if item is None:
        sys.exit(f"Unknown item {args.item}")

    c = rubric[args.criterion]
    print(TEMPLATE.format(
        cid=c["id"], question=c["question"], pass_=c["pass"], fail=c["fail"],
        na=c["na"], tags=", ".join(c["error_tags"]),
        examples=few_shot(c["id"], golden, item["id"]) if args.with_examples else "",
        context=json.dumps(item["context"], indent=2, ensure_ascii=False),
        conversation=format_conversation(item["conversation"]),
    ))
    return 0


if __name__ == "__main__":
    sys.exit(main())
