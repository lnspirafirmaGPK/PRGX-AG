from prgx_ag.agents.prgx3_diplomat import PRGX3Diplomat
from prgx_ag.core.aetherbus import AetherBus
from prgx_ag.schemas.enums import EthicalStatus


def test_prgx3_translation() -> None:
    diplomat = PRGX3Diplomat(agent_id='PRGX3', role='Diplomat', bus=AetherBus())
    assert 'stable' in diplomat.translate_to_world(EthicalStatus.CLEAN).lower()
