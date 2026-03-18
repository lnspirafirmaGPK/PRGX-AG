# Bug Fix Proposal

## Scope
Major structural fix: migrate repository from static-only docs layout into complete Python backend architecture for PRGX-AG Nexus while preserving governance documentation intent.

## Findings
1. Backend architecture existed only as narrative, not executable modules.
2. No strict schemas, no event bus runtime, no orchestrator, and no policy tests.
3. Missing CLI, RSI loop, and triad-agent integration.

## Proposed fixes
1. Add `src/prgx_ag` modular backend with strict Pydantic models and async AetherBus.
2. Implement PRGX1/PRGX2/PRGX3 agents with Patimokkha-enforced healing flow.
3. Add orchestrator + RSI engine + bounded learning state.
4. Add pytest coverage for policy, bus, agents, RSI, and full cycle.

## Expected impact
- Architecture is now executable and testable.
- Harmful intents are programmatically blocked before write operations.
- Repository now supports production-style governance flow and self-healing cycle.

## Rollback
Revert this change set if consumers require previous static-only documentation repository state.

## 2026-03-17 Major structural fix
- Implemented full hybrid PRGX-AG architecture (.prgx-ag governance + GitHub workflows + Python runtime triad).
- Added strict schemas, event-driven nexus wiring, safe fix executor guardrails, RSI bounded learning, and manifest/policy loaders.
- Added deterministic pytest coverage for policy, bus, triad behavior, manifest loading, translation matrix, and full cycle flow.

## 2026-03-17 Bug fix and documentation alignment
- Fixed pytest execution bug by adding `pythonpath = ["src"]` in `pyproject.toml`, so test imports work without manual environment overrides.
- Updated README system architecture into database/state-aligned ER diagram based on `.prgx-ag` data sources.
- Removed completed-recommendation noise and replaced with forward-only EN/TH backlog proposals.

## 2026-03-17 Triad hardening and architecture completion pass
- Added explicit PRGX1 read-only scan methods for dependency, structure, and integrity drift observation.
- Added integrity scanner + healing intent builder + finding/narrative schemas to complete Porisjem role boundaries.
- Extended orchestrator with `PRGXAGNexus` naming, shutdown support, and compatibility alias.
- Updated README with full Porisjem/AETHERIUM framing, refreshed architecture diagram context, and new EN/TH future backlog items.

## 2026-03-17 README architecture/data-store alignment refresh
- Refined README system architecture to mirror the actual `.prgx-ag` data layout, including policy, manifest, workflow, state, and audit relationships.
- Removed completed-recommendation overlap from bilingual backlog sections and replaced it with new forward-looking EN/TH enhancement proposals.

## 2026-03-18 Source recovery fix
- Repaired `src/prgx_ag/agents/prgx1_sentry.py` after a diff artifact and concatenated multi-file patch content were accidentally committed into the module body.
- Restored the file to valid Python source so import, compile, and packaging pipelines can load the PRGX1 agent again.

## 2026-03-18 Workflow governance gate alignment
- Promoted `.github/workflows/prgx-test.yml` as the canonical repository-health gate with a consistent early `python -m compileall src` sanity check.
- Standardized Python setup/install patterns across the PRGX scan, nightly, and healing workflows to reduce dependency drift and simplify triage.
- Removed the generic GitHub Pages deployment workflow because it deployed the entire repository root instead of a dedicated static-site artifact, which was not appropriate for this repository health model.

## 2026-03-18 Governed healing pipeline expansion
- Extended healing fix-plan entries with machine-readable metadata for fix class, rationale, verification commands, rollback hints, and source issue provenance.
- Upgraded executor and narrative layers so applied fix classes, verification state, and rollback guidance remain visible to reviewers and automation.
- Reworked the PR healing workflow to keep `.github/workflows/prgx-heal-pr.yml` as the entry point while adding post-fix verification, blocked/revert behavior, and dynamic PR branch metadata generation.
- Refreshed README architecture documentation to mirror the concrete `.prgx-ag` data stores/workflows and removed completed-recommendation sections from both English and Thai text.

## 2026-03-18 Structured Patimokkha rule evaluation refactor
- Replaced flat blocked-token matching with explicit policy rule objects carrying scope, severity, allow-context hints, and recommended actions.
- Extended audit outputs with structured match evidence so reviewers can see which field matched, which rule fired, and whether the outcome was allow, contextual review, or reject.
- Added regression tests for defensive narratives, safe exported commands, and malicious payloads hidden inside metadata.

## 2026-03-18 Governed repair pipeline regression hardening
- Added deeper Nexus/Mechanic/Patimokkha integration coverage, including realistic governed repair payloads, protected-path enforcement, invalid fix plans, duplicate fixes, traversal attempts, and empty plan rejections.
- Added PR/report narrative regressions for `github_bridge.py` and `narrative_builder.py` so audit metadata, rollback guidance, and changed-file summaries remain stable.
- Strengthened `.github/workflows/prgx-test.yml` and README release guidance so governed integration tests run as a required quality gate before broader matrix testing.

## 2026-03-18 Repair engine bounded-safety expansion
- Introduced explicit governed fix classes (`create_empty_init`, `manifest_sync`, `dependency_bump`) with validator metadata instead of relying on generic empty-file writes.
- Added dependency allowlist policy data so automatic manifest edits are limited to preapproved package/range pairs and minor-only bump rules.
- Captured per-fix snapshots, rollback metadata, and post-fix verification results so PR narratives can explain safety, validation, and deterministic reversion paths.

## 2026-03-18 Repository metadata and test-noise cleanup
- Removed the unused `pytest-asyncio` configuration path from `pyproject.toml` so the test suite no longer emits an unknown-config warning in environments that do not install that plugin.
- Rewrote `README.md` to keep the architecture summary aligned with the actual `.prgx-ag` governance assets and to explicitly exclude completed-suggestion lists from both English and Thai summaries.
- Replaced leftover demo metadata in `index.html` and `package.json` with repository-accurate PRGX-AG descriptions.
