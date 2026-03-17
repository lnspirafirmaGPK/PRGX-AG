from __future__ import annotations

from uuid import uuid4

from prgx_ag.core import BaseAgent
from prgx_ag.core.events import EXECUTE_FIX, FIX_COMPLETED, INTENT_TRANSLATED, ISSUE_REPORTED
from prgx_ag.schemas import AuditStatus, EthicalStatus
from prgx_ag.services.narrative_builder import build_commit_style_narrative
from prgx_ag.services.translation_matrix import build_healing_intent, translate_status


class PRGX3Diplomat(BaseAgent):
    async def start(self) -> None:
        await super().start()
        await self.subscribe(ISSUE_REPORTED, self.receive_issue_report)

    def translate_to_world(self, status: EthicalStatus) -> str:
        return translate_status(status)

    async def receive_issue_report(self, findings: dict[str, object]) -> None:
        intent = build_healing_intent(findings)
        fixes: list[dict[str, str]] = []
        for issue in findings.get('structural_issues', []):
            if isinstance(issue, str) and issue.startswith('Missing __init__.py in '):
                fixes.append({'path': issue.replace('Missing __init__.py in ', '') + '/__init__.py', 'content': ''})
        payload = {'envelope_id': str(uuid4()), 'intent': intent, 'audit_status': AuditStatus.APPROVED, 'findings': findings, 'fixes': fixes}
        await self.publish(INTENT_TRANSLATED, {'intent': intent})
        await self.publish(EXECUTE_FIX, payload)

    async def report_result(self, outcome) -> None:
        await self.publish(FIX_COMPLETED, {'outcome': outcome, 'narrative': build_commit_style_narrative(outcome)})
