from __future__ import annotations

from datetime import datetime, timezone


def prepare_pr_branch_name(prefix: str = 'prgx/heal') -> str:
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    return f'{prefix}-{stamp}'


def format_pr_body(summary: str, changes: list[str]) -> str:
    bullets = '\n'.join(f'- {item}' for item in changes)
    return f"## PRGX-AG Healing Report\n\n{summary}\n\n### Applied changes\n{bullets or '- none'}\n"
