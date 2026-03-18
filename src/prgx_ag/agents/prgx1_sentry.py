from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from prgx_ag.core import BaseAgent
from prgx_ag.core.events import ISSUE_REPORTED
from prgx_ag.schemas.findings import Finding, IssueReport
from prgx_ag.services.dependency_scanner import scan_dependency_anomalies
from prgx_ag.services.integrity_scanner import scan_integrity_drift
from prgx_ag.services.structure_scanner import detect_structure_issues


class PRGX1Sentry(BaseAgent):
    """Read-only repository scanner for dependency, structure, and integrity drift."""

    def __init__(self, bus, root: Path) -> None:
        super().__init__(agent_id="PRGX1", role="Sentry", bus=bus)
        self.root = root

    def detect_outdated_dependencies(self) -> list[str]:
        return scan_dependency_anomalies(self.root)

    def detect_structural_anomalies(self) -> list[str]:
        return detect_structure_issues(self.root)

    def detect_integrity_drift(self) -> list[str]:
        return scan_integrity_drift(self.root)

    @staticmethod
    def has_findings(report: Mapping[str, object]) -> bool:
        return bool(report.get("requires_fix", False))

    def _build_findings(self, category: str, issues: list[str]) -> list[Finding]:
        return [
            Finding(
                category=category,
                message=issue,
                metadata={"scanner": self.agent_id.lower()},
            )
            for issue in issues
        ]

    def scan_entropy(self) -> dict[str, Any]:
        dependency_issues = self.detect_outdated_dependencies()
        structural_issues = self.detect_structural_anomalies()
        integrity_issues = self.detect_integrity_drift()

        findings = [
            *self._build_findings("dependency", dependency_issues),
            *self._build_findings("structure", structural_issues),
            *self._build_findings("integrity", integrity_issues),
        ]

        report = IssueReport(
            target=str(self.root),
            dependency_issues=dependency_issues,
            structural_issues=structural_issues,
            integrity_issues=integrity_issues,
            issue_count=len(findings),
            requires_fix=bool(findings),
            findings=findings,
        )
        return report.model_dump()

    async def publish_issue_report(self) -> dict[str, Any]:
        report = self.scan_entropy()
        if not self.has_findings(report):
            self.logger.info(
                "No actionable findings detected; publishing %s for observability only.",
                ISSUE_REPORTED,
            )

        await self.publish(ISSUE_REPORTED, report)
        return report
