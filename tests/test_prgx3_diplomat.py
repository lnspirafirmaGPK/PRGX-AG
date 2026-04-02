import asyncio
from pathlib import Path
from unittest.mock import patch

from prgx_ag.agents.prgx3_diplomat import PRGX3Diplomat
from prgx_ag.core.aetherbus import AetherBus
from prgx_ag.core.events import EXECUTE_FIX
from prgx_ag.schemas.enums import EthicalStatus


def test_prgx3_translation() -> None:
    diplomat = PRGX3Diplomat(agent_id='PRGX3', role='Diplomat', bus=AetherBus())
    assert 'stable' in diplomat.translate_to_world(EthicalStatus.CLEAN).lower()


def test_prgx3_stores_runtime_profile() -> None:
    diplomat = PRGX3Diplomat(bus=AetherBus(), runtime_profile='production')
    assert diplomat.runtime_profile == 'production'


def test_prgx3_default_runtime_profile_is_development() -> None:
    diplomat = PRGX3Diplomat(bus=AetherBus())
    assert diplomat.runtime_profile == 'development'


def test_prgx3_issue_count_gate_skips_execution_when_exceeds_production_threshold(
    tmp_path: Path,
) -> None:
    """Production threshold is 12; a findings with 13 issues must not emit EXECUTE_FIX."""
    async def _run() -> None:
        bus = AetherBus(history_size=20)
        diplomat = PRGX3Diplomat(bus=bus, runtime_profile='production')
        await diplomat.start()

        findings = {
            'summary': 'scan completed',
            'target': str(tmp_path),
            'issue_count': 13,  # exceeds production max_issue_count_for_auto_fix=12
            'requires_fix': True,
            'structural_issues': [],
            'dependency_issues': [],
            'integrity_issues': [],
        }
        await diplomat.receive_issue_report(findings)

        topics = [topic for topic, _ in bus.history]
        assert EXECUTE_FIX not in topics

    asyncio.run(_run())


def test_prgx3_issue_count_gate_allows_execution_at_production_threshold(
    tmp_path: Path,
) -> None:
    """Production threshold is 12; exactly 12 issues must be allowed through."""
    async def _run() -> None:
        bus = AetherBus(history_size=20)
        diplomat = PRGX3Diplomat(bus=bus, runtime_profile='production')
        await diplomat.start()

        findings = {
            'summary': 'scan completed',
            'target': str(tmp_path),
            'issue_count': 12,  # equal to max; should not be blocked
            'requires_fix': True,
            'structural_issues': [],
            'dependency_issues': [],
            'integrity_issues': [],
        }
        # build_fix_plan may return empty list without real dir structure;
        # that is fine — we only assert EXECUTE_FIX is NOT suppressed by the gate
        with patch(
            'prgx_ag.agents.prgx3_diplomat.build_fix_plan',
            return_value=[{'action': 'test-fix', 'path': 'test'}],
        ):
            await diplomat.receive_issue_report(findings)

        # Verify the gate allowed execution by checking EXECUTE_FIX was published
        topics = [topic for topic, _ in bus.history]
        assert EXECUTE_FIX in topics

    asyncio.run(_run())


def test_prgx3_issue_count_aggregated_from_structural_and_dependency_lists(
    tmp_path: Path,
) -> None:
    """When issue_count is not an int, it's summed from structural+dependency lists."""
    async def _run() -> None:
        bus = AetherBus(history_size=20)
        # staging threshold=30; 31 items should block
        diplomat = PRGX3Diplomat(bus=bus, runtime_profile='staging')
        await diplomat.start()

        findings = {
            'summary': 'scan completed',
            'target': str(tmp_path),
            # issue_count missing — force aggregation
            'structural_issues': [f'issue-{i}' for i in range(20)],
            'dependency_issues': [f'dep-{i}' for i in range(11)],  # total=31
            'integrity_issues': [],
            'requires_fix': True,
        }
        await diplomat.receive_issue_report(findings)

        topics = [topic for topic, _ in bus.history]
        assert EXECUTE_FIX not in topics

    asyncio.run(_run())


def test_prgx3_issue_count_aggregation_below_threshold_is_not_blocked(
    tmp_path: Path,
) -> None:
    """Aggregated count below staging threshold must not be suppressed by the gate."""
    async def _run() -> None:
        bus = AetherBus(history_size=20)
        diplomat = PRGX3Diplomat(bus=bus, runtime_profile='staging')
        await diplomat.start()

        findings = {
            'summary': 'scan completed',
            'target': str(tmp_path),
            # No issue_count; aggregated: 1+1=2, well below staging threshold of 30
            'structural_issues': ['one structural'],
            'dependency_issues': ['one dep'],
            'integrity_issues': [],
            'requires_fix': True,
        }
        with patch(
            'prgx_ag.agents.prgx3_diplomat.build_fix_plan',
            return_value=[{'action': 'test-fix', 'path': 'test'}],
        ):
            await diplomat.receive_issue_report(findings)

        # Verify the gate allowed execution by checking EXECUTE_FIX was published
        topics = [topic for topic, _ in bus.history]
        assert EXECUTE_FIX in topics

    asyncio.run(_run())


def test_prgx3_non_actionable_report_does_not_publish_any_events(
    tmp_path: Path,
) -> None:
    """requires_fix=False must not result in any event publications."""
    async def _run() -> None:
        bus = AetherBus(history_size=20)
        diplomat = PRGX3Diplomat(bus=bus, runtime_profile='development')
        await diplomat.start()

        findings = {
            'summary': 'all clear',
            'target': str(tmp_path),
            'issue_count': 0,
            'requires_fix': False,
            'structural_issues': [],
            'dependency_issues': [],
            'integrity_issues': [],
        }
        await diplomat.receive_issue_report(findings)

        # The only subscribed event is ISSUE_REPORTED which happens upstream;
        # diplomat itself should publish nothing when not actionable
        topics = [topic for topic, _ in bus.history]
        assert not topics

    asyncio.run(_run())


def test_prgx3_fix_count_capped_at_profile_max_auto_fix_items(
    tmp_path: Path,
) -> None:
    """build_fix_plan returning more items than max_auto_fix_items must be capped."""
    async def _run() -> None:
        bus = AetherBus(history_size=20)
        # production: max_auto_fix_items=5, max_issue_count_for_auto_fix=12
        diplomat = PRGX3Diplomat(bus=bus, runtime_profile='production')
        await diplomat.start()

        execute_fix_payloads: list[dict] = []

        async def capture(payload: dict) -> None:
            execute_fix_payloads.append(payload)

        await bus.subscribe(EXECUTE_FIX, capture)

        # Return 8 fake fix items from build_fix_plan — cap should reduce to 5
        fake_fixes = [{'action': f'fix-{i}', 'path': 'x'} for i in range(8)]

        findings = {
            'summary': 'scan completed',
            'target': str(tmp_path),
            'issue_count': 8,  # within production threshold of 12
            'requires_fix': True,
            'structural_issues': [f's{i}' for i in range(8)],
            'dependency_issues': [],
            'integrity_issues': [],
        }

        with patch(
            'prgx_ag.agents.prgx3_diplomat.build_fix_plan',
            return_value=fake_fixes,
        ):
            await diplomat.receive_issue_report(findings)

        assert execute_fix_payloads, 'EXECUTE_FIX was not published'
        assert len(execute_fix_payloads[0]['fixes']) == 5

    asyncio.run(_run())


def test_prgx3_fix_count_not_truncated_when_below_cap(
    tmp_path: Path,
) -> None:
    """When fix count is within profile cap, all fixes are passed through."""
    async def _run() -> None:
        bus = AetherBus(history_size=20)
        diplomat = PRGX3Diplomat(bus=bus, runtime_profile='production')
        await diplomat.start()

        execute_fix_payloads: list[dict] = []

        async def capture(payload: dict) -> None:
            execute_fix_payloads.append(payload)

        await bus.subscribe(EXECUTE_FIX, capture)

        # Return 3 items — well below production cap of 5
        fake_fixes = [{'action': f'fix-{i}', 'path': 'x'} for i in range(3)]

        findings = {
            'summary': 'scan completed',
            'target': str(tmp_path),
            'issue_count': 3,
            'requires_fix': True,
            'structural_issues': [],
            'dependency_issues': [],
            'integrity_issues': [],
        }

        with patch(
            'prgx_ag.agents.prgx3_diplomat.build_fix_plan',
            return_value=fake_fixes,
        ):
            await diplomat.receive_issue_report(findings)

        assert execute_fix_payloads, 'EXECUTE_FIX was not published'
        assert len(execute_fix_payloads[0]['fixes']) == 3

    asyncio.run(_run())