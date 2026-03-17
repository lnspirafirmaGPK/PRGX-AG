from __future__ import annotations

from prgx_ag.schemas import GemOfWisdom, ProcessingOutcome


class RSIEngine:
    def analyze(self, outcome: ProcessingOutcome) -> GemOfWisdom | None:
        if outcome.success and outcome.execution_time <= 1.5:
            return GemOfWisdom(
                lesson='Stable and efficient execution path validated.',
                param_update={'efficiency': 0.1, 'stability': 0.05},
                scope='runtime',
            )
        if outcome.success and outcome.execution_time > 1.5:
            return GemOfWisdom(
                lesson='Execution succeeded but needs optimization.',
                param_update={'efficiency': 0.05},
                scope='runtime',
            )
        return GemOfWisdom(
            lesson='Failure indicates safety/stability hardening is required.',
            param_update={'stability': 0.1},
            scope='safety',
        )
