import pytest

from prgx_ag.core.aetherbus import AetherBus


@pytest.mark.asyncio
async def test_aetherbus_multi_subscriber_dispatch() -> None:
    bus = AetherBus()
    events: list[str] = []

    async def h1(payload: str) -> None:
        events.append(f'h1:{payload}')

    async def h2(payload: str) -> None:
        events.append(f'h2:{payload}')

    await bus.subscribe('topic', h1)
    await bus.subscribe('topic', h2)
    await bus.publish('topic', 'ok')
    assert 'h1:ok' in events
    assert 'h2:ok' in events
