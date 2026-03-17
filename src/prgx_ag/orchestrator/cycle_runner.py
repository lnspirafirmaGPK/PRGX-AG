from __future__ import annotations

import asyncio


async def sleep_cycle(interval_seconds: int) -> None:
    await asyncio.sleep(interval_seconds)
