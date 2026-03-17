# AGENTS Status and Roles

## Current repository status
- Repository type: lightweight static/documentation project.
- Current focus: architecture specification, governance flow, and documentation correctness.
- Last maintenance update: bug-fix and documentation alignment pass.

## Roles
- **Maintainer Agent**: keeps docs and architecture contracts consistent with implementation intent.
- **Validation Agent**: runs repository checks (format/links/basic consistency) before release.
- **Governance Agent**: reviews policy, telemetry, and alignment model changes for compliance impact.

## Operational rules
- Do not commit `node_modules/`.
- Keep README architecture synced with endpoint/entity changes.
- Log major structural fixes in `BUGFIX_PROPOSAL.md`.
