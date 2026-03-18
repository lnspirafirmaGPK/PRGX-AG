from prgx_ag.schemas import ProcessingOutcome
from prgx_ag.services.github_bridge import format_pr_body, format_pr_title
from prgx_ag.services.healing_intent_builder import build_fix_plan
from prgx_ag.services.narrative_builder import build_commit_style_narrative, build_repair_narrative


def test_healing_intent_generation_for_missing_init() -> None:
    findings = {'structural_issues': ['Missing __init__.py in src/prgx_ag/new_pkg']}
    plan = build_fix_plan(findings)
    assert plan == [
        {
            'path': 'src/prgx_ag/new_pkg/__init__.py',
            'content': '',
            'fix_class': 'structural.package_marker',
            'rationale': 'Restore the missing Python package marker required by the expected source tree.',
            'verification_commands': ['compileall', 'pytest', 'ruff', 'mypy'],
            'rollback_hint': 'Delete src/prgx_ag/new_pkg/__init__.py only if the directory should stop behaving as a Python package.',
            'source_issue': 'Missing __init__.py in src/prgx_ag/new_pkg',
        }
    ]


def test_commit_narrative_generation() -> None:
    outcome = ProcessingOutcome(
        agent_name='PRGX2',
        envelope_id='abc123',
        success=True,
        execution_time=0.2,
        message='Safe fixes applied',
        details={
            'fix_classes': ['structural.package_marker'],
            'verification_status': 'passed',
        },
    )
    narrative = build_commit_style_narrative(outcome)
    assert 'fix:' in narrative
    assert 'abc123' in narrative
    assert 'fix_classes=structural.package_marker' in narrative
    assert 'verification=passed' in narrative


def test_pr_body_generation_contains_governance_sections() -> None:
    title = format_pr_title(
        findings_summary={'summary': 'Missing package markers', 'target': 'repository', 'issue_count': 1},
        audit_result='approved',
        verification_result='passed',
        fix_classes=['structural.package_marker'],
    )
    body = format_pr_body(
        findings_summary={'summary': 'Missing package markers', 'target': 'repository', 'issue_count': 1},
        audit_result='approved',
        changed_files=['src/prgx_ag/new_pkg/__init__.py'],
        verification_result='passed',
        rollback_instructions=['Delete src/prgx_ag/new_pkg/__init__.py if the package marker is not needed.'],
        fix_classes=['structural.package_marker'],
        verification_commands=['compileall', 'pytest'],
    )
    assert 'approved' in title
    assert '### Findings summary' in body
    assert '### Audit result' in body
    assert '### Changed files' in body
    assert '### Verification result' in body
    assert '### Rollback instructions' in body


def test_pr_generation_includes_audit_metadata_and_changed_file_summaries() -> None:
    findings = {
        'summary': 'Repository drift corrected',
        'target': 'src/prgx_ag',
        'issue_count': 3,
    }
    title = format_pr_title(
        findings_summary=findings,
        audit_result='review_required',
        verification_result='passed',
        fix_classes=['structural.package_marker', 'structural.expected_path'],
    )
    body = format_pr_body(
        findings_summary=findings,
        audit_result='review_required',
        changed_files=['src/prgx_ag/api/__init__.py', 'src/prgx_ag/core/__init__.py'],
        verification_result='passed',
        rollback_instructions=['git checkout -- src/prgx_ag/api/__init__.py'],
        fix_classes=['structural.package_marker', 'structural.expected_path'],
        verification_commands=['python -m compileall src', 'pytest -q tests/test_pipeline_integration.py'],
    )

    assert title == 'chore(prgx): heal src/prgx_ag [review_required; passed; structural.package_marker, structural.expected_path]'
    assert '- Summary: Repository drift corrected' in body
    assert '- Issue count: 3' in body
    assert '- Status: review_required' in body
    assert '- src/prgx_ag/api/__init__.py' in body
    assert '- src/prgx_ag/core/__init__.py' in body
    assert 'python -m compileall src, pytest -q tests/test_pipeline_integration.py' in body


def test_repair_narrative_includes_payload_audit_and_changed_summary() -> None:
    outcome = ProcessingOutcome(
        agent_name='PRGX2',
        envelope_id='env-22',
        success=True,
        execution_time=0.321,
        message='Safe fixes applied',
        details={
            'target': 'repo',
            'fix_count': 6,
            'fix_classes': ['structural.package_marker'],
            'changed': [
                'src/a.py',
                'src/b.py',
                'src/c.py',
                'src/d.py',
                'src/e.py',
                'src/f.py',
            ],
            'verification_status': 'passed',
            'payload_audit': {'outcome': 'allow'},
            'rollback_hints': ['git checkout -- src/a.py'],
        },
    )

    narrative = build_repair_narrative(outcome)

    assert narrative.title == 'Repair applied successfully'
    assert 'Target=repo' in narrative.detected
    assert 'PlannedFixes=6' in narrative.detected
    assert 'Changed=src/a.py, src/b.py, src/c.py, src/d.py, src/e.py, +1 more' in narrative.repaired
    assert 'Verification=passed' in narrative.repaired
    assert 'PayloadAudit=present' in narrative.learned
    assert 'RollbackHints=1' in narrative.learned
