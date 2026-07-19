"""Pins the protected, reproducible release lane for instruction skills."""

from __future__ import annotations

import pathlib
import re
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "sign-and-publish.yml"


def _normalized_name(requirement: str) -> str:
    match = re.match(r"[A-Za-z0-9._-]+", requirement)
    assert match is not None
    return match.group(0).lower().replace("_", "-")


def test_release_workflow_is_dispatch_only_versioned_and_protected() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    trigger = workflow.split("\non:\n", maxsplit=1)[1].split("\npermissions:\n", maxsplit=1)[0]
    assert re.search(r"(?m)^  workflow_dispatch:$", trigger)
    assert re.search(r"(?m)^      version:$", trigger)
    assert not re.search(r"(?m)^  (?:push|pull_request|release|schedule):", trigger)
    assert "validate-request:" in workflow
    assert re.search(r"(?m)^    environment: release$", workflow)
    assert "requested version does not match pyproject.toml" in workflow
    assert "release tag already exists" in workflow
    assert "GitHub release already exists" in workflow


def test_release_workflow_installs_the_pinned_supply_chain_toolchain() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "COSIGN_VERSION=3.0.6" in workflow
    assert "c956e5dfcac53d52bcf058360d579472f0c1d2d9b69f55209e256fe7783f4c74" in workflow
    assert "SYFT_VERSION=1.45.1" in workflow
    assert "20c84195e24927f50a3b2269946be51f4c4abc9d2f145fee7388b4199149f716" in workflow
    assert "GRYPE_VERSION=0.114.0" in workflow
    assert "edda0968d8827daab01d32b3cd7de192ae0915005e7bbfcfef9e68e79bc43343" in workflow
    assert workflow.count("sha256sum -c -") == 3
    assert "pip-licenses --version" in workflow


def test_release_workflow_custodies_and_retires_the_environment_key() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "COSIGN_PRIVATE_KEY: ${{ secrets.COSIGN_PRIVATE_KEY }}" in workflow
    assert "COSIGN_PASSWORD: ${{ secrets.COSIGN_PASSWORD }}" in workflow
    assert 'chmod 0600 "$COGNIC_SIGNING_KEY_PATH"' in workflow
    assert 'cosign public-key --key "$COGNIC_SIGNING_KEY_PATH"' in workflow
    assert 'cmp -s "$RUNNER_TEMP/derived-cosign.pub" cosign.pub' in workflow
    assert "if: always()" in workflow
    assert 'rm -f "${COGNIC_SIGNING_KEY_PATH:-}"' in workflow


def test_skill_release_builds_signs_verifies_and_publishes_without_jws() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "uv lock --check" in workflow
    assert "uv sync --frozen --extra dev" in workflow
    assert "uv build --wheel" in workflow
    assert "agentos sign --bundle ." in workflow
    assert "agentos verify --trust-root cosign.pub ." in workflow
    assert 'gh release create "$tag"' in workflow
    assert "release.sh" not in workflow
    assert "AGENT_CARD" not in workflow
    assert "jws" not in workflow.lower()


def test_dev_inventory_provisions_pip_licenses() -> None:
    project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    dev = project["project"]["optional-dependencies"]["dev"]
    assert "pip-licenses" in {_normalized_name(item) for item in dev}

    lock = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
    package = next(item for item in lock["package"] if item.get("source") == {"editable": "."})
    locked_dev = package["optional-dependencies"]["dev"]
    assert "pip-licenses" in {str(item["name"]).lower().replace("_", "-") for item in locked_dev}
