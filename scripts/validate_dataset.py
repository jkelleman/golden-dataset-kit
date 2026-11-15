#!/usr/bin/env python3
"""Validate golden_set.jsonl against the rubric and print a coverage report.

Checks every item for:
  - required fields and unique ids
  - final turn is an agent turn (that's what gets graded)
  - a label for every rubric criterion, with a valid value
  - na only where the rubric allows it
  - a rationale for every fail
  - error tags that exist in the rubric

    python scripts/validate_dataset.py
"""
from __future__ import annotations

import sys
from collections import Counter

from common import load_golden, load_rubric

REQUIRED = ["id", "intent", "channel", "locale", "difficulty", "context",
            "conversation", "labels", "rationale", "error_tags", "adjudicated"]
VALID = {"pass", "fail", "na"}


def main() -> int:
    rubric = load_rubric()
    criteria = {c["id"]: c for c in rubric["criteria"]}
    na_forbidden = {cid for cid, c in criteria.items() if c["na"].startswith("Never")}
    all_tags = {t for c in criteria.values() for t in c["error_tags"]}

    items = load_golden()
    errors: list[str] = []
    seen: set[str] = set()

    for item in items:
        iid = item.get("id", "<missing id>")
        for field in REQUIRED:
            if field not in item:
                errors.append(f"{iid}: missing field '{field}'")
        if iid in seen:
            errors.append(f"{iid}: duplicate id")
        seen.add(iid)

        convo = item.get("conversation", [])
        if not convo or convo[-1].get("role") != "agent":
            errors.append(f"{iid}: final turn must be the agent turn being graded")

        labels = item.get("labels", {})
        for cid in criteria:
            value = labels.get(cid)
            if value not in VALID:
                errors.append(f"{iid}: '{cid}' label is {value!r}")
            elif value == "na" and cid in na_forbidden:
                errors.append(f"{iid}: '{cid}' can't be na per rubric")
            elif value == "fail" and not item.get("rationale", {}).get(cid):
                errors.append(f"{iid}: '{cid}' is fail but has no rationale")
        for tag in item.get("error_tags", []):
            if tag not in all_tags:
                errors.append(f"{iid}: unknown error tag '{tag}'")
        if item.get("adjudicated") is not True:
            errors.append(f"{iid}: not adjudicated; golden items must be adjudicated")

    if errors:
        print(f"FAIL: {len(errors)} problem(s)")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(items)} items, {len(criteria)} criteria, all labels valid\n")
    print("Coverage")
    print(f"  channels:     {dict(Counter(i['channel'] for i in items))}")
    print(f"  locales:      {dict(Counter(i['locale'] for i in items))}")
    print(f"  difficulty:   {dict(Counter(i['difficulty'] for i in items))}")
    clean = sum(1 for i in items if "fail" not in i["labels"].values())
    print(f"  clean passes: {clean} of {len(items)}\n")
    print(f"  {'criterion':<24}{'pass':>6}{'fail':>6}{'na':>6}")
    for cid in criteria:
        counts = Counter(i["labels"][cid] for i in items)
        print(f"  {cid:<24}{counts['pass']:>6}{counts['fail']:>6}{counts['na']:>6}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
