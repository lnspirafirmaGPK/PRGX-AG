from __future__ import annotations

import asyncio
import logging
from pathlib import Path

from prgx_ag.agents import PRGX1Sentry, PRGX2Mechanic, PRGX3Diplomat
from prgx_ag.config import RuntimePaths, Settings, parse_path_list
from prgx_ag.core import AetherBus
from prgx_ag.core.events import EXECUTE_FIX, RSI_FEEDBACK
from prgx_ag.policy import PatimokkhaChecker
from prgx_ag.rsi import LearningState, RSIEngine
from prgx_ag.rsi.gems import append_gem_log


class PRGXAGNexus:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.repo_root = Path(settings.repo_root).resolve()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.bus = AetherBus(history_size=settings.event_history_size)
        self.checker = PatimokkhaChecker()
        self.state_path = self.repo_root / ".prgx-ag/state/learning_state.json"
        self.gem_log_path = self.repo_root / ".prgx-ag/state/gem_log.json"

        defaults = RuntimePaths()
        allowed = parse_path_list(settings.allowed_write_paths, defaults.allowed)
        protected = parse_path_list(settings.protected_paths, defaults.protected)

        self.prgx1 = PRGX1Sentry(self.bus, root=self.repo_root)
        self.prgx2 = PRGX2Mechanic(
            self.bus,
            root=self.repo_root,
            checker=self.checker,
            allowed_paths=allowed,
            protected_paths=protected,
            dry_run=settings.dry_run,
        )
        self.prgx3 = PRGX3Diplomat(
            bus=self.bus,
            checker=self.checker,
            agent_id="PRGX3",
            role="Diplomat",
        )
        self.rsi_engine = RSIEngine()
        self.learning_state = LearningState.load(self.state_path)
        self._running = False

    async def wire_event_subscriptions(self) -> None:
        await self.prgx3.start()
        await self.bus.subscribe(EXECUTE_FIX, self._handle_execute_fix)

    async def wire_subscriptions(self) -> None:
        # backward compatibility
        await self.wire_event_subscriptions()

    async def _handle_execute_fix(self, payload: dict[str, object]) -> None:
        findings = payload.get("findings", {})
        target = (
            str(findings.get("target", self.repo_root))
            if isinstance(findings, dict)
            else str(self.repo_root)
        )

        outcome = await self.prgx2.apply_shadow_fix(target, payload)
        await self.prgx3.report_result(outcome)

        gem = self.rsi_engine.analyze(outcome)
        if gem and self.learning_state.apply_gem(gem):
            self.learning_state.save(self.state_path)
            append_gem_log(self.gem_log_path, gem)
            await self.bus.publish(RSI_FEEDBACK, {"gem": gem.model_dump()})

    async def run_self_healing_cycle(self) -> dict[str, object]:
        return await self.prgx1.publish_issue_report()

    async def run_scan_only(self) -> dict[str, object]:
        return self.prgx1.scan_entropy()

    async def run_once(self) -> None:
        await self.wire_event_subscriptions()
        await self.run_self_healing_cycle()

    async def run_continuous(self, interval_seconds: int = 10) -> None:
        await self.wire_event_subscriptions()
        self._running = True

        while self._running:
            await self.run_self_healing_cycle()
            await asyncio.sleep(interval_seconds)

    async def shutdown(self) -> None:
        self._running = False


PRGX_AG_Nexus = PRGXAGNexus
