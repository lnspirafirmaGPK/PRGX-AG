from __future__ import annotations

from pathlib import Path
from typing import Any

from prgx_ag.config import RUNTIME_PROFILES, RuntimeProfileName
from uuid import uuid4

from prgx_ag.core import BaseAgent
from prgx_ag.core.events import (
    AUDIT_VIOLATION,
    EXECUTE_FIX,
    FIX_COMPLETED,
    INTENT_TRANSLATED,
    ISSUE_REPORTED,
)
from prgx_ag.policy import PatimokkhaChecker
from prgx_ag.schemas import AuditStatus, EthicalStatus, Intent
from prgx_ag.services.healing_intent_builder import build_fix_plan
from prgx_ag.services.narrative_builder import build_commit_style_narrative
from prgx_ag.services.translation_matrix import build_healing_intent, translate_status


class PRGX3Diplomat(BaseAgent):
    """Translate findings into governed execution intent."""

    def __init__(
        self,
        bus,
        checker: PatimokkhaChecker | None = None,
        agent_id: str = "PRGX3",
        role: str = "Diplomat",
        runtime_profile: RuntimeProfileName = "development",
    ) -> None:
        super().__init__(agent_id=agent_id, role=role, bus=bus)
        self.checker = checker or PatimokkhaChecker()
        self.runtime_profile = runtime_profile

    async def start(self) -> None:
        await super().start()
        await self.subscribe(ISSUE_REPORTED, self.receive_issue_report)

    def create_healing_intent(self, findings: dict[str, Any]) -> Intent:
        return build_healing_intent(findings)

    def translate_to_world(self, status: EthicalStatus) -> str:
        return translate_status(status)

    def build_narrative(self, outcome) -> str:
        return build_commit_style_narrative(outcome)

    def evaluate_audit(self, intent: Intent) -> tuple[AuditStatus, dict[str, Any]]:
        audit = self.checker.validate_intent(intent)
        audit_status = AuditStatus.APPROVED if audit.is_allowed else AuditStatus.REJECTED
        return audit_status, audit.model_dump()

    async def publish_execute_fix(self, payload: dict[str, Any]) -> None:
        await self.publish(EXECUTE_FIX, payload)

    async def receive_issue_report(self, findings: dict[str, object]) -> None:
        if not bool(findings.get("requires_fix", False)):
            self.logger.info("Issue report marked as non-actionable; skipping execution.")
            return

        intent = self.create_healing_intent(findings)
        repo_root = Path(str(findings.get("target", ".")))
        profile = RUNTIME_PROFILES[self.runtime_profile]

        raw_issue_count = findings.get("issue_count")
        if isinstance(raw_issue_count, int):
            issue_count = raw_issue_count
        elif isinstance(raw_issue_count, str):
            try:
                issue_count = int(raw_issue_count.strip())
            except ValueError:
                issue_count = profile.max_issue_count_for_auto_fix + 1
        else:
            issue_count = profile.max_issue_count_for_auto_fix + 1

        if issue_count > profile.max_issue_count_for_auto_fix:
            self.logger.warning(
                "Issue count %s exceeds %s profile threshold %s; skip execution.",
                issue_count,
                profile.name,
                profile.max_issue_count_for_auto_fix,
            )
            return

        fixes = build_fix_plan(findings, repo_root=repo_root)
        if len(fixes) > profile.max_auto_fix_items:
            fixes = fixes[: profile.max_auto_fix_items]

        envelope_id = str(uuid4())
        audit_status, audit = self.evaluate_audit(intent)

        payload = {
            "envelope_id": envelope_id,
            "intent": intent,
            "audit_status": audit_status,
            "audit": audit,
            "findings": findings,
            "fixes": fixes,
        }

        await self.publish(INTENT_TRANSLATED, {"intent": intent})

        if audit_status != AuditStatus.APPROVED:
            await self.publish(
                AUDIT_VIOLATION,
                {
                    "envelope_id": envelope_id,
                    "intent": intent,
                    "audit_status": audit_status,
                    "audit": audit,
                    "findings": findings,
                },
            )
            return

        if not fixes:
            self.logger.info(
                "No executable fix plan generated for envelope %s; skipping execution.",
                envelope_id,
            )
            return

        await self.publish_execute_fix(payload)

    async def report_result(self, outcome) -> None:
        await self.publish(
            FIX_COMPLETED,
            {
                "outcome": outcome,
                "narrative": self.build_narrative(outcome),
            },
        )
