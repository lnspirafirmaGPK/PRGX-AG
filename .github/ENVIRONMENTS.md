# GitHub Environment Setup

This repository uses GitHub Actions environment gates for workflow-driven deployment and promotion flows. GitHub Environments are configured in repository settings, but the expected names and branch mappings are versioned here so workflow behavior stays reproducible.

## Required environment names
- `development`
- `staging`
- `production`

## Workflow mapping
- `.github/workflows/main.yml`
  - `main` / `master` -> `production`
  - `develop` -> `staging`
  - `feature/**` and other branches -> `development`
  - `workflow_dispatch` can override the target with the `target_environment` input
- `.github/workflows/prgx-nightly.yml` -> `staging`
- `.github/workflows/prgx-heal-pr.yml` -> `staging`

## Recommended protection rules
1. Add required reviewers for `production`.
2. Scope secrets and vars per environment when deployment hooks are introduced.
3. Use wait timers only for `production` if you need a promotion hold.

## Suggested environment variables or secrets
- `PRGX_RUNTIME_PROFILE`
- `PRGX_AUDIT_WINDOW_HOURS` (integer hours, default: `24`)
- `PRGX_MEDICAL_FINDINGS_PATH` (filesystem path, default: `.prgx-ag/evidence/medical_research_findings.json`)
- `PRGX_DEPLOY_TARGET`
- Any future cloud credentials needed by downstream deployment jobs

## Typed runtime profile contract
- `development`
  - Higher auto-repair allowance (`max_auto_fix_items=20`, `max_issue_count_for_auto_fix=60`)
  - Compact audit verbosity
- `staging`
  - Medium auto-repair allowance (`max_auto_fix_items=12`, `max_issue_count_for_auto_fix=30`)
  - Standard audit verbosity
- `production`
  - Strict auto-repair allowance (`max_auto_fix_items=5`, `max_issue_count_for_auto_fix=12`)
  - Forensic audit verbosity with signed governance evidence expectation

## Notes
- GitHub Environments cannot be fully created from tracked repository files alone; they must also exist in the repository settings UI or via the GitHub API.
- These names are intentionally simple so future deployment workflows can share the same approval and secret boundaries.
