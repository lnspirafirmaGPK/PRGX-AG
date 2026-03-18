from pathlib import Path

import asyncio

import pytest

from prgx_ag.core import AetherBus
from prgx_ag.core.events import AUDIT_VIOLATION, EXECUTE_FIX, FIX_COMPLETED, INTENT_TRANSLATED, ISSUE_REPORTED
from prgx_ag.policy import PatimokkhaChecker
from prgx_ag.agents import PRGX1Sentry, PRGX2Mechanic, PRGX3Diplomat
from prgx_ag.services.github_bridge import format_pr_body, format_pr_title
from prgx_ag.services.narrative_builder import build_repair_narrative


def test_governed_repair_pipeline_generates_narrative_and_pr_report(tmp_path: Path) -> None:
    async def _run() -> None:
        bus = AetherBus(history_size=20)
        checker = PatimokkhaChecker()
        sentry = PRGX1Sentry(bus, root=tmp_path)
        diplomat = PRGX3Diplomat(bus, checker=checker)
        mechanic = PRGX2Mechanic(bus, tmp_path, checker, ['src/'], ['.git/'], dry_run=False)
    
        await diplomat.start()
    
        completed_payloads: list[dict[str, object]] = []
    
        async def execute_fix(payload: dict[str, object]) -> None:
            findings = payload['findings']
            target = str(findings['target']) if isinstance(findings, dict) else str(tmp_path)
            outcome = await mechanic.apply_shadow_fix(target, payload)
            await diplomat.report_result(outcome)
    
        async def collect_completed(payload: dict[str, object]) -> None:
            completed_payloads.append(payload)
    
        await bus.subscribe(EXECUTE_FIX, execute_fix)
        await bus.subscribe(FIX_COMPLETED, collect_completed)
    
        findings = {
            'summary': 'repository scan completed',
            'target': str(tmp_path),
            'dependency_issues': ['Dependency drift observed in pyproject.toml'],
            'structural_issues': ['Missing __init__.py in src/prgx_ag/api'],
            'integrity_issues': [],
            'issue_count': 2,
            'requires_fix': True,
        }
    
        await sentry.publish(ISSUE_REPORTED, findings)
    
        topics = [topic for topic, _ in bus.history]
        assert topics[:3] == [ISSUE_REPORTED, INTENT_TRANSLATED, EXECUTE_FIX]
        assert FIX_COMPLETED in topics
        assert completed_payloads
    
        completion = completed_payloads[0]
        outcome = completion['outcome']
        repair_narrative = build_repair_narrative(outcome)
        pr_title = format_pr_title(
            findings_summary=findings,
            audit_result='approved',
            verification_result='passed',
            fix_classes=outcome.details['fix_classes'],
        )
        pr_body = format_pr_body(
            findings_summary=findings,
            audit_result='approved',
            changed_files=outcome.details['changed'],
            verification_result='passed',
            rollback_instructions=outcome.details['rollback_hints'],
            fix_classes=outcome.details['fix_classes'],
            verification_commands=outcome.details['verification_commands'],
        )
    
        assert outcome.success is True
        assert outcome.details['payload_audit']['outcome'] == 'allow'
        assert repair_narrative.title == 'Repair applied successfully'
        assert 'Changed=src/prgx_ag/api/__init__.py' in repair_narrative.repaired
        assert 'PayloadAudit=present' in repair_narrative.learned
        assert pr_title.startswith('chore(prgx): heal')
        assert '- Issue count: 2' in pr_body
        assert '- src/prgx_ag/api/__init__.py' in pr_body
        assert 'compileall, pytest, ruff, mypy' in pr_body
        assert (tmp_path / 'src' / 'prgx_ag' / 'api' / '__init__.py').exists()
    
    
    asyncio.run(_run())
def test_governed_repair_pipeline_emits_audit_violation_for_hard_reject(tmp_path: Path) -> None:
    async def _run() -> None:
        bus = AetherBus(history_size=20)
        checker = PatimokkhaChecker()
        diplomat = PRGX3Diplomat(bus, checker=checker)
        violations: list[dict[str, object]] = []
    
        await diplomat.start()
    
        async def collect_violation(payload: dict[str, object]) -> None:
            violations.append(payload)
    
        await bus.subscribe(AUDIT_VIOLATION, collect_violation)
    
        findings = {
            'summary': 'wipe repository proposal detected',
            'target': str(tmp_path),
            'dependency_issues': [],
            'structural_issues': ['Missing __init__.py in src/prgx_ag/api'],
            'integrity_issues': ['Integrity drift detected: wipe repository'],
            'issue_count': 2,
            'requires_fix': True,
        }
    
        await diplomat.receive_issue_report(findings)
    
        topics = [topic for topic, _ in bus.history]
        assert INTENT_TRANSLATED in topics
        assert AUDIT_VIOLATION in topics
        assert EXECUTE_FIX not in topics
        assert violations[0]['audit']['outcome'] == 'reject'
        assert violations[0]['audit_status'].value == 'REJECTED'
    asyncio.run(_run())
