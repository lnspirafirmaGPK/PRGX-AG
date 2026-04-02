from prgx_ag.config import RUNTIME_PROFILES, Settings


def test_runtime_profiles_have_distinct_controls() -> None:
    development = RUNTIME_PROFILES['development']
    staging = RUNTIME_PROFILES['staging']
    production = RUNTIME_PROFILES['production']

    # Assert exact expected constants for each profile
    assert development.max_auto_fix_items == 20
    assert development.max_issue_count_for_auto_fix == 60
    assert development.audit_verbosity == 'compact'
    assert development.evidence_signature_required is False

    assert staging.max_auto_fix_items == 12
    assert staging.max_issue_count_for_auto_fix == 30
    assert staging.audit_verbosity == 'standard'
    assert staging.evidence_signature_required is True

    assert production.max_auto_fix_items == 5
    assert production.max_issue_count_for_auto_fix == 12
    assert production.audit_verbosity == 'forensic'
    assert production.evidence_signature_required is True


def test_settings_exposes_profile() -> None:
    settings = Settings(PRGX_RUNTIME_PROFILE='staging')
    assert settings.profile.name == 'staging'
    assert settings.profile.evidence_signature_required is True
