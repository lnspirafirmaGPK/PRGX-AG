from prgx_ag.policy import PatimokkhaChecker
from prgx_ag.schemas import EthicalStatus, Intent


def test_patimokkha_blocks_destructive_intent() -> None:
    checker = PatimokkhaChecker()
    intent = Intent(id='1', source_agent='x', description='mass deletion now', target_firma='repo')
    result = checker.validate_intent(intent)
    assert result.is_allowed is False
    assert result.status == EthicalStatus.PARAJIKA
