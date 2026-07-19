"""Byte and schema pins for the reviewer-ratified warehouse corpus."""

from __future__ import annotations

import hashlib
import json
import pathlib
from collections import Counter
from typing import Any

_PATH = pathlib.Path(__file__).resolve().parents[1] / "golden" / "queries.jsonl"
_SHA256 = "14f2d87573ba744029b91768e76ec381ba8caf6a6fa19d67fa2d91235da917dd"
_COUNTS = {"golden": 10, "adversarial": 5, "refusal": 5, "trigger_pos": 3, "trigger_neg": 3}


def _cases() -> list[dict[str, Any]]:
    return [json.loads(line) for line in _PATH.read_text(encoding="utf-8").splitlines()]


def test_corpus_is_byte_identical_to_the_ratified_draft() -> None:
    assert hashlib.sha256(_PATH.read_bytes()).hexdigest() == _SHA256


def test_corpus_shape_and_distribution_are_closed() -> None:
    cases = _cases()
    assert len(cases) == 26
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert Counter(case["kind"] for case in cases) == _COUNTS
    assert sum(bool(case["holdout"]) for case in cases) == 3
    assert all(case["case_id"].startswith("sh-") for case in cases)


def test_trigger_cases_are_routing_contracts() -> None:
    triggers = [case for case in _cases() if case["kind"].startswith("trigger_")]
    assert len(triggers) == 6
    assert all(case["reference_sql"] is None for case in triggers)


def test_sh_104_remains_the_open_judge_scored_exception() -> None:
    case = next(case for case in _cases() if case["case_id"] == "sh-104")
    assert case["scoring"] == "judge"
    assert case["holdout"] is True
    assert "one deliberate exception to result-only scoring" in case["notes"]
