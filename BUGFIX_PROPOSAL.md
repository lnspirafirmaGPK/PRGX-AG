# Bug Fix Proposal

## Scope
Stabilize repository structure and remove high-risk inconsistencies between stated architecture and usable project artifacts.

## Findings
1. README mixed narrative text with inconsistent structure, making architecture/data model hard to validate.
2. No explicit repository rule to prevent accidental `node_modules/` commits.
3. Missing maintenance role/status handoff note for future agent-driven updates.

## Proposed fixes
1. Rewrite README into a schema-oriented architecture reference with a clear system diagram.
2. Add `.gitignore` to block dependency artifacts and reduce accidental bloat.
3. Add `AGENTS.md` to record project roles, status, and operational update rules.

## Expected impact
- Higher documentation reliability.
- Lower risk of repository pollution and broken static deployment artifacts.
- Faster onboarding for future maintenance agents.

## Rollback
- Revert README, AGENTS.md, BUGFIX_PROPOSAL.md, and `.gitignore` in one commit if downstream teams need the previous narrative format.
