"""Byte and schema pins for the live-v23.3-verified warehouse corpus."""

from __future__ import annotations

import hashlib
import json
import pathlib
import tomllib
from collections import Counter
from typing import Any

_PATH = pathlib.Path(__file__).resolve().parents[1] / "golden" / "queries.jsonl"
_MANIFEST_PATH = _PATH.with_name("manifest.toml")
_SHA256 = "70f7d30bb4f2ab61f0b77c02355f7d05f99843e2fb7c8b5ef1506c46bc3c2f84"
_COUNTS = {"golden": 10, "adversarial": 5, "refusal": 5, "trigger_pos": 3, "trigger_neg": 3}


def _cases() -> list[dict[str, Any]]:
    return [json.loads(line) for line in _PATH.read_text(encoding="utf-8").splitlines()]


def test_corpus_is_byte_identical_to_the_live_verified_contract() -> None:
    assert hashlib.sha256(_PATH.read_bytes()).hexdigest() == _SHA256


def test_judge_calibration_is_bound_to_the_human_labelled_set() -> None:
    manifest = tomllib.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))
    assert manifest["judge"] == {
        "model_alias": "cognic-tier1-proof-m85e",
        "rubric_ref": "a007-sql-result-v1",
        "calibration_set_id": "m85e-a007-human-labelled-v1",
        "measured_kappa": 1.0,
    }


def test_corpus_shape_and_distribution_are_closed() -> None:
    cases = _cases()
    assert len(cases) == 26
    assert len({case["case_id"] for case in cases}) == len(cases)
    assert Counter(case["kind"] for case in cases) == _COUNTS
    assert sum(bool(case["holdout"]) for case in cases) == 3
    assert all(case["case_id"].startswith("sh-") for case in cases)


def test_refusal_teaching_names_the_approval_path() -> None:
    refusals = [
        case for case in _cases() if case["kind"] == "refusal" and case["case_id"] != "sh-205"
    ]
    assert all(
        "approval" in case["notes"] and "offer to request" in case["notes"] for case in refusals
    )


def test_sh_103_requires_both_labeled_measure_cuts() -> None:
    case = next(case for case in _cases() if case["case_id"] == "sh-103")
    assert case["expected"] == {"mode": "rows", "value": None, "verify_live": True}
    assert "total_amount_sold" in case["reference_sql"]
    assert "total_quantity_sold" in case["reference_sql"]
    assert "clarifying question = FAIL" in case["notes"]
    assert "single cut = FAIL" in case["notes"]


def test_refusal_offer_severity_is_case_specific() -> None:
    cases = {case["case_id"]: case for case in _cases()}
    for case_id in ("sh-201", "sh-204"):
        notes = cases[case_id]["notes"]
        assert "REQUIRED" in notes
        assert "entitlement/approval path" in notes
        assert "offer to request" in notes
    impossible = cases["sh-205"]["notes"]
    assert "OPTIONAL" in impossible
    assert "no governed join key" in impossible


def test_trigger_cases_are_routing_contracts() -> None:
    triggers = [case for case in _cases() if case["kind"].startswith("trigger_")]
    assert len(triggers) == 6
    assert all(case["reference_sql"] is None for case in triggers)


def test_sh_104_remains_the_open_judge_scored_exception() -> None:
    case = next(case for case in _cases() if case["case_id"] == "sh-104")
    assert case["scoring"] == "judge"
    assert case["holdout"] is True
    assert "one deliberate exception to result-only scoring" in case["notes"]
