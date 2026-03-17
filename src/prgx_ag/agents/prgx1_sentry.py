from __future__ import annotations

from pathlib import Path

from prgx_ag.core import BaseAgent
from prgx_ag.core.events import ISSUE_REPORTED
from prgx_ag.services.dependency_scanner import scan_dependency_anomalies
from prgx_ag.services.structure_scanner import detect_structure_issues


class PRGX1Sentry(BaseAgent):
    def __init__(self, bus, root: Path) -> None:
        super().__init__(agent_id='PRGX1', role='Sentry', bus=bus)
        self.root = root

    def scan_entropy(self) -> dict[str, object]:
        dep_issues = scan_dependency_anomalies(self.root)
        structural_issues = detect_structure_issues(self.root)
        all_issues = dep_issues + structural_issues
        return {
            'summary': 'repository scan completed',
            'target': str(self.root),
            'dependency_issues': dep_issues,
            'structural_issues': structural_issues,
            'requires_fix': bool(all_issues),
        }

    async def publish_issue_report(self) -> dict[str, object]:
        report = self.scan_entropy()
        await self.publish(ISSUE_REPORTED, report)
        return report
