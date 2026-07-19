"""SKILL.md shape and warehouse semantic-contract pins."""

from __future__ import annotations

import pathlib
import re
import tomllib
from typing import Any

from cognic_agentos.cli.validators.skills import validate as validate_skill_pack
from cognic_agentos.protocol.skill_manifest import parse_skill_md, validate_skill_md

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_DESCRIPTION = (
    "Warehouse sales, revenue, units, channels, promotions, and calendar or fiscal "
    "time questions over governed Oracle SH star-schema views."
)
_VIEWS = {
    "SH.V_SALES_STAR",
    "SH.V_CALENDAR",
    "SH.V_PROMOTIONS",
    "SH.V_SALES_BY_CHANNEL",
}
_AMBIGUOUS_BLOCK = """## 9.1 AMBIGUOUS

- `\"revenue\"` -> `AMOUNT_SOLD` stated-default.
- bare `\"sales/sell\"` -> ASK.
- explicit calendar/fiscal -> answer."""
_SQL_BLOCK_RE = re.compile(r"```sql\n(.*?)```", re.DOTALL)
_QUALIFIED_REF_RE = re.compile(r"\b([A-Z][A-Z0-9_$#]{1,}\.[A-Z][A-Z0-9_$#]*)\b")


def _text() -> str:
    return (_ROOT / "SKILL.md").read_text(encoding="utf-8")


def _parsed() -> tuple[dict[str, Any], str]:
    return parse_skill_md(_text())


def test_frontmatter_is_trigger_tuned_and_valid() -> None:
    frontmatter, body = _parsed()
    validate_skill_md(frontmatter, body=body)
    assert frontmatter == {"name": "warehouse-data", "description": _DESCRIPTION}


def test_body_names_scope_tool_and_all_governed_views() -> None:
    _frontmatter, body = _parsed()
    assert "`warehouse`" in body
    assert "cognic-tool-oracle-schema/run_readonly_query" in body
    for view in _VIEWS:
        assert view in body


def test_star_grain_fanout_and_rollup_grain_are_explicit() -> None:
    _frontmatter, body = _parsed()
    normalized = " ".join(body.split())
    assert "(`PROD_ID`, `CUST_ID`, `TIME_ID`, `CHANNEL_ID`, `PROMO_ID`)" in normalized
    assert "join dimensions THROUGH `SH.V_SALES_STAR`, never dimension-to-dimension" in normalized
    assert "channel x calendar-month grain" in normalized


def test_ambiguous_block_matches_the_corpus_binding_exactly() -> None:
    assert _AMBIGUOUS_BLOCK in _parsed()[1]


def test_promotion_cost_and_unexposed_dimensions_are_not_claimed() -> None:
    _frontmatter, body = _parsed()
    assert "`V_PROMOTIONS` deliberately excludes `PROMO_COST`" in body
    assert "product and customer dimensions are not exposed" in body


def test_examples_reference_only_governed_views() -> None:
    blocks = _SQL_BLOCK_RE.findall(_parsed()[1])
    assert len(blocks) >= 2
    refs = {ref for block in blocks for ref in _QUALIFIED_REF_RE.findall(block.upper())}
    assert refs
    assert refs <= _VIEWS


def test_kernel_instruction_validator_has_no_refusals() -> None:
    manifest = tomllib.loads((_ROOT / "cognic-pack-manifest.toml").read_text(encoding="utf-8"))
    findings = validate_skill_pack(manifest, _ROOT)
    assert [finding for finding in findings if finding.severity == "refusal"] == []
    assert [finding.reason for finding in findings if finding.severity == "warning"] == [
        "skill_manifest_referenced_tool_unverifiable"
    ]
