"""Small structured trace store for the Observation pillar."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any

logger = logging.getLogger("agent_tax.trace")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class TraceLog:
    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def add(self, event: str, **data: Any) -> dict[str, Any]:
        item = {"at": now_iso(), "event": event, **data}
        self.events.append(item)
        logger.info(json.dumps(item, default=str))
        return item

    def as_list(self) -> list[dict[str, Any]]:
        return self.events
