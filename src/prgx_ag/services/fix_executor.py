from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

from prgx_ag.schemas import ProcessingOutcome


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

        # exact file or directory prefix block
        if normalized == pattern or normalized.startswith(f"{pattern}/"):
            return True

        # wildcard block เช่น .env.*, *.pem, *.key
        if fnmatch(normalized, pattern) or fnmatch(f"./{normalized}", pattern):
            return True

    return False


def apply_safe_fixes(
    repo_root: Path,
    fixes: list[dict[str, str]],
    allowed_paths: list[str],
    protected_paths: list[str],
    envelope_id: str,
    dry_run: bool,
) -> ProcessingOutcome:
    changed: list[str] = []

    for fix in fixes:
        rel_path = str(fix.get("path", "")).strip()
        if not rel_path:
            return ProcessingOutcome(
                agent_name="PRGX2",
                envelope_id=envelope_id,
                success=False,
                execution_time=0.0,
                message="Fix entry missing path",
            )

        rel_target = Path(rel_path)
        if rel_target.is_absolute():
            return ProcessingOutcome(
                agent_name="PRGX2",
                envelope_id=envelope_id,
                success=False,
                execution_time=0.0,
                message=f"Absolute path blocked: {rel_path}",
            )

        normalized_rel_path = _normalize_rel_path(rel_path)
        target = (repo_root / normalized_rel_path).resolve()

        if _matches_protected(normalized_rel_path, protected_paths):
            return ProcessingOutcome(
                agent_name="PRGX2",
                envelope_id=envelope_id,
                success=False,
                execution_time=0.0,
                message=f"Protected path blocked: {normalized_rel_path}",
            )

        allowed = any(_is_under(target, (repo_root / p).resolve()) for p in allowed_paths)
        if not allowed:
            return ProcessingOutcome(
                agent_name="PRGX2",
                envelope_id=envelope_id,
                success=False,
                execution_time=0.0,
                message=f"Path not allowed: {normalized_rel_path}",
            )

        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            content = str(fix.get("content", ""))
            target.write_text(content, encoding="utf-8")

        changed.append(normalized_rel_path)

    return ProcessingOutcome(
        agent_name="PRGX2",
        envelope_id=envelope_id,
        success=True,
        execution_time=0.01,
        message="Safe fixes applied",
        details={
            "changed": changed,
            "dry_run": dry_run,
        },
    )
