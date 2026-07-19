"""Manifest, packaging, and instruction-only invariants for warehouse-data."""

from __future__ import annotations

import pathlib
import tomllib
from typing import Any

_ROOT = pathlib.Path(__file__).resolve().parents[1]
_DISTRIBUTION = "cognic-skill-warehouse-data"
_PACKAGE = "cognic_skill_warehouse_data"
_REFERENCED_TOOL = "cognic-tool-oracle-schema/run_readonly_query"
_KERNEL_REVISION = "e5a3f0dbb83b467f555ab87be279635dcbc89713"


def _manifest() -> dict[str, Any]:
    return tomllib.loads((_ROOT / "cognic-pack-manifest.toml").read_text(encoding="utf-8"))


def _pyproject() -> dict[str, Any]:
    return tomllib.loads((_ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def test_manifest_identity_and_instruction_contract() -> None:
    manifest = _manifest()
    assert manifest["pack"] == {
        "pack_id": _DISTRIBUTION,
        "schema_version": 1,
        "kind": "skill",
    }
    assert manifest["skill"] == {
        "mode": "instruction",
        "referenced_tools": [_REFERENCED_TOOL],
    }
    assert manifest["risk_tier"]["tier"] == "read_only"
    assert "declared_tools" not in manifest["skill"]


def test_identity_block_matches_the_public_repo() -> None:
    identity = _manifest()["identity"]
    assert identity["agent_id"] == f"did:web:github.com:bmzee:{_DISTRIBUTION}"
    assert identity["display_name"] == "Cognic Skill Warehouse Data"
    assert identity["provider_url"] == f"https://github.com/bmzee/{_DISTRIBUTION}"
    assert "agent_card_url" not in identity
    assert "agent_card_jws_path" not in identity


def test_wheel_is_runtime_empty_and_kernel_pin_is_immutable() -> None:
    project = _pyproject()["project"]
    assert project["dependencies"] == []
    kernel = [
        dep for dep in project["optional-dependencies"]["dev"] if dep.startswith("cognic-agentos @")
    ]
    assert kernel == [
        "cognic-agentos @ git+https://github.com/bmzee/cognic-agentos@" + _KERNEL_REVISION
    ]
    assert "entry-points" not in project


def test_skill_and_manifest_ship_as_package_data() -> None:
    force = _pyproject()["tool"]["hatch"]["build"]["targets"]["wheel"]["force-include"]
    assert force == {
        "SKILL.md": f"{_PACKAGE}/SKILL.md",
        "cognic-pack-manifest.toml": f"{_PACKAGE}/cognic-pack-manifest.toml",
        "golden/queries.jsonl": f"{_PACKAGE}/golden/queries.jsonl",
    }


def test_supply_chain_paths_are_release_owned() -> None:
    assert _manifest()["supply_chain"]["attestation_paths"] == [
        "attestations/cosign.sig",
        "attestations/sbom.cdx.json",
    ]


def test_dependency_lock_is_committed_policy() -> None:
    assert (_ROOT / "uv.lock").is_file()
    ignored = {
        line.strip()
        for line in (_ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    assert "uv.lock" not in ignored
