from pathlib import Path

import pytest

from prgx_ag.agents.prgx1_sentry import PRGX1Sentry
from prgx_ag.core.aetherbus import AetherBus
from prgx_ag.core.events import ISSUE_REPORTED


@pytest.mark.asyncio
async def test_prgx1_does_not_write_files(tmp_path: Path) -> None:
    (tmp_path / 'README.md').write_text('x', encoding='utf-8')
    (tmp_path / 'pyproject.toml').write_text('[project]\ndependencies=[]\n', encoding='utf-8')
    (tmp_path / 'src' / 'pkg').mkdir(parents=True)
    (tmp_path / 'src' / 'pkg' / '__init__.py').write_text('', encoding='utf-8')
    (tmp_path / 'tests').mkdir()

    sentry = PRGX1Sentry(bus=AetherBus(), root=tmp_path)
    before = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.glob('**/*') if p.is_file())
    await sentry.publish_issue_report()
    after = sorted(p.relative_to(tmp_path).as_posix() for p in tmp_path.glob('**/*') if p.is_file())
    assert before == after


@pytest.mark.asyncio
async def test_prgx1_skips_publish_when_no_findings(tmp_path: Path) -> None:
    (tmp_path / 'README.md').write_text('x', encoding='utf-8')
    (tmp_path / 'pyproject.toml').write_text('[project]\ndependencies=[]\n', encoding='utf-8')
    (tmp_path / 'src' / 'pkg').mkdir(parents=True)
    (tmp_path / 'src' / 'pkg' / '__init__.py').write_text('', encoding='utf-8')
    (tmp_path / 'tests').mkdir()

    bus = AetherBus()
    sentry = PRGX1Sentry(bus=bus, root=tmp_path)

    report = await sentry.publish_issue_report()

    assert report['requires_fix'] is False
    assert report['issue_count'] == 0
    assert bus.history[0][0] == ISSUE_REPORTED


@pytest.mark.asyncio
async def test_prgx1_publishes_issue_report_with_structured_findings(tmp_path: Path) -> None:
    (tmp_path / 'README.md').write_text('x', encoding='utf-8')
    (tmp_path / 'src' / 'pkg').mkdir(parents=True)
    (tmp_path / 'src' / 'pkg' / '__init__.py').write_text('', encoding='utf-8')
    (tmp_path / 'tests').mkdir()

    bus = AetherBus()
    sentry = PRGX1Sentry(bus=bus, root=tmp_path)

    report = await sentry.publish_issue_report()

    assert report['requires_fix'] is True
    assert report['issue_count'] == len(report['findings'])
    assert any(finding['category'] == 'dependency' for finding in report['findings'])
    assert bus.history[0][0] == ISSUE_REPORTED
