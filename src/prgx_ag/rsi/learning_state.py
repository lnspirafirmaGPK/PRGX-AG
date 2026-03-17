from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from prgx_ag.schemas import GemOfWisdom


@dataclass(slots=True)
class LearningState:
    parameters: dict[str, float] = field(default_factory=lambda: {'stability': 1.0, 'efficiency': 1.0})

    def apply_gem(self, gem: GemOfWisdom) -> bool:
        if not gem.safe_to_apply:
            return False
        for key, delta in gem.param_update.items():
            if not isinstance(delta, (int, float)):
                return False
            current = self.parameters.get(key, 1.0)
            self.parameters[key] = max(0.1, min(10.0, current + float(delta)))
        return True

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.parameters, indent=2), encoding='utf-8')
