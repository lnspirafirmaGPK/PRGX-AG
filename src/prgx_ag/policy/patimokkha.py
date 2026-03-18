from __future__ import annotations

from typing import Any, Iterable

from prgx_ag.policy.ruleset import (
    BLOCKED_PATTERNS,
    PRINCIPLES,
    SAFE_AETHEBUD_TERMS,
    SAFE_CONTEXT_HINTS,
    SAFE_EXPORTED_COMMANDS,
)
from prgx_ag.schemas import AuditResult, EthicalStatus, Intent


class PatimokkhaChecker:
    """Context-aware intent auditor for governed execution."""

    def _flatten(self, value: Any) -> Iterable[str]:
        if value is None:
            return []

        if isinstance(value, dict):
            parts: list[str] = []
            for key, item in value.items():
                parts.append(str(key))
                parts.extend(self._flatten(item))
            return parts

        if isinstance(value, (list, tuple, set)):
            parts: list[str] = []
            for item in value:
                parts.extend(self._flatten(item))
            return parts

        return [str(value)]

    def _normalize_text(self, value: Any) -> str:
        return " ".join(str(value).split()).strip().lower()

    def _metadata(self, intent: Intent) -> dict[str, Any]:
        return intent.metadata if isinstance(intent.metadata, dict) else {}

    def _intent_text(self, intent: Intent) -> str:
        metadata = self._metadata(intent)
        parts = [
            getattr(intent, "id", ""),
            getattr(intent, "source_agent", ""),
            getattr(intent, "target_firma", ""),
            getattr(intent, "description", ""),
            *self._flatten(metadata),
        ]
        return self._normalize_text(" ".join(filter(None, map(str, parts))))

    def _safe_command_context(self, metadata: dict[str, Any]) -> bool:
        internal_term = self._normalize_text(metadata.get("internal_term", ""))
        exported_command = self._normalize_text(metadata.get("exported_command", ""))

        return (
            internal_term in SAFE_AETHEBUD_TERMS
            or exported_command in SAFE_EXPORTED_COMMANDS
        )

    def _has_safe_context_near_match(
        self,
        text: str,
        token: str,
        window: int = 96,
    ) -> bool:
        start = 0
        while True:
            index = text.find(token, start)
            if index == -1:
                return False

            left = max(0, index - window)
            right = min(len(text), index + len(token) + window)
            local_text = text[left:right]

            if any(hint in local_text for hint in SAFE_CONTEXT_HINTS):
                return True

            start = index + len(token)

    def _classify_matches(
        self,
        text: str,
    ) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
        hard_blocks: list[tuple[str, str]] = []
        contextual_mentions: list[tuple[str, str]] = []

        for token, reason in BLOCKED_PATTERNS.items():
            if token not in text:
                continue

            if self._has_safe_context_near_match(text, token):
                contextual_mentions.append((token, reason))
            else:
                hard_blocks.append((token, reason))

        return hard_blocks, contextual_mentions

    def _derive_operational_status(
        self,
        metadata: dict[str, Any],
    ) -> EthicalStatus:
        raw_status = self._normalize_text(metadata.get("ethical_status", ""))

        if raw_status == self._normalize_text(EthicalStatus.PARAJIKA.value):
            return EthicalStatus.PARAJIKA

        if raw_status == self._normalize_text(EthicalStatus.MAJOR_VIOLATION.value):
            return EthicalStatus.MAJOR_VIOLATION

        if raw_status == self._normalize_text(EthicalStatus.MINOR_INFRACTION.value):
            return EthicalStatus.MINOR_INFRACTION

        return EthicalStatus.CLEAN

    def validate_intent(self, intent: Intent) -> AuditResult:
        metadata = self._metadata(intent)
        text = self._intent_text(intent)

        hard_blocks, contextual_mentions = self._classify_matches(text)

        if hard_blocks:
            token, reason = hard_blocks[0]
            return AuditResult(
                is_allowed=False,
                status=EthicalStatus.PARAJIKA,
                reason=f"{reason} Matched token: {token}",
                suggested_action="Escalate to audit and reject execution.",
            )

        if contextual_mentions:
            tokens = ", ".join(token for token, _ in contextual_mentions[:5])
            return AuditResult(
                is_allowed=True,
                status=EthicalStatus.MINOR_INFRACTION,
                reason=(
                    "Contextual risk terms were detected, but they appear in a "
                    f"defensive or audit-oriented context. Reviewed tokens: {tokens}"
                ),
                suggested_action="Proceed with monitored execution and retain audit trail.",
            )

        operational_status = self._derive_operational_status(metadata)
        if operational_status in {
            EthicalStatus.MAJOR_VIOLATION,
            EthicalStatus.PARAJIKA,
        } and self._safe_command_context(metadata):
            return AuditResult(
                is_allowed=True,
                status=operational_status,
                reason=(
                    "High-severity operational state acknowledged, but intent remains "
                    "bounded by recognized safety commands and governance context."
                ),
                suggested_action="Proceed with strict monitoring and retain full audit evidence.",
            )

        principles = ", ".join(PRINCIPLES)
        return AuditResult(
            is_allowed=True,
            status=EthicalStatus.CLEAN,
            reason=f"Intent complies with Patimokkha principles: {principles}.",
            suggested_action="Proceed with monitored execution.",
        )
