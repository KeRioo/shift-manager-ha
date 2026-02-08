"""Server-Sent Events (SSE) broadcast hub.

Allows any number of connected clients to receive real-time updates
when shifts are created, modified, or deleted.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import AsyncGenerator

from fastapi import APIRouter
from starlette.responses import StreamingResponse

router = APIRouter(tags=["events"])

# ── Subscriber registry ─────────────────────────────────────────

_subscribers: list[asyncio.Queue] = []


def broadcast(event_type: str = "refresh", data: dict | None = None):
    """Push an event to every connected SSE client."""
    payload = json.dumps({
        "type": event_type,
        "ts": time.time(),
        **(data or {}),
    })
    dead: list[asyncio.Queue] = []
    for q in _subscribers:
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            dead.append(q)
    for q in dead:
        _subscribers.remove(q)


async def _event_stream(queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Yield SSE-formatted messages from a per-client queue."""
    try:
        # Initial keepalive so the browser sees the connection is open
        yield ": connected\n\n"
        while True:
            payload = await asyncio.wait_for(queue.get(), timeout=25)
            yield f"data: {payload}\n\n"
    except asyncio.TimeoutError:
        # Send a keepalive comment every ~25 s to prevent proxy timeouts
        yield ": keepalive\n\n"
    except asyncio.CancelledError:
        return
    finally:
        if queue in _subscribers:
            _subscribers.remove(queue)


async def _sse_generator(queue: asyncio.Queue) -> AsyncGenerator[str, None]:
    """Wraps _event_stream with infinite reconnect-safe loop."""
    try:
        yield ": connected\n\n"
        while True:
            try:
                payload = await asyncio.wait_for(queue.get(), timeout=25)
                yield f"data: {payload}\n\n"
            except asyncio.TimeoutError:
                yield ": keepalive\n\n"
    except asyncio.CancelledError:
        pass
    finally:
        if queue in _subscribers:
            _subscribers.remove(queue)


# ── SSE endpoint ────────────────────────────────────────────────

@router.get("/api/events")
async def sse_events():
    """SSE stream – clients listen here for live updates."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=64)
    _subscribers.append(queue)
    return StreamingResponse(
        _sse_generator(queue),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
