import json
from pathlib import Path

from prgx_ag.services.governance_evidence import (
    append_audit_event,
    create_signed_governance_evidence_bundle,
)


def test_governance_evidence_bundle_is_signed(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / '.prgx-ag/audit').mkdir(parents=True)
    (repo_root / '.prgx-ag/evidence').mkdir(parents=True)
    (repo_root / '.prgx-ag/evidence/medical_research_findings.json').write_text(
        json.dumps([{'id': 'med-1', 'summary': 'finding'}]),
        encoding='utf-8',
    )

    append_audit_event(
        repo_root / '.prgx-ag/audit/audit_log.jsonl',
        event='porisjem.fix_completed',
        actor='PRGX2',
        details={'envelope_id': 'abc', 'verification_status': 'passed'},
    )

    path = create_signed_governance_evidence_bundle(
        repo_root,
        audit_window_hours=24,
        fix_plan_metadata={'envelope_id': 'abc', 'fix_count': 1},
        medical_findings_path='.prgx-ag/evidence/medical_research_findings.json',
        profile_name='staging',
    )

    payload = json.loads(path.read_text(encoding='utf-8'))
    assert payload['profile'] == 'staging'
    assert payload['fix_plan_metadata']['fix_count'] == 1
    assert payload['audit_records']
    assert payload['medical_research_findings']

    # Verify signature exists and matches bundle contents
    import hashlib
    assert 'signature' in payload
    signature_block = payload['signature']
    assert 'algorithm' in signature_block

    # Extract payload without signature
    bundle_without_sig = {k: v for k, v in payload.items() if k != 'signature'}
    canonical = json.dumps(bundle_without_sig, ensure_ascii=False, sort_keys=True)
    expected_digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()

    # Check if using real signature (RSA-PSS) or fallback (sha256)
    if signature_block['algorithm'] == 'RSA-PSS-SHA256':
        assert 'signature' in signature_block
        assert 'key_id' in signature_block
        assert signature_block['signature']  # Base64 encoded signature exists
    elif signature_block['algorithm'] == 'sha256':
        # Fallback mode - verify digest
        assert 'digest' in signature_block
        assert signature_block['digest'] == expected_digest
    else:
        raise AssertionError(f"Unexpected signature algorithm: {signature_block['algorithm']}")
