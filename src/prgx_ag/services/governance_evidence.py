from __future__ import annotations

import hashlib
import json
import os
import base64
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, ValueError):
        return None


def _read_audit_slice(audit_log: Path, *, hours: int) -> list[dict[str, Any]]:
    if not audit_log.exists():
        return []

    cutoff = _utc_now() - timedelta(hours=max(hours, 1))
    rows: list[dict[str, Any]] = []
    for line in audit_log.read_text(encoding='utf-8').splitlines():
        record = line.strip()
        if not record:
            continue
        try:
            payload = json.loads(record)
        except json.JSONDecodeError:
            continue
        ts_raw = payload.get('ts')
        if not isinstance(ts_raw, str):
            continue
        try:
            ts = datetime.fromisoformat(ts_raw.replace('Z', '+00:00'))
        except ValueError:
            continue
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts >= cutoff:
            rows.append(payload)
    return rows


def _resolve_safe_path(repo_root: Path, requested_path: str) -> Path:
    root = repo_root.resolve()
    candidate = (root / requested_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"Path escapes repository root: {requested_path}") from exc
    return candidate


def _sign_payload(canonical_payload: str) -> dict[str, str]:
    key_data = os.getenv('PRGX_GOVERNANCE_PRIVATE_KEY_PEM', '').strip()
    key_id = os.getenv('PRGX_GOVERNANCE_SIGNING_KEY_ID', 'configured-private-key')
    if key_data:
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding, rsa
        except Exception:
            key_data = ''

    if key_data:
        private_key = serialization.load_pem_private_key(key_data.encode('utf-8'), password=None)
        payload_bytes = canonical_payload.encode('utf-8')
        algorithm = 'rsa-pss-sha256'

        if isinstance(private_key, rsa.RSAPrivateKey):
            signature = private_key.sign(
                payload_bytes,
                padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.MAX_LENGTH),
                hashes.SHA256(),
            )
        elif isinstance(private_key, ec.EllipticCurvePrivateKey):
            signature = private_key.sign(payload_bytes, ec.ECDSA(hashes.SHA256()))
            algorithm = 'ecdsa-sha256'
        elif isinstance(private_key, ed25519.Ed25519PrivateKey):
            signature = private_key.sign(payload_bytes)
            algorithm = 'ed25519'
        else:
            raise ValueError('Unsupported signing key type')

        return {
            'algorithm': algorithm,
            'value': base64.b64encode(signature).decode('ascii'),
            'key_id': key_id,
        }

    digest = hashlib.sha256(canonical_payload.encode('utf-8')).hexdigest()
    return {
        'algorithm': 'sha256',
        'value': digest,
        'key_id': 'content-digest',
    }


def append_audit_event(audit_log: Path, *, event: str, actor: str, details: dict[str, Any]) -> None:
    audit_log.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'ts': _utc_now().isoformat(),
        'event': event,
        'actor': actor,
        'details': details,
    }
    with audit_log.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + '\n')


def create_signed_governance_evidence_bundle(
    repo_root: Path,
    *,
    audit_window_hours: int,
    fix_plan_metadata: dict[str, Any],
    medical_findings_path: str,
    profile_name: str,
) -> Path:
    audit_log = repo_root / '.prgx-ag/audit/audit_log.jsonl'
    medical_path = _resolve_safe_path(repo_root, medical_findings_path)
    evidence_dir = repo_root / '.prgx-ag/artifacts/compliance'
    evidence_dir.mkdir(parents=True, exist_ok=True)

    medical_findings = _read_json(medical_path)
    if not isinstance(medical_findings, list):
        medical_findings = []

    audit_slice = _read_audit_slice(audit_log, hours=audit_window_hours)

    payload = {
        'created_at': _utc_now().isoformat(),
        'profile': profile_name,
        'audit_window_hours': audit_window_hours,
        'audit_records': audit_slice,
        'fix_plan_metadata': fix_plan_metadata,
        'medical_research_findings': medical_findings,
        'compliance_statement': 'Governance evidence bundle generated from bounded PRGX-AG runtime records.',
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    signed_bundle = {
        **payload,
        'signature': _sign_payload(canonical),
    }

    stamp = _utc_now().strftime('%Y%m%d-%H%M%S')
    out_path = evidence_dir / f'governance-evidence-{stamp}.json'
    out_path.write_text(json.dumps(signed_bundle, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return out_path
