#!/usr/bin/env python3
"""Score an LLM judge against the golden labels.

Input: a JSONL of judge predictions, one per line:
    {"id": "gs-002", "criterion": "factually_grounded", "verdict": "fail"}

Reports, per criterion:
  - agreement with golden labels
  - fail recall: of the turns humans failed, how many the judge caught
  - fail precision: of the turns the judge failed, how many humans also failed

Fail recall matters most for critical criteria: a judge that misses a
hallucinated refund policy is worse than one that flags a few extra turns
for human review.

    python scripts/score_judge.py data/sample_judge_predictions.jsonl
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

from common import load_golden, load_jsonl, load_rubric


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--min-agreement", type=float, default=0.85)
    parser.add_argument("--min-recall-critical", type=float, default=0.95)
    args = parser.parse_args()

    rubric = {c["id"]: c for c in load_rubric()["criteria"]}
    golden = {i["id"]: i["labels"] for i in load_golden()}
    preds = load_jsonl(args.predictions)

    stats = defaultdict(lambda: {"n": 0, "agree": 0, "tp": 0, "fn": 0, "fp": 0})
    misses = []
    for p in preds:
        truth = golden.get(p["id"], {}).get(p["criterion"])
        if truth is None:
            continue
        s = stats[p["criterion"]]
        s["n"] += 1
        s["agree"] += p["verdict"] == truth
        if truth == "fail" and p["verdict"] == "fail":
            s["tp"] += 1
        elif truth == "fail":
            s["fn"] += 1
            misses.append((p["id"], p["criterion"], p["verdict"]))
        elif p["verdict"] == "fail":
            s["fp"] += 1

    print(f"{'criterion':<24}{'sev':>9}{'n':>4}{'agree':>7}{'recall':>8}{'prec':>7}  gate")
    failing = []
    for cid, s in stats.items():
        sev = rubric[cid]["severity"]
        agree = s["agree"] / s["n"]
        recall = s["tp"] / (s["tp"] + s["fn"]) if s["tp"] + s["fn"] else float("nan")
        prec = s["tp"] / (s["tp"] + s["fp"]) if s["tp"] + s["fp"] else float("nan")
        ok = agree >= args.min_agreement
        if sev == "critical" and recall == recall:  # skip nan
            ok = ok and recall >= args.min_recall_critical
        if not ok:
            failing.append(cid)
        print(f"{cid:<24}{sev:>9}{s['n']:>4}{agree:>7.0%}{recall:>8.0%}{prec:>7.0%}"
              f"  {'ok' if ok else 'NOT READY'}")

    if misses:
        print("\nMissed fails (send to human review, then fix the judge prompt):")
        for iid, cid, verdict in misses:
            print(f"  {iid}  {cid:<22} judge said {verdict}")
    print("\nResult:", "judge ready" if not failing
          else f"not ready on {', '.join(failing)}")
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
