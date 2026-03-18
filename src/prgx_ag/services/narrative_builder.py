from __future__ import annotations

from prgx_ag.schemas import ProcessingOutcome, RepairNarrative


def _coerce_str(value: object, default: str = "n/a") -> str:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or default

    if value is None:
        return default

    return str(value)


def _coerce_bool(value: object, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "y", "on"}:
            return True
        if lowered in {"false", "0", "no", "n", "off"}:
            return False

    return default


def _coerce_list_of_str(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized: list[str] = []
    for item in value:
        if isinstance(item, str):
            text = item.strip()
            if text:
                normalized.append(text)
    return normalized


def _details_of(outcome: ProcessingOutcome) -> dict[str, object]:
    return outcome.details if isinstance(outcome.details, dict) else {}


def _mode_label(outcome: ProcessingOutcome) -> str:
    details = _details_of(outcome)
    dry_run = _coerce_bool(details.get("dry_run"), default=False)

    if outcome.success and dry_run:
        return "dry-run"
    if outcome.success:
        return "fix"
    return "blocked"


def _title_for(outcome: ProcessingOutcome) -> str:
    mode = _mode_label(outcome)

    if mode == "dry-run":
        return "Dry-run repair review completed"
    if mode == "fix":
        return "Repair applied successfully"
    return "Repair execution blocked"


def _detected_for(outcome: ProcessingOutcome) -> str:
    details = _details_of(outcome)
    target = _coerce_str(details.get("target"), default="repository")
    audit_reason = _coerce_str(details.get("audit_reason"), default="")
    fix_count = details.get("fix_count")

    segments: list[str] = [f"Target={target}"]

    if isinstance(fix_count, int):
        segments.append(f"PlannedFixes={fix_count}")

    if audit_reason and audit_reason != "n/a":
        segments.append(f"Audit={audit_reason}")

    segments.append(f"Message={outcome.message}")
    return " | ".join(segments)


def _repaired_for(outcome: ProcessingOutcome) -> str:
    details = _details_of(outcome)
    changed = _coerce_list_of_str(details.get("changed"))
    dry_run = _coerce_bool(details.get("dry_run"), default=False)

    if changed:
        changed_preview = ", ".join(changed[:5])
        if len(changed) > 5:
            changed_preview += f", +{len(changed) - 5} more"
    else:
        changed_preview = "none"

    if outcome.success and dry_run:
        return f"Validated safe fix set without writing files. Changed={changed_preview}"

    if outcome.success:
        return f"Applied safe fixes. Changed={changed_preview}"

    return f"No repair applied. Changed={changed_preview}"


def _learned_for(outcome: ProcessingOutcome) -> str:
    details = _details_of(outcome)
    payload_audit = details.get("payload_audit")
    audit_reason = _coerce_str(details.get("audit_reason"), default="")
    execution_time = f"{outcome.execution_time:.4f}s"

    notes: list[str] = [f"ExecutionTime={execution_time}"]

    if audit_reason and audit_reason != "n/a":
        notes.append(f"Guardrail={audit_reason}")

    if isinstance(payload_audit, dict) and payload_audit:
        notes.append("PayloadAudit=present")

    return " | ".join(notes)


def build_narrative(
    findings: dict[str, object],
    approved: bool,
    changed: list[str],
) -> str:
    summary = _coerce_str(findings.get("summary"), default="repository scan completed")
    target = _coerce_str(findings.get("target"), default="repository")
    issue_count = findings.get("issue_count", "n/a")
    changed_text = ", ".join(changed) if changed else "none"

    return (
        f"Detected={summary} | "
        f"Target={target} | "
        f"IssueCount={issue_count} | "
        f"Approved={approved} | "
        f"Changed={changed_text}"
    )


def build_repair_narrative(outcome: ProcessingOutcome) -> RepairNarrative:
    return RepairNarrative(
        title=_title_for(outcome),
        detected=_detected_for(outcome),
        repaired=_repaired_for(outcome),
        learned=_learned_for(outcome),
    )


def build_commit_style_narrative(outcome: ProcessingOutcome) -> str:
    mode = _mode_label(outcome)
    details = _details_of(outcome)

    changed = _coerce_list_of_str(details.get("changed"))
    changed_text = ", ".join(changed[:5]) if changed else "none"
    if len(changed) > 5:
        changed_text += f", +{len(changed) - 5} more"

    target = _coerce_str(details.get("target"), default="repository")
    fix_count = details.get("fix_count")
    fix_count_text = str(fix_count) if isinstance(fix_count, int) else "n/a"

    return (
        f"{mode}: {outcome.message} | "
        f"target={target} | "
        f"fixes={fix_count_text} | "
        f"changed={changed_text} | "
        f"elapsed={outcome.execution_time:.4f}s | "
        f"envelope={outcome.envelope_id}"
    )
