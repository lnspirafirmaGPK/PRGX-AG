from __future__ import annotations

from prgx_ag.schemas import ProcessingOutcome


def build_narrative(findings: dict[str, object], approved: bool, changed: list[str]) -> str:
    return (
        f"Detected={findings.get('summary', 'n/a')}; "
        f"Approved={approved}; Changed={', '.join(changed) if changed else 'none'}"
    )


def build_commit_style_narrative(outcome: ProcessingOutcome) -> str:
    status = 'fix' if outcome.success else 'blocked'
    return f"{status}: {outcome.message} (envelope={outcome.envelope_id})"
