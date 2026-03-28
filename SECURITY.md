# Security Policy

## Supported Versions

PRGX-AG is currently maintained as a rolling mainline project.

| Version | Supported |
| --- | --- |
| `main` / latest commit | ✅ |
| historical tags/commits | ❌ |

## Reporting a Vulnerability

Please report security issues privately before public disclosure.

1. Open a **private security advisory** in GitHub (preferred), or contact maintainers through repository security contact channels.
2. Include:
   - affected file/module and branch or commit hash,
   - reproduction steps or proof-of-concept,
   - expected vs actual behavior,
   - potential impact (confidentiality/integrity/availability).
3. Do **not** publish exploit details until a fix is available.

## Response Targets

- Initial triage acknowledgment: within **3 business days**.
- Risk assessment and mitigation plan: within **7 business days** for validated reports.
- Coordinated disclosure timeline: agreed case-by-case based on severity and fix complexity.

## Scope Guidance

Security-relevant areas include:
- Policy enforcement and repair authorization in `src/prgx_ag/policy` and `src/prgx_ag/services`.
- Workflow automation under `.github/workflows/`.
- Governance state integrity under `.prgx-ag/` (policy, manifests, audit, and learning state).

## Safe Harbor

Good-faith research is welcome. Avoid:
- destructive testing against maintainers' infrastructure,
- data exfiltration,
- denial-of-service behavior,
- social engineering.

If you follow this policy and act in good faith, we will treat your report as authorized security research.
