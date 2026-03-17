# PRGX-AG: Governed Self-Healing Core

PRGX-AG is a hybrid architecture where:
- `.github/workflows/` is the external GitHub orchestration layer.
- `.prgx-ag/` is the internal governance/manifest/state layer.
- `src/prgx_ag/` is the executable Python 3.11+ self-healing engine.

## System Architecture Diagram

```mermaid
flowchart TD
    GH[GitHub Actions\n(.github/workflows)] --> NX[PRGX-AG Nexus]
    NX --> B[AetherBus Events]
    B --> S1[PRGX1 Sentry\nRead-only scan]
    B --> S3[PRGX3 Diplomat\nIntent translation]
    S3 --> P[Patimokkha Governance]
    P -->|Approved| S2[PRGX2 Mechanic\nSafe fix executor]
    P -->|Rejected| AV[audit_violation]
    S2 --> FC[fix_completed]
    FC --> RSI[RSI Engine]
    RSI --> ST[.prgx-ag/state\nlearning_state.json\ngem_log.json]
    NX --> AUD[.prgx-ag/audit/audit_log.jsonl]
```

## System Status (Data/State Structure)

| Subsystem | Source of truth | Status detail |
|---|---|---|
| Governance policy | `.prgx-ag/policy/*.yaml` | Blocks destructive intents and protected-path writes |
| Operational workflows | `.prgx-ag/workflows/*.yaml` | Includes scan-only and self-heal cycles |
| Structure contract | `.prgx-ag/manifests/*.yaml` | Expected/critical/writable/protected definitions |
| Runtime learning | `.prgx-ag/state/*.json` | Bounded RSI state and gem log |
| Audit trail | `.prgx-ag/audit/audit_log.jsonl` | Reserved for violation and cycle evidence |

## PRGX Triad
- **PRGX1 Sentry**: scans dependencies + structure, emits `porisjem.issue_reported`.
- **PRGX3 Diplomat**: translates findings into healing intents and narratives.
- **PRGX2 Mechanic**: only writer; executes approved, reversible fixes inside allowlisted paths.

## Patimokkha Governance
Blocked examples: `delete_core`, `shutdown_nexus`, `exploit`, destructive recursion, unsafe infinite loops, mass deletion, protected-path modification.

## Event Topics
- `porisjem.issue_reported`
- `porisjem.intent_translated`
- `porisjem.execute_fix`
- `porisjem.fix_completed`
- `porisjem.audit_violation`
- `porisjem.rsi_feedback`

## Local Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Run
```bash
python -m prgx_ag.main --once
python -m prgx_ag.main --continuous --interval 10
python -m prgx_ag.main --scan-only
```

## Safe PR-first operation
- Use `PRGX_AG_DRY_RUN=true` by default.
- Workflows run scan/heal in non-destructive mode and produce artifacts.
- Tokens/keys are read from env/GitHub Secrets only.

## Test
```bash
pytest
```
