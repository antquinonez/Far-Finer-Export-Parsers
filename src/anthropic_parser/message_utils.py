"""
Message ordering utilities.
"""

from datetime import datetime
from typing import Any


def sort_messages_by_timestamp(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Sort messages by created_at timestamp in ascending order.

    Messages without timestamps are placed at the end, preserving their relative order.

    Args:
        messages: List of message dictionaries

    Returns:
        New list with messages sorted by timestamp
    """

    def parse_timestamp(msg: dict[str, Any]) -> tuple[int, float]:
        ts = msg.get("created_at") or msg.get("timestamp")
        if not ts:
            return (1, 0.0)
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return (0, dt.timestamp())
        except (ValueError, AttributeError):
            return (1, 0.0)

    return sorted(messages, key=parse_timestamp)
