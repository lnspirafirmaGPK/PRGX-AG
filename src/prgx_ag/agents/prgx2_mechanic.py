from __future__ import annotations

from pathlib import Path
from time import perf_counter

from prgx_ag.core import BaseAgent
from prgx_ag.policy import PatimokkhaChecker
from prgx_ag.schemas import AuditStatus, Intent, ProcessingOutcome
from prgx_ag.services.fix_executor import apply_safe_fixes


class PRGX2Mechanic(BaseAgent):
    def __init__(
        self,
        bus,
        root: Path,
        checker: PatimokkhaChecker,
        allowed_paths: list[str],
        protected_paths: list[str],
        dry_run: bool = True,
    ) -> None:
        super().__init__(agent_id='PRGX2', role='Mechanic', bus=bus)
        self.root = root
        self.checker = checker
        self.allowed_paths = allowed_paths
        self.protected_paths = protected_paths
        self.dry_run = dry_run

    async def apply_shadow_fix(self, target: str, fix_plan: dict[str, object]) -> ProcessingOutcome:
        intent = fix_plan['intent']
        assert isinstance(intent, Intent)
        audit_status = fix_plan['audit_status']
        assert isinstance(audit_status, AuditStatus)

        if audit_status != AuditStatus.APPROVED:
            return ProcessingOutcome(agent_name=self.agent_id, envelope_id=str(fix_plan.get('envelope_id', 'na')), success=False, execution_time=0.0, message='Rejected: intent not approved', details={'target': target})

        audit = self.checker.validate_intent(intent)
        if not audit.is_allowed:
            return ProcessingOutcome(agent_name=self.agent_id, envelope_id=str(fix_plan.get('envelope_id', 'na')), success=False, execution_time=0.0, message=f'Rejected by Patimokkha: {audit.reason}', details={'target': target})

        start = perf_counter()
        outcome = apply_safe_fixes(
            self.root,
            fixes=fix_plan.get('fixes', []),
            allowed_paths=self.allowed_paths,
            protected_paths=self.protected_paths,
            envelope_id=str(fix_plan.get('envelope_id', 'na')),
            dry_run=self.dry_run,
        )
        outcome.execution_time = perf_counter() - start
        return outcome
