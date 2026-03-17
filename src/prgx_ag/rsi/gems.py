from __future__ import annotations

import json
from pathlib import Path

from prgx_ag.schemas import GemOfWisdom


def append_gem_log(log_path: Path, gem: GemOfWisdom) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    existing: list[dict] = []
    if log_path.exists():
        existing = json.loads(log_path.read_text(encoding='utf-8') or '[]')
    existing.append(gem.model_dump())
    if len(existing) > 200:
        existing = existing[-200:]
    log_path.write_text(json.dumps(existing, indent=2), encoding='utf-8')
