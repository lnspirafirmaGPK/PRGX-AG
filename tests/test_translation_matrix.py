from prgx_ag.schemas.enums import EthicalStatus
from prgx_ag.services.translation_matrix import translate_internal_term, translate_status


def test_translation_matrix_mappings() -> None:
    assert translate_internal_term('Parajika') == 'SYSTEM_HALT_IMMEDIATE'
    assert 'stable' in translate_status(EthicalStatus.CLEAN).lower()
