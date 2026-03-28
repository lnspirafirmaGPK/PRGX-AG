from __future__ import annotations

import hashlib
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

from prgx_ag.schemas import ProcessingOutcome

FixPlanEntry = dict[str, Any]


def _is_under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _normalize_rel_path(rel_path: str) -> str:
    return rel_path.replace("\\", "/").lstrip("./")


def _matches_protected(rel_path: str, protected_paths: list[str]) -> bool:
    normalized = _normalize_rel_path(rel_path)
    for protected in protected_paths:
        pattern = protected.replace("\\", "/").rstrip("/")
        if not pattern:
            continue
        if normalized == pattern or normalized.startswith(f"{pattern}/"):
            return True
        if fnmatch(normalized, pattern) or fnmatch(f"./{normalized}", pattern):
            return True
    return False


def _collect_fix_metadata(fixes: list[FixPlanEntry]) -> dict[str, list[str]]:
    fix_classes: list[str] = []
    verification_commands: list[str] = []
    rollback_hints: list[str] = []
    validators: list[str] = []

    for fix in fixes:
        fix_class = str(fix.get("fix_class", "")).strip()
        if fix_class and fix_class not in fix_classes:
            fix_classes.append(fix_class)
        validator = str(fix.get("validator", "")).strip()
        if validator and validator not in validators:
            validators.append(validator)
        raw_commands = fix.get("verification_commands", [])
        if isinstance(raw_commands, list):
            for command in raw_commands:
                text = str(command).strip()
                if text and text not in verification_commands:
                    verification_commands.append(text)
        rollback_hint = str(fix.get("rollback_hint", "")).strip()
        if rollback_hint and rollback_hint not in rollback_hints:
            rollback_hints.append(rollback_hint)

    return {
        "fix_classes": fix_classes,
        "verification_commands": verification_commands,
        "rollback_hints": rollback_hints,
        "validators": validators,
    }


def _snapshot_for(target: Path, rel_path: str, fix: FixPlanEntry) -> dict[str, Any]:
    existed = target.exists()
    previous_content = target.read_text(encoding="utf-8") if existed and target.is_file() else None
    previous_hash = hashlib.sha256(previous_content.encode("utf-8")).hexdigest() if previous_content is not None else None
    return {
        "path": rel_path,
        "fix_class": str(fix.get("fix_class", "")),
        "existed": existed,
        "previous_hash": previous_hash,
        "previous_content": previous_content,
        "rollback": "restore previous_content if existed else delete file",
    }


def _render_dependency_manifest(original: str, dependency_name: str, version_spec: str) -> str:
    lines = original.splitlines()
    updated: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(f'"{dependency_name}'):
            indent = line[: len(line) - len(line.lstrip())]
            updated.append(f'{indent}"{dependency_name}{version_spec}",')
            replaced = True
        else:
            updated.append(line)
    if not replaced:
        raise ValueError(f"Dependency not found in manifest: {dependency_name}")
    return "\n".join(updated) + ("\n" if original.endswith("\n") else "")


def _apply_fix_content(target: Path, rel_path: str, fix: FixPlanEntry) -> str:
    raw_metadata = fix.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    fix_class = str(fix.get("fix_class", ""))
    if fix_class == "dependency_bump":
        original = target.read_text(encoding="utf-8") if target.exists() else ""
        dependency_name = str(metadata.get("dependency_name", "")).strip()
        version_spec = str(metadata.get("dependency_version", "")).strip()
        return _render_dependency_manifest(original, dependency_name, version_spec)
    return str(fix.get("content", ""))


def _validate_fix(fix: FixPlanEntry, rel_path: str) -> str | None:
    fix_class = str(fix.get("fix_class", ""))
    validator = str(fix.get("validator", "")).strip()
    raw_metadata = fix.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}

    if fix_class == "create_empty_init":
        if not rel_path.endswith("/__init__.py") and rel_path != "__init__.py":
            return "create_empty_init requires an __init__.py target"
        if str(fix.get("content", "")) != "":
            return "create_empty_init only permits empty file content"
    elif fix_class == "manifest_sync":
        if not rel_path.endswith("/__init__.py") and rel_path != "__init__.py":
            return "manifest_sync currently only supports __init__.py restoration"
        if str(fix.get("content", "")) != "":
            return "manifest_sync currently only permits empty file content"
    elif fix_class == "dependency_bump":
        required_keys = {"dependency_name", "dependency_version", "manifest_path", "allowlisted_range", "bump_policy"}
        if not required_keys.issubset(metadata.keys()):
            return "dependency_bump missing allowlist metadata"
        if rel_path != str(metadata.get("manifest_path", "")).strip():
            return "dependency_bump manifest path mismatch"
        if str(metadata.get("dependency_version", "")).strip() != str(metadata.get("allowlisted_range", "")).strip():
            return "dependency_bump version is outside the allowlisted range"
    else:
        return f"Unsupported fix class: {fix_class or 'unknown'}"

    if not validator:
        return "Missing validator for fix entry"
    return None


def _verify_fix(target: Path, fix: FixPlanEntry, rendered_content: str) -> dict[str, Any]:
    fix_class = str(fix.get("fix_class", ""))
    raw_metadata = fix.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    exists = target.exists()
    current_content = target.read_text(encoding="utf-8") if exists and target.is_file() else None

    passed = False
    summary = "verification not run"
    if fix_class in {"create_empty_init", "manifest_sync"}:
        passed = exists and current_content == rendered_content == ""
        summary = "verified empty package marker exists"
    elif fix_class == "dependency_bump":
        needle = f'{metadata.get("dependency_name", "")}{metadata.get("dependency_version", "")}'
        passed = exists and current_content is not None and needle in current_content
        summary = f"verified manifest contains allowlisted spec {needle}"

    return {
        "path": str(fix.get("path", "")),
        "fix_class": fix_class,
        "passed": passed,
        "summary": summary,
        "revert": str(fix.get("rollback_hint", "")).strip(),
    }


def _detect_write_path_issue(repo_root: Path, target: Path) -> str | None:
    if target.exists() and target.is_dir():
        return f"target path is an existing directory: {target.relative_to(repo_root)}"

    parent = target.parent
    if parent.exists() and not parent.is_dir():
        return f"target parent is not a directory: {parent.relative_to(repo_root)}"

    rel_parent = parent.relative_to(repo_root)
    cursor = repo_root
    for segment in rel_parent.parts:
        cursor = cursor / segment
        if cursor.exists() and not cursor.is_dir():
            return f"mkdir would fail because path segment is a file: {cursor.relative_to(repo_root)}"

    return None


def _verify_rendered_fix(repo_root: Path, target: Path, fix: FixPlanEntry, rendered_content: str) -> dict[str, Any]:
    fix_class = str(fix.get("fix_class", ""))
    raw_metadata = fix.get("metadata")
    metadata: dict[str, Any] = raw_metadata if isinstance(raw_metadata, dict) else {}
    path_issue = _detect_write_path_issue(repo_root, target)

    passed = False
    summary = "verification not run"
    if fix_class in {"create_empty_init", "manifest_sync"}:
        passed = rendered_content == "" and path_issue is None
        summary = (
            "verified dry-run payload renders an empty package marker"
            if path_issue is None
            else f"dry-run detected non-writable target path: {path_issue}"
        )
    elif fix_class == "dependency_bump":
        needle = f'{metadata.get("dependency_name", "")}{metadata.get("dependency_version", "")}'
        passed = needle in rendered_content and path_issue is None
        summary = (
            f"verified dry-run manifest contains allowlisted spec {needle}"
            if path_issue is None
            else f"dry-run detected non-writable target path: {path_issue}"
        )

    return {
        "path": str(fix.get("path", "")),
        "fix_class": fix_class,
        "passed": passed,
        "summary": summary,
        "revert": str(fix.get("rollback_hint", "")).strip(),
    }


def apply_safe_fixes(repo_root: Path, fixes: list[FixPlanEntry], allowed_paths: list[str], protected_paths: list[str], envelope_id: str, dry_run: bool) -> ProcessingOutcome:
    changed: list[str] = []
    snapshots: list[dict[str, Any]] = []
    verification_results: list[dict[str, Any]] = []
    metadata = _collect_fix_metadata(fixes)

    for fix in fixes:
        rel_path = str(fix.get("path", "")).strip()
        if not rel_path:
            return ProcessingOutcome(agent_name="PRGX2", envelope_id=envelope_id, success=False, execution_time=0.0, message="Fix entry missing path", details=metadata)
        rel_target = Path(rel_path)
        if rel_target.is_absolute():
            return ProcessingOutcome(agent_name="PRGX2", envelope_id=envelope_id, success=False, execution_time=0.0, message=f"Absolute path blocked: {rel_path}", details=metadata)

        normalized_rel_path = _normalize_rel_path(rel_path)
        validation_error = _validate_fix(fix, normalized_rel_path)
        if validation_error is not None:
            return ProcessingOutcome(agent_name="PRGX2", envelope_id=envelope_id, success=False, execution_time=0.0, message=validation_error, details=metadata)

        target = (repo_root / normalized_rel_path).resolve()
        if _matches_protected(normalized_rel_path, protected_paths):
            return ProcessingOutcome(agent_name="PRGX2", envelope_id=envelope_id, success=False, execution_time=0.0, message=f"Protected path blocked: {normalized_rel_path}", details=metadata)

        allowed = any(_is_under(target, (repo_root / p).resolve()) for p in allowed_paths)
        if not allowed:
            return ProcessingOutcome(agent_name="PRGX2", envelope_id=envelope_id, success=False, execution_time=0.0, message=f"Path not allowed: {normalized_rel_path}", details=metadata)

        try:
            rendered_content = _apply_fix_content(target, normalized_rel_path, fix)
        except ValueError as exc:
            return ProcessingOutcome(agent_name="PRGX2", envelope_id=envelope_id, success=False, execution_time=0.0, message=str(exc), details=metadata)
        snapshots.append(_snapshot_for(target, normalized_rel_path, fix))

        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered_content, encoding="utf-8")
        else:
            verification_results.append(_verify_rendered_fix(repo_root, target, fix, rendered_content))

        if not dry_run:
            verification_results.append(_verify_fix(target, fix, rendered_content))

        changed.append(normalized_rel_path)

    verification_status = "passed" if verification_results and all(result.get("passed") for result in verification_results) else "not-run"
    if verification_results and not all(result.get("passed") for result in verification_results):
        verification_status = "failed"

    return ProcessingOutcome(
        agent_name="PRGX2",
        envelope_id=envelope_id,
        success=True,
        execution_time=0.01,
        message="Safe fixes applied",
        details={
            "changed": changed,
            "dry_run": dry_run,
            "verification_status": verification_status,
            "verification_results": verification_results,
            "snapshots": snapshots,
            **metadata,
        },
    )
