"""In-process pub/sub hub for pushing live alerts to WebSocket clients.

Lightweight and dependency-free: each subscriber gets an asyncio.Queue. When the
backend records an alert it calls `publish()`, and every connected dashboard
receives it in real time. For a multi-process deployment you'd swap this for
Redis pub/sub or Firestore listeners, but for a single API process this is ideal.
"""
from __future__ import annotations

import asyncio
from typing import Optional


class EventHub:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue] = set()

    async def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=100)
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    async def publish(self, message: dict) -> None:
        for q in list(self._subscribers):
            try:
                q.put_nowait(message)
            except asyncio.QueueFull:
                # Drop for a slow consumer rather than blocking everyone.
                pass

    @property
    def subscriber_count(self) -> int:
        return len(self._subscribers)


_hub: Optional[EventHub] = None


def get_event_hub() -> EventHub:
    global _hub
    if _hub is None:
        _hub = EventHub()
    return _hub
