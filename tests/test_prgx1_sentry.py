from pathlib import Path

import asyncio

from prgx_ag.agents.prgx1_sentry import PRGX1Sentry
from prgx_ag.core.aetherbus import AetherBus


def test_prgx1_does_not_write_files(tmp_path: Path) -> None:
    async def _run() -> None:
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

    asyncio.run(_run())
