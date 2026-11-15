#!/usr/bin/env python3
"""Inter-annotator agreement for a labeling round.

Input: a CSV with columns item_id, criterion, annotator_a, annotator_b
(values pass / fail / na). Output: percent agreement and Cohen's kappa per
criterion, plus an adjudication queue of every disagreement.

    python scripts/agreement.py data/annotations_round1.csv
    python scripts/agreement.py data/annotations_round1.csv --queue out.csv

Reading the results: kappa corrects for agreement you'd get by chance.
Rough guide: > 0.8 strong, 0.6-0.8 substantial, < 0.6 means the criterion
definition or examples need work before you trust labels (or a judge) on it.
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter, defaultdict
from pathlib import Path


def cohens_kappa(pairs: list[tuple[str, str]]) -> float:
    n = len(pairs)
    if n == 0:
        return float("nan")
    observed = sum(a == b for a, b in pairs) / n
    count_a = Counter(a for a, _ in pairs)
    count_b = Counter(b for _, b in pairs)
    labels = set(count_a) | set(count_b)
    expected = sum((count_a[l] / n) * (count_b[l] / n) for l in labels)
    if expected == 1:
        return 1.0
    return (observed - expected) / (1 - expected)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--queue", type=Path, help="write disagreements to this CSV")
    parser.add_argument("--min-kappa", type=float, default=0.6)
    args = parser.parse_args()

    by_criterion: dict[str, list[tuple[str, str]]] = defaultdict(list)
    disagreements = []
    with args.csv_path.open() as f:
        for row in csv.DictReader(f):
            a, b = row["annotator_a"].strip(), row["annotator_b"].strip()
            by_criterion[row["criterion"]].append((a, b))
            if a != b:
                disagreements.append(row)

    print(f"{'criterion':<24}{'n':>4}{'agree':>8}{'kappa':>8}  status")
    weak = []
    for crit, pairs in by_criterion.items():
        agree = sum(a == b for a, b in pairs) / len(pairs)
        kappa = cohens_kappa(pairs)
        status = "ok" if kappa >= args.min_kappa else "REVISE DEFINITION"
        if kappa < args.min_kappa:
            weak.append(crit)
        print(f"{crit:<24}{len(pairs):>4}{agree:>8.0%}{kappa:>8.2f}  {status}")

    total = sum(len(p) for p in by_criterion.values())
    print(f"\n{len(disagreements)} disagreement(s) out of {total} labels")
    if weak:
        print(f"Criteria below kappa {args.min_kappa}: {', '.join(weak)}")

    if args.queue:
        with args.queue.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["item_id", "criterion",
                                                   "annotator_a", "annotator_b"])
            writer.writeheader()
            for row in disagreements:
                writer.writerow({k: row[k] for k in writer.fieldnames})
        print(f"Adjudication queue written to {args.queue}")
    else:
        for row in disagreements:
            print(f"  {row['item_id']}  {row['criterion']:<22} "
                  f"A={row['annotator_a']:<5} B={row['annotator_b']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
