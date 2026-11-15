"""Shared loaders for the golden-dataset-kit scripts."""
from __future__ import annotations

import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
RUBRIC_PATH = ROOT / "rubric" / "rubric.yaml"
GOLDEN_PATH = ROOT / "data" / "golden_set.jsonl"


def load_rubric() -> dict:
    return yaml.safe_load(RUBRIC_PATH.read_text())


def criteria_ids() -> list[str]:
    return [c["id"] for c in load_rubric()["criteria"]]


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def load_golden() -> list[dict]:
    return load_jsonl(GOLDEN_PATH)
