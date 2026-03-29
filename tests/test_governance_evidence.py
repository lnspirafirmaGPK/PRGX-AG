import json
import hashlib
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
    assert payload['signature']['algorithm'] == 'sha256'
    assert payload['signature']['value']

    unsigned_payload = dict(payload)
    unsigned_payload.pop('signature', None)
    canonical = json.dumps(unsigned_payload, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(canonical.encode('utf-8')).hexdigest()
    assert payload['signature']['value'] == digest


def test_governance_evidence_handles_invalid_optional_findings(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / '.prgx-ag/audit').mkdir(parents=True)
    (repo_root / '.prgx-ag/evidence').mkdir(parents=True)
    (repo_root / '.prgx-ag/evidence/medical_research_findings.json').write_text('{invalid', encoding='utf-8')

    append_audit_event(
        repo_root / '.prgx-ag/audit/audit_log.jsonl',
        event='porisjem.fix_completed',
        actor='PRGX2',
        details={'envelope_id': 'abc'},
    )

    path = create_signed_governance_evidence_bundle(
        repo_root,
        audit_window_hours=24,
        fix_plan_metadata={'envelope_id': 'abc', 'fix_count': 1},
        medical_findings_path='.prgx-ag/evidence/medical_research_findings.json',
        profile_name='staging',
    )
    payload = json.loads(path.read_text(encoding='utf-8'))
    assert payload['medical_research_findings'] == []


def test_governance_evidence_blocks_path_escape(tmp_path: Path) -> None:
    repo_root = tmp_path
    (repo_root / '.prgx-ag/audit').mkdir(parents=True)
    append_audit_event(
        repo_root / '.prgx-ag/audit/audit_log.jsonl',
        event='porisjem.fix_completed',
        actor='PRGX2',
        details={'envelope_id': 'abc'},
    )

    try:
        create_signed_governance_evidence_bundle(
            repo_root,
            audit_window_hours=24,
            fix_plan_metadata={'envelope_id': 'abc', 'fix_count': 1},
            medical_findings_path='../../etc/passwd',
            profile_name='staging',
        )
    except ValueError:
        pass
    else:
        raise AssertionError('Expected path traversal to be rejected')
