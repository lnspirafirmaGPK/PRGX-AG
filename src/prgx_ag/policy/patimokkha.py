from __future__ import annotations

from prgx_ag.policy.ruleset import BLOCKED_PATTERNS
from prgx_ag.schemas import AuditResult, EthicalStatus, Intent


class PatimokkhaChecker:
    def validate_intent(self, intent: Intent) -> AuditResult:
        text = f"{intent.description} {intent.metadata}".lower()
        for token, reason in BLOCKED_PATTERNS.items():
            if token in text:
                return AuditResult(
                    is_allowed=False,
                    status=EthicalStatus.PARAJIKA,
                    reason=reason,
                    suggested_action='Escalate to audit and reject execution.',
                )
        return AuditResult(
            is_allowed=True,
            status=EthicalStatus.CLEAN,
            reason='Intent complies with Patimokkha principles.',
            suggested_action='Proceed with monitored execution.',
        )
