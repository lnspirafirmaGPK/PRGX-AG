from __future__ import annotations

from pathlib import Path

from prgx_ag.schemas import ProcessingOutcome


def _is_under(path: Path, base: Path) -> bool:
    try:
        path.resolve().relative_to(base.resolve())
        return True
    except ValueError:
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
        rel_path = fix['path']
        target = (repo_root / rel_path).resolve()
        if any(str(rel_path).startswith(protected.rstrip('/')) for protected in protected_paths):
            return ProcessingOutcome(agent_name='PRGX2', envelope_id=envelope_id, success=False, execution_time=0.0, message=f'Protected path blocked: {rel_path}')
        allowed = any(_is_under(target, (repo_root / p).resolve()) for p in allowed_paths)
        if not allowed:
            return ProcessingOutcome(agent_name='PRGX2', envelope_id=envelope_id, success=False, execution_time=0.0, message=f'Path not allowed: {rel_path}')
        if not dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            content = fix.get('content', '')
            target.write_text(content, encoding='utf-8')
        changed.append(rel_path)
    return ProcessingOutcome(agent_name='PRGX2', envelope_id=envelope_id, success=True, execution_time=0.01, message='Safe fixes applied', details={'changed': changed})
