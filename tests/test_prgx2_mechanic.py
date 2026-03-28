from pathlib import Path

import asyncio

import pytest

from prgx_ag.agents.prgx2_mechanic import PRGX2Mechanic
from prgx_ag.core.aetherbus import AetherBus
from prgx_ag.policy import PatimokkhaChecker
from prgx_ag.schemas import AuditStatus, Intent


def test_prgx2_requires_approved_intent(tmp_path: Path) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/', 'pyproject.toml'], ['.git/'])
        payload = {'envelope_id': 'e1', 'intent': Intent(id='1', source_agent='a', description='safe fix', target_firma='repo'), 'audit_status': AuditStatus.REJECTED, 'fixes': []}
        out = await mech.apply_shadow_fix('repo', payload)
        assert out.success is False
    asyncio.run(_run())


def test_protected_path_write_blocked(tmp_path: Path) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/', 'pyproject.toml'], ['.git/'])
        payload = {
            'envelope_id': 'e2',
            'intent': Intent(id='2', source_agent='a', description='safe fix', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'fixes': [{'path': '.git/config', 'content': 'x', 'fix_class': 'create_empty_init', 'validator': 'validate_empty_init_fix'}],
        }
        out = await mech.apply_shadow_fix('repo', payload)
        assert out.success is False
    asyncio.run(_run())


@pytest.mark.parametrize(
    ('fixes', 'expected_message'),
    [
        ('not-a-list', 'Invalid fixes payload'),
        ([{'content': 'x'}], 'Invalid fixes payload'),
        ([{'path': 'src/example.py', 'content': object()}], 'Unsupported fix class: unknown'),
    ],
)
def test_prgx2_invalid_fix_payload_regressions(tmp_path: Path, fixes: object, expected_message: str) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/', 'pyproject.toml'], ['.git/'], dry_run=True)
        payload = {
            'envelope_id': 'invalid-fixes',
            'intent': Intent(id='intent-invalid', source_agent='agent', description='Apply safe repair', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'fixes': fixes,
        }
        out = await mech.apply_shadow_fix('repo', payload)
        assert out.message == expected_message
        assert out.success is False
    asyncio.run(_run())


def test_prgx2_blocks_empty_fix_plan_even_if_approved(tmp_path: Path) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/', 'pyproject.toml'], ['.git/'], dry_run=True)
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
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/', 'pyproject.toml'], ['.git/'], dry_run=True)
        payload = {
            'envelope_id': 'traversal',
            'intent': Intent(id='intent-traversal', source_agent='agent', description='Apply safe repair', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'fixes': [{'path': 'src/../../secrets.txt', 'content': 'x', 'fix_class': 'create_empty_init', 'validator': 'validate_empty_init_fix'}],
        }
        out = await mech.apply_shadow_fix('repo', payload)
        assert out.success is False
        assert out.message == 'create_empty_init requires an __init__.py target'
    asyncio.run(_run())


def test_prgx2_applies_duplicate_fix_entries_as_audited_plan(tmp_path: Path) -> None:
    async def _run() -> None:
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/', 'pyproject.toml'], ['.git/'], dry_run=False)
        payload = {
            'envelope_id': 'duplicate-fixes',
            'intent': Intent(id='intent-duplicate', source_agent='agent', description='Apply safe package marker repair', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'audit': {'outcome': 'allow', 'review': 'retained'},
            'fixes': [
                {
                    'path': 'src/pkg/__init__.py',
                    'content': '',
                    'fix_class': 'create_empty_init',
                    'validator': 'validate_empty_init_fix',
                    'verification_commands': ['compileall'],
                    'rollback_hint': 'Remove package marker if package is retired.',
                },
                {
                    'path': 'src/pkg/__init__.py',
                    'content': '',
                    'fix_class': 'create_empty_init',
                    'validator': 'validate_empty_init_fix',
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
        assert out.details['rollback_hints'] == ['Remove package marker if package is retired.', 'Revert duplicate fix entry.']
        assert out.details['verification_status'] == 'passed'
        assert len(out.details['snapshots']) == 2
        assert out.details['payload_audit'] == {'outcome': 'allow', 'review': 'retained'}
        assert (tmp_path / 'src' / 'pkg' / '__init__.py').exists()
    asyncio.run(_run())


def test_prgx2_dependency_bump_records_snapshot_and_verification(tmp_path: Path) -> None:
    async def _run() -> None:
        pyproject = tmp_path / 'pyproject.toml'
        pyproject.write_text('[project]\ndependencies = [\n  "pydantic>=2.5,<3",\n]\n', encoding='utf-8')
        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/', 'pyproject.toml'], ['.git/'], dry_run=False)
        outcome = await mech.update_dependency('pyproject.toml', 'Allowlisted dependency bump in pyproject.toml: pydantic -> >=2.6,<3')
        assert outcome.success is True
        assert outcome.details['fix_classes'] == ['dependency_bump']
        assert outcome.details['verification_status'] == 'passed'
        assert outcome.details['snapshots'][0]['previous_content'].startswith('[project]')
        assert 'pydantic>=2.6,<3' in pyproject.read_text(encoding='utf-8')
    asyncio.run(_run())


def test_prgx2_dry_run_dependency_bump_keeps_repository_unchanged(tmp_path: Path) -> None:
    async def _run() -> None:
        pyproject = tmp_path / 'pyproject.toml'
        original = '[project]\ndependencies = [\n  "pydantic>=2.5,<3",\n]\n'
        pyproject.write_text(original, encoding='utf-8')
        src_dir = tmp_path / 'src'
        assert not src_dir.exists()

        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/', 'pyproject.toml'], ['.git/'], dry_run=True)
        outcome = await mech.update_dependency('pyproject.toml', 'Allowlisted dependency bump in pyproject.toml: pydantic -> >=2.6,<3')

        assert outcome.success is True
        assert outcome.details['verification_status'] == 'passed'
        assert pyproject.read_text(encoding='utf-8') == original
        assert not src_dir.exists()
    asyncio.run(_run())


def test_prgx2_dry_run_marks_unwritable_create_empty_init_as_failed_verification(tmp_path: Path) -> None:
    async def _run() -> None:
        blocking_path = tmp_path / 'src' / 'pkg'
        blocking_path.parent.mkdir(parents=True, exist_ok=True)
        blocking_path.write_text('not-a-directory', encoding='utf-8')

        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['src/', 'pyproject.toml'], ['.git/'], dry_run=True)
        payload = {
            'envelope_id': 'dry-run-unwritable',
            'intent': Intent(id='intent-unwritable', source_agent='agent', description='Validate dry-run path feasibility', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'fixes': [
                {
                    'path': 'src/pkg/__init__.py',
                    'content': '',
                    'fix_class': 'create_empty_init',
                    'validator': 'validate_empty_init_fix',
                }
            ],
        }

        out = await mech.apply_shadow_fix('repo', payload)
        assert out.success is True
        assert out.details['verification_status'] == 'failed'
        assert out.details['verification_results'][0]['passed'] is False
        assert 'non-writable target path' in out.details['verification_results'][0]['summary']
    asyncio.run(_run())


def test_prgx2_dry_run_handles_symlinked_allowed_path_outside_repo(tmp_path: Path) -> None:
    async def _run() -> None:
        external_root = tmp_path.parent / f'{tmp_path.name}-external'
        external_root.mkdir(parents=True, exist_ok=True)
        symlink_root = tmp_path / 'linked'
        symlink_root.symlink_to(external_root, target_is_directory=True)

        mech = PRGX2Mechanic(AetherBus(), tmp_path, PatimokkhaChecker(), ['linked/'], ['.git/'], dry_run=True)
        payload = {
            'envelope_id': 'dry-run-symlink-outside',
            'intent': Intent(id='intent-symlink-outside', source_agent='agent', description='Validate dry-run path feasibility via symlink', target_firma='repo'),
            'audit_status': AuditStatus.APPROVED,
            'fixes': [
                {
                    'path': 'linked/pkg/__init__.py',
                    'content': '',
                    'fix_class': 'create_empty_init',
                    'validator': 'validate_empty_init_fix',
                }
            ],
        }

        out = await mech.apply_shadow_fix('repo', payload)
        assert out.success is True
        assert out.details['verification_status'] == 'failed'
        assert out.details['verification_results'][0]['passed'] is False
        assert 'escapes repo root' in out.details['verification_results'][0]['summary']
    asyncio.run(_run())
