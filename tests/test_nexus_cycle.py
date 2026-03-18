from pathlib import Path

import pytest

from prgx_ag.config import Settings
from prgx_ag.orchestrator import PRGX_AG_Nexus


@pytest.mark.asyncio
async def test_full_nexus_cycle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / 'README.md').write_text('x', encoding='utf-8')
    (tmp_path / 'src' / 'prgx_ag').mkdir(parents=True)
    (tmp_path / 'src' / 'prgx_ag' / 'module').mkdir(parents=True)
    (tmp_path / 'src' / 'prgx_ag' / 'module' / 'worker.py').write_text('VALUE = 1\n', encoding='utf-8')
    (tmp_path / 'tests').mkdir()

    monkeypatch.setenv('PRGX_AG_REPO_ROOT', str(tmp_path))
    settings = Settings(dry_run=True)
    nexus = PRGX_AG_Nexus(settings)
    await nexus.run_once()

    topics = [topic for topic, _ in nexus.bus.history]
    assert 'porisjem.issue_reported' in topics
    assert 'porisjem.execute_fix' in topics
    assert 'porisjem.fix_completed' in topics
