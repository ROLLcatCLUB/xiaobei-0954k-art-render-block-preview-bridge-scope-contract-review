from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path


STAGE_ID = "0954K_ART_RENDER_BLOCK_PREVIEW_BRIDGE_SCOPE_CONTRACT"
STAGE_TYPE = "art_render_block_preview_bridge_scope_contract_only"
PASS_STATUS = "ART_RENDER_BLOCK_PREVIEW_BRIDGE_SCOPE_CONTRACT_PASS"
NEXT_STAGE = "0954L_ART_RENDER_BLOCK_PREVIEW_BRIDGE_APPLY_CONTRACT_OR_GATE"
PY_OK = "ALL_0954K_ART_RENDER_BLOCK_PREVIEW_BRIDGE_SCOPE_CONTRACT_CHECKS_OK"
PACKAGE_MANIFEST = "docs/audit_packages/art_render_block_preview_bridge_scope_contract_0954K_manifest.json"
ZIP_PATH = "docs/audit_packages/art_render_block_preview_bridge_scope_contract_0954K.zip"

REQUIRED_FILES = [
    "docs/foundation/art_render_block_preview_bridge_scope_contract_0954K.md",
    "docs/foundation/art_render_block_preview_bridge_scope_contract_0954K.json",
    "docs/audit/art_render_block_preview_bridge_scope_contract_0954K_report.md",
    "scripts/validate_art_render_block_preview_bridge_scope_contract_0954K.py",
    PACKAGE_MANIFEST,
]

SOURCE_FILES = [
    "docs/audit/legacy_card_updates_to_art_render_block_inactive_seal_0954J_result.json",
    "docs/audit/legacy_card_updates_to_art_render_block_inactive_seal_0954J_report.md",
    "docs/audit_packages/legacy_card_updates_to_art_render_block_inactive_seal_0954J_manifest.json",
    "compatibility/card_updates/legacy_card_updates_art_render_block_inactive_apply_0954H.json",
    "docs/audit/legacy_card_updates_to_art_render_block_inactive_smoke_0954I_result.json",
    "platform_core/render_blocks/render_block_type_schema_0954C.json",
    "subject_packs/art/topic_contexts/qinglv_china_color_topic_context_0954E.json",
    "frontend/workbench/fixtures/agent_output_existing_workbench_fixture_0952F_R1.js",
    "frontend/workbench/fixtures/provider_candidate_patch_0952G_R1.js",
    "docs/contracts/workbench_runtime_preview_bridge_069E.schema.json",
    "docs/frontend_experience/workbench_runtime_preview_bridge_069E_report.md",
    "docs/frontend_experience/workbench_preview_viewmodel_contract_071A.md",
    "docs/frontend_experience/workbench_preview_viewmodel_builder_071B.md",
]

MUST_BE_FALSE = [
    "runtime_import_allowed",
    "active_render_allowed",
    "provider_called",
    "memory_read",
    "memory_write",
    "feishu_writeback",
    "formal_scoring",
    "formal_export",
    "server_deploy",
    "frontend_modified",
    "index_html_modified",
    "existing_frontend_runtime_modified",
    "component_grid_behavior_changed",
    "backend_modified",
    "endpoint_created",
    "runtime_executed",
    "adapter_executed",
    "server_executed",
    "active_render_plan_created",
    "inactive_actions_made_executable",
    "real_preview_bridge_apply_connected",
]

RUNTIME_FILES_TO_SCAN = [
    "frontend/workbench/index.html",
    "frontend/workbench/workbench_dynamic_cards_v1.js",
    "frontend/workbench/workbench_agent_runtime_client_v1.js",
    "frontend/workbench/workbench_runtime_preview_bridge_069E.js",
    "frontend/workbench/workbench_preview_viewmodel_adapter_070G.js",
    "backend/xiaobei_ai/workbench_preview_viewmodel_builder_071B.py",
    "backend/xiaobei_ai/workbench_preview_viewmodel_routes_071C.py",
]

FORBIDDEN_RUNTIME_REFS = [
    "art_render_block_preview_bridge_scope_contract_0954K",
    "validate_art_render_block_preview_bridge_scope_contract_0954K",
]

FORBIDDEN_ZIP_PATTERNS = [
    re.compile(r"(^|/)\.env($|[./_-])", re.IGNORECASE),
    re.compile(r"token", re.IGNORECASE),
    re.compile(r"secret", re.IGNORECASE),
    re.compile(r"student[_-]?private", re.IGNORECASE),
    re.compile(r"真实学生数据"),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None)
    return parser.parse_args()


def get_root() -> Path:
    args = parse_args()
    if args.root:
        return Path(args.root).resolve()
    return Path(__file__).resolve().parents[1]


ROOT = get_root()


def read_json(relative_path: str) -> dict:
    with (ROOT / relative_path).open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise AssertionError(f"{relative_path} must contain a JSON object")
    return value


def normalize_newlines(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def bytes_match_manifest(path: Path, expected_sha: str, expected_size: int) -> bool:
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() == expected_sha and len(data) == expected_size:
        return True
    return hashlib.sha256(normalize_newlines(data)).hexdigest() == expected_sha


def assert_files_exist() -> None:
    for relative_path in [*REQUIRED_FILES, *SOURCE_FILES]:
        if not (ROOT / relative_path).is_file():
            raise AssertionError(f"missing file: {relative_path}")
    if not (ROOT / ZIP_PATH).is_file():
        raise AssertionError(f"missing zip: {ZIP_PATH}")


def assert_contract() -> None:
    contract = read_json("docs/foundation/art_render_block_preview_bridge_scope_contract_0954K.json")
    if contract.get("stage_id") != STAGE_ID:
        raise AssertionError("stage_id mismatch")
    if contract.get("stage_type") != STAGE_TYPE:
        raise AssertionError("stage_type mismatch")
    if contract.get("previous_stage") != "0954J_LEGACY_CARD_UPDATES_ART_RENDER_BLOCK_INACTIVE_SEAL":
        raise AssertionError("previous_stage mismatch")
    if contract.get("previous_status") != "LEGACY_CARD_UPDATES_ART_RENDER_BLOCK_INACTIVE_SEALED":
        raise AssertionError("previous_status mismatch")
    if contract.get("source") != "0954J sealed inactive compatibility assets":
        raise AssertionError("source mismatch")
    if contract.get("target") != "future workbench preview bridge candidate only":
        raise AssertionError("target mismatch")
    if contract.get("mode") != "scope_contract_only_no_apply":
        raise AssertionError("mode mismatch")
    levels = set(contract.get("allowed_bridge_level") or [])
    if levels != {"L0_declarative_inventory_only", "L1_declarative_preview_contract_only"}:
        raise AssertionError("allowed bridge level mismatch")
    if contract.get("preview_source") != "readonly sealed inactive assets":
        raise AssertionError("preview_source mismatch")
    sealed = contract.get("sealed_source", {})
    if sealed.get("sealed_scope") != "legacy_card_updates_art_render_block_inactive_compatibility_assets":
        raise AssertionError("sealed scope mismatch")
    if sealed.get("sealed_level") != "inactive_art_render_block_compatibility_only":
        raise AssertionError("sealed level mismatch")
    if sealed.get("legacy_card_block_count") != 12:
        raise AssertionError("sealed legacy count mismatch")
    for key in MUST_BE_FALSE:
        if contract.get(key) is not False:
            raise AssertionError(f"{key} must be false")
    if contract.get("next_stage_requires_explicit_decision") is not True:
        raise AssertionError("next_stage_requires_explicit_decision must be true")
    if contract.get("final_status") != PASS_STATUS:
        raise AssertionError("final_status mismatch")
    if contract.get("recommended_next_stage") != NEXT_STAGE:
        raise AssertionError("recommended_next_stage mismatch")
    references = set(contract.get("static_reference_sources") or [])
    for source in SOURCE_FILES:
        if source not in references:
            raise AssertionError(f"static reference missing: {source}")


def assert_source_chain() -> None:
    seal = read_json("docs/audit/legacy_card_updates_to_art_render_block_inactive_seal_0954J_result.json")
    smoke = read_json("docs/audit/legacy_card_updates_to_art_render_block_inactive_smoke_0954I_result.json")
    asset = read_json("compatibility/card_updates/legacy_card_updates_art_render_block_inactive_apply_0954H.json")
    schema = read_json("platform_core/render_blocks/render_block_type_schema_0954C.json")
    topic = read_json("subject_packs/art/topic_contexts/qinglv_china_color_topic_context_0954E.json")
    if seal.get("final_status") != "LEGACY_CARD_UPDATES_ART_RENDER_BLOCK_INACTIVE_SEALED":
        raise AssertionError("0954J seal final_status mismatch")
    if smoke.get("final_status") != "LEGACY_CARD_UPDATES_ART_RENDER_BLOCK_INACTIVE_SMOKE_PASS":
        raise AssertionError("0954I smoke final_status mismatch")
    if len(asset.get("legacy_card_blocks", [])) != 12:
        raise AssertionError("0954H asset legacy count mismatch")
    if asset.get("compatibility_runtime_imported") is not False or asset.get("component_grid_behavior_changed") is not False:
        raise AssertionError("0954H asset boundary mismatch")
    enum = schema.get("properties", {}).get("block_type", {}).get("enum", [])
    for block_type in ["legacy_card_block", "candidate_patch_block", "review_gate_block", "status_summary_block"]:
        if block_type not in enum:
            raise AssertionError(f"0954C schema missing {block_type}")
    if topic.get("topic_context") != "qinglv_china_color":
        raise AssertionError("0954E qinglv topic mismatch")


def assert_static_preview_refs() -> None:
    schema = read_json("docs/contracts/workbench_runtime_preview_bridge_069E.schema.json")
    if schema.get("title") != "069E Workbench Runtime Preview Bridge":
        raise AssertionError("069E schema title mismatch")
    report = (ROOT / "docs/frontend_experience/workbench_runtime_preview_bridge_069E_report.md").read_text(encoding="utf-8")
    c071a = (ROOT / "docs/frontend_experience/workbench_preview_viewmodel_contract_071A.md").read_text(encoding="utf-8")
    c071b = (ROOT / "docs/frontend_experience/workbench_preview_viewmodel_builder_071B.md").read_text(encoding="utf-8")
    for phrase in ["runtime_attached", "teacher_review_required"]:
        if phrase not in report:
            raise AssertionError(f"069E report missing {phrase}")
    for phrase in ["Workbench Preview ViewModel", "candidate_blocks"]:
        if phrase not in c071a:
            raise AssertionError(f"071A contract missing {phrase}")
    lowered_071b = c071b.lower()
    for phrase in ["纯函数", "dry-run"]:
        if phrase not in lowered_071b:
            raise AssertionError(f"071B doc missing {phrase}")


def run_static_checks() -> None:
    subprocess.run([sys.executable, "-m", "py_compile", str(ROOT / "scripts/validate_art_render_block_preview_bridge_scope_contract_0954K.py")], check=True, cwd=ROOT)


def assert_runtime_not_imported() -> None:
    for relative_path in RUNTIME_FILES_TO_SCAN:
        path = ROOT / relative_path
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for ref in FORBIDDEN_RUNTIME_REFS:
            if ref in text:
                raise AssertionError(f"runtime file references 0954K scope contract: {relative_path} -> {ref}")


def assert_report() -> None:
    report = (ROOT / "docs/audit/art_render_block_preview_bridge_scope_contract_0954K_report.md").read_text(encoding="utf-8")
    for phrase in [
        "scope_contract_only_no_apply",
        "L0/L1 declarative preview contract only",
        "readonly sealed inactive assets",
        "next_stage_requires_explicit_decision=true",
        PY_OK,
    ]:
        if phrase not in report:
            raise AssertionError(f"report missing phrase: {phrase}")


def assert_zip_path_safe(name: str) -> None:
    if "\\" in name:
        raise AssertionError(f"zip path must use forward slashes: {name}")
    if name.startswith("/") or re.match(r"^[A-Za-z]:", name):
        raise AssertionError(f"zip path must be relative: {name}")
    parts = name.split("/")
    if ".." in parts or any(part == "" for part in parts):
        raise AssertionError(f"zip path must not contain empty or parent segments: {name}")
    for pattern in FORBIDDEN_ZIP_PATTERNS:
        if pattern.search(name):
            raise AssertionError(f"zip contains forbidden path pattern: {name}")


def assert_zip_manifest(expected_files: list[str]) -> None:
    manifest = read_json(PACKAGE_MANIFEST)
    if manifest.get("stage_id") != STAGE_ID:
        raise AssertionError("package manifest stage_id mismatch")
    if manifest.get("package_type") != "github_review_audit_package":
        raise AssertionError("package_type mismatch")
    files = manifest.get("files")
    if not isinstance(files, list):
        raise AssertionError("manifest files must be list")
    manifest_paths = {item.get("path") for item in files}
    expected_paths = set(expected_files)
    if manifest_paths != expected_paths:
        raise AssertionError(f"manifest paths mismatch: {sorted(manifest_paths ^ expected_paths)}")
    entries = {}
    for item in files:
        path = item.get("path")
        assert_zip_path_safe(path)
        entries[path] = item
        if path == PACKAGE_MANIFEST and item.get("sha256") == "SELF_REFERENTIAL_MANIFEST":
            continue
        full = ROOT / path
        if not bytes_match_manifest(full, item.get("sha256"), item.get("size_bytes")):
            raise AssertionError(f"manifest sha256 mismatch: {path}")
    with zipfile.ZipFile(ROOT / ZIP_PATH, "r") as archive:
        names = set(archive.namelist())
        for name in names:
            assert_zip_path_safe(name)
        if names != manifest_paths:
            raise AssertionError(f"zip/manifest path mismatch: {sorted(names ^ manifest_paths)}")
        for name in names:
            entry = entries[name]
            data = archive.read(name)
            if name == PACKAGE_MANIFEST and entry.get("sha256") == "SELF_REFERENTIAL_MANIFEST":
                continue
            if entry.get("sha256") != hashlib.sha256(data).hexdigest():
                raise AssertionError(f"zip sha256 mismatch: {name}")
            if entry.get("size_bytes") != len(data):
                raise AssertionError(f"zip size mismatch: {name}")
    if manifest.get("zip_self_entry_count") != len(expected_paths):
        raise AssertionError("zip_self_entry_count mismatch")


def main() -> int:
    try:
        assert_files_exist()
        assert_contract()
        assert_source_chain()
        assert_static_preview_refs()
        run_static_checks()
        assert_runtime_not_imported()
        assert_report()
        assert_zip_manifest([*REQUIRED_FILES, *SOURCE_FILES])
    except Exception as exc:
        print(f"0954K_VALIDATION_FAILED: {exc}", file=sys.stderr)
        return 1
    print(PY_OK)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
