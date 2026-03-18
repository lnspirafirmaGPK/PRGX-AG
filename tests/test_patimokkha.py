from prgx_ag.policy import PatimokkhaChecker
from prgx_ag.schemas import EthicalStatus, Intent


def test_patimokkha_rejects_destructive_metadata_command() -> None:
    checker = PatimokkhaChecker()
    intent = Intent(
        id="1",
        source_agent="x",
        description="Prepare maintenance plan",
        target_firma="repo",
        metadata={"operation_command": "rm -rf /"},
    )

    result = checker.validate_intent(intent)

    assert result.is_allowed is False
    assert result.status == EthicalStatus.PARAJIKA
    assert result.metadata["outcome"] == "reject"
    assert result.metadata["rule_fired"] == "data-rm-root"
    assert result.metadata["matched_fields"] == ["metadata.operation_command"]


def test_patimokkha_reviews_defensive_narrative_without_rejecting() -> None:
    checker = PatimokkhaChecker()
    intent = Intent(
        id="2",
        source_agent="audit-bot",
        description="Audit narrative for how to block mass deletion of backups",
        target_firma="repo",
    )

    result = checker.validate_intent(intent)

    assert result.is_allowed is True
    assert result.status == EthicalStatus.MINOR_INFRACTION
    assert result.metadata["outcome"] == "review_required"
    assert result.metadata["evaluation_mode"] == "contextual_review"
    assert result.metadata["matched_fields"] == ["description"]
    assert result.metadata["evidence"][0]["context_hint"] == "block"


def test_patimokkha_allows_safe_exported_shutdown_context() -> None:
    checker = PatimokkhaChecker()
    intent = Intent(
        id="3",
        source_agent="governance",
        description="Export the approved safe shutdown command for incident drills.",
        target_firma="repo",
        metadata={
            "ethical_status": "PARAJIKA",
            "exported_command": "graceful_shutdown",
            "audit_note": "defensive incident drill",
        },
    )

    result = checker.validate_intent(intent)

    assert result.is_allowed is True
    assert result.status == EthicalStatus.PARAJIKA
    assert result.metadata["outcome"] == "allow"
    assert result.metadata["evaluation_mode"] == "safe_operational_override"


def test_patimokkha_does_not_reject_harmless_narrative_mention_in_metadata_context() -> None:
    checker = PatimokkhaChecker()
    intent = Intent(
        id="4",
        source_agent="writer",
        description="Document defensive guidance for reviewers.",
        target_firma="repo",
        metadata={
            "audit_note": "Narrative example: privilege escalation should be rejected during review.",
        },
    )

    result = checker.validate_intent(intent)

    assert result.is_allowed is True
    assert result.status == EthicalStatus.CLEAN
    assert result.metadata["outcome"] == "allow"
    assert result.metadata["matched_fields"] == []


def test_patimokkha_rejects_malicious_variant_hidden_inside_metadata() -> None:
    checker = PatimokkhaChecker()
    intent = Intent(
        id="5",
        source_agent="x",
        description="Routine export",
        target_firma="repo",
        metadata={
            "execution_payload": {
                "shell_command": "python cleanup.py && rm -rf .",
                "comment": "hidden destructive suffix",
            }
        },
    )

    result = checker.validate_intent(intent)

    assert result.is_allowed is False
    assert result.status == EthicalStatus.PARAJIKA
    assert result.metadata["outcome"] == "reject"
    assert result.metadata["matched_fields"] == ["metadata.execution_payload"]
    assert result.metadata["evidence"][0]["pattern"] == "rm -rf ."


def test_patimokkha_keeps_review_only_contexts_out_of_hard_rejects() -> None:
    checker = PatimokkhaChecker()
    intent = Intent(
        id='6',
        source_agent='governance-reviewer',
        description='Review-only checklist documenting how to block privilege escalation attempts during incident response.',
        target_firma='repo',
        metadata={
            'audit_note': 'review-only escalation path for red-team simulation',
            'review_context': {'instructions': ['block privilege escalation attempts', 'document reject decision']},
        },
    )

    result = checker.validate_intent(intent)

    assert result.is_allowed is True
    assert result.status == EthicalStatus.MINOR_INFRACTION
    assert result.metadata['outcome'] == 'review_required'
    assert result.metadata['evaluation_mode'] == 'contextual_review'
    assert 'description' in result.metadata['matched_fields'] or 'metadata.review_context' in result.metadata['matched_fields']


def test_patimokkha_hard_rejects_operational_payload_without_safe_context() -> None:
    checker = PatimokkhaChecker()
    intent = Intent(
        id='7',
        source_agent='governance-reviewer',
        description='Routine governance update',
        target_firma='repo',
        metadata={
            'operation_plan': {
                'step': 'drop table accounts',
                'purpose': 'speed up maintenance',
            }
        },
    )

    result = checker.validate_intent(intent)

    assert result.is_allowed is False
    assert result.status == EthicalStatus.PARAJIKA
    assert result.metadata['outcome'] == 'reject'
    assert result.metadata['evaluation_mode'] == 'direct_block'
    assert result.metadata['matched_fields'] == ['metadata.operation_plan']
