from pathlib import Path

import asyncio

import pytest

from prgx_ag.config import Settings
from prgx_ag.core.events import AUDIT_VIOLATION, EXECUTE_FIX, FIX_COMPLETED, ISSUE_REPORTED
from prgx_ag.orchestrator import PRGX_AG_Nexus


def test_full_nexus_cycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _run() -> None:
        (tmp_path / 'README.md').write_text('x', encoding='utf-8')
        (tmp_path / 'pyproject.toml').write_text('[project]\ndependencies=[]\n', encoding='utf-8')
        (tmp_path / 'src' / 'prgx_ag' / 'new_pkg').mkdir(parents=True)
        (tmp_path / 'src' / 'prgx_ag' / '__init__.py').write_text('', encoding='utf-8')
        (tmp_path / 'src' / 'prgx_ag' / 'new_pkg' / 'module.py').write_text('VALUE = 1\n', encoding='utf-8')
        (tmp_path / 'tests').mkdir()
    
        monkeypatch.setenv('PRGX_AG_REPO_ROOT', str(tmp_path))
        monkeypatch.setenv('PRGX_AG_DRY_RUN', 'true')
        settings = Settings()
        nexus = PRGX_AG_Nexus(settings)
        nexus.rsi_engine.analyze = lambda outcome: None
        await nexus.run_once()
    
        topics = [topic for topic, _ in nexus.bus.history]
        assert ISSUE_REPORTED in topics
        assert EXECUTE_FIX in topics
        assert FIX_COMPLETED in topics
    
        fix_completed_payload = next(payload for topic, payload in nexus.bus.history if topic == FIX_COMPLETED)
        outcome = fix_completed_payload['outcome']
        assert outcome.success is True
        assert outcome.details['dry_run'] is True
        assert outcome.details['target'] == str(tmp_path)
        assert outcome.details['fix_count'] == 1
        assert outcome.details['changed'] == ['src/prgx_ag/new_pkg/__init__.py']
        assert outcome.details['fix_classes'] == ['structural.package_marker']
        assert 'src/prgx_ag/new_pkg/__init__.py' in fix_completed_payload['narrative']
    
    
    asyncio.run(_run())
def test_nexus_cycle_persists_audit_metadata_for_realistic_findings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _run() -> None:
        findings_root = tmp_path / 'src' / 'prgx_ag' / 'feature' / 'nested'
        findings_root.mkdir(parents=True)
        (tmp_path / 'README.md').write_text('x', encoding='utf-8')
        (tmp_path / 'pyproject.toml').write_text('[project]\ndependencies=[]\n', encoding='utf-8')
        (tmp_path / 'src' / 'prgx_ag' / '__init__.py').write_text('', encoding='utf-8')
    
        monkeypatch.setenv('PRGX_AG_REPO_ROOT', str(tmp_path))
        monkeypatch.setenv('PRGX_AG_DRY_RUN', 'false')
        settings = Settings()
        nexus = PRGX_AG_Nexus(settings)
        nexus.rsi_engine.analyze = lambda outcome: None
        await nexus.wire_event_subscriptions()
    
        findings = {
            'summary': 'Repository scan found recoverable package marker drift',
            'target': str(tmp_path),
            'dependency_issues': ['Dependency drift observed in pyproject.toml'],
            'structural_issues': [
                'Missing __init__.py in src/prgx_ag/feature',
                'Missing __init__.py in src/prgx_ag/feature/nested',
            ],
            'integrity_issues': [],
            'issue_count': 3,
            'requires_fix': True,
        }
    
        await nexus.prgx1.publish(ISSUE_REPORTED, findings)
    
        payload = next(event for topic, event in nexus.bus.history if topic == FIX_COMPLETED)
        outcome = payload['outcome']
    
        assert outcome.success is True
        assert outcome.details['payload_audit']['outcome'] == 'allow'
        assert outcome.details['audit_reason'].startswith('Intent complies with Patimokkha principles')
        assert outcome.details['fix_count'] == 2
        assert outcome.details['changed'] == [
            'src/prgx_ag/feature/__init__.py',
            'src/prgx_ag/feature/nested/__init__.py',
        ]
        assert outcome.details['changed'].count('src/prgx_ag/feature/__init__.py') == 1
        assert outcome.details['changed'].count('src/prgx_ag/feature/nested/__init__.py') == 1
        assert 'Safe fixes applied' in payload['narrative']
        assert 'verification=compileall,pytest,ruff,mypy' not in payload['narrative']
    
    
    asyncio.run(_run())
def test_nexus_cycle_publishes_audit_violation_without_execution_for_hard_reject(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def _run() -> None:
        (tmp_path / 'README.md').write_text('x', encoding='utf-8')
        (tmp_path / 'pyproject.toml').write_text('[project]\ndependencies=[]\n', encoding='utf-8')
        (tmp_path / 'src' / 'prgx_ag').mkdir(parents=True)
        (tmp_path / 'src' / 'prgx_ag' / '__init__.py').write_text('', encoding='utf-8')
    
        monkeypatch.setenv('PRGX_AG_REPO_ROOT', str(tmp_path))
        monkeypatch.setenv('PRGX_AG_DRY_RUN', 'true')
        settings = Settings()
        nexus = PRGX_AG_Nexus(settings)
        nexus.rsi_engine.analyze = lambda outcome: None
        await nexus.wire_event_subscriptions()
    
        findings = {
            'summary': 'Repository scan surfaced wipe repository recovery proposal',
            'target': str(tmp_path),
            'dependency_issues': [],
            'structural_issues': ['Missing __init__.py in src/prgx_ag/danger_zone'],
            'integrity_issues': ['Integrity drift detected: wipe repository'],
            'issue_count': 2,
            'requires_fix': True,
        }
    
        await nexus.prgx1.publish(ISSUE_REPORTED, findings)
    
        topics = [topic for topic, _ in nexus.bus.history]
        assert AUDIT_VIOLATION in topics
        assert EXECUTE_FIX not in topics
        assert FIX_COMPLETED not in topics
    
        violation = next(payload for topic, payload in nexus.bus.history if topic == AUDIT_VIOLATION)
        assert violation['audit_status'].value == 'REJECTED'
        assert violation['audit']['outcome'] == 'reject'
    asyncio.run(_run())
