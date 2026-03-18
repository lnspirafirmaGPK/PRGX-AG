from pathlib import Path

import asyncio

import pytest

from prgx_ag.agents.prgx2_mechanic import PRGX2Mechanic
from prgx_ag.core.aetherbus import AetherBus
from prgx_ag.policy import PatimokkhaChecker
from prgx_ag.schemas import AuditStatus, Intent


def test_prgx2_requires_approved_intent(tmp_path: Path) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/'], ['.git/'])
        payload = {'envelope_id': 'e1', 'intent': Intent(id='1', source_agent='a', description='safe fix', target_firma='repo'), 'audit_status': AuditStatus.REJECTED, 'fixes': []}
        out = await mech.apply_shadow_fix('repo', payload)
        assert out.success is False
    
    
    asyncio.run(_run())
def test_protected_path_write_blocked(tmp_path: Path) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/'], ['.git/'])
        payload = {
            'envelope_id': 'e2',
            'intent': Intent(id='2', source_agent='a', description='safe fix', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'fixes': [{'path': '.git/config', 'content': 'x'}],
        }
        out = await mech.apply_shadow_fix('repo', payload)
        assert out.success is False
    
    
    asyncio.run(_run())
@pytest.mark.parametrize(
    ('fixes', 'expected_message'),
    [
        ('not-a-list', 'Invalid fixes payload'),
        ([{'content': 'x'}], 'Invalid fixes payload'),
        ([{'path': 'src/example.py', 'content': object()}], 'Safe fixes applied'),
    ],
)
def test_prgx2_invalid_fix_payload_regressions(tmp_path: Path, fixes: object, expected_message: str) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/'], ['.git/'], dry_run=True)
        payload = {
            'envelope_id': 'invalid-fixes',
            'intent': Intent(id='intent-invalid', source_agent='agent', description='Apply safe repair', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'fixes': fixes,
        }
    
        out = await mech.apply_shadow_fix('repo', payload)
    
        assert out.message == expected_message
        if expected_message == 'Safe fixes applied':
            assert out.success is True
            assert out.details['changed'] == ['src/example.py']
        else:
            assert out.success is False
    
    
    asyncio.run(_run())
def test_prgx2_blocks_empty_fix_plan_even_if_approved(tmp_path: Path) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/'], ['.git/'], dry_run=True)
        payload = {
            'envelope_id': 'empty-fixes',
            'intent': Intent(id='intent-empty', source_agent='agent', description='Apply safe repair', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'fixes': [],
        }
    
        out = await mech.apply_shadow_fix('repo', payload)
    
        assert out.success is False
        assert out.message == 'No executable fixes supplied'
        assert out.details['fix_count'] == 0
    
    
    asyncio.run(_run())
def test_prgx2_blocks_path_traversal_attempt(tmp_path: Path) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/'], ['.git/'], dry_run=True)
        payload = {
            'envelope_id': 'traversal',
            'intent': Intent(id='intent-traversal', source_agent='agent', description='Apply safe repair', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'fixes': [{'path': 'src/../../secrets.txt', 'content': 'x'}],
        }
    
        out = await mech.apply_shadow_fix('repo', payload)
    
        assert out.success is False
        assert out.message == 'Path not allowed: src/../../secrets.txt'
    
    
    asyncio.run(_run())
def test_prgx2_applies_duplicate_fix_entries_as_audited_plan(tmp_path: Path) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/'], ['.git/'], dry_run=False)
        payload = {
            'envelope_id': 'duplicate-fixes',
            'intent': Intent(id='intent-duplicate', source_agent='agent', description='Apply safe package marker repair', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'audit': {'outcome': 'allow', 'review': 'retained'},
            'fixes': [
                {
                    'path': 'src/pkg/__init__.py',
                    'content': '',
                    'fix_class': 'structural.package_marker',
                    'verification_commands': ['compileall'],
                    'rollback_hint': 'Remove package marker if package is retired.',
                },
                {
                    'path': 'src/pkg/__init__.py',
                    'content': '',
                    'fix_class': 'structural.package_marker',
                    'verification_commands': ['pytest'],
                    'rollback_hint': 'Revert duplicate fix entry.',
                },
            ],
        }
    
        out = await mech.apply_shadow_fix('repo', payload)
    
        assert out.success is True
        assert out.details['fix_count'] == 2
        assert out.details['changed'] == ['src/pkg/__init__.py', 'src/pkg/__init__.py']
        assert out.details['verification_commands'] == ['compileall', 'pytest']
        assert out.details['rollback_hints'] == [
            'Remove package marker if package is retired.',
            'Revert duplicate fix entry.',
        ]
        assert out.details['payload_audit'] == {'outcome': 'allow', 'review': 'retained'}
        assert (tmp_path / 'src' / 'pkg' / '__init__.py').exists()
    asyncio.run(_run())
