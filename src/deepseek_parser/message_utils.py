"""Message extraction utilities for DeepSeek exports."""

from datetime import datetime
from typing import Any


def extract_messages_from_mapping(mapping: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract messages from DeepSeek's tree-based mapping structure.

    Traverses the tree from root through children to create a linear
    message list.

    Args:
        mapping: DeepSeek mapping object with node IDs as keys

    Returns:
        List of message dictionaries with sender, text, created_at, files
    """
    messages = []

    root = mapping.get("root")
    if not root:
        return messages

    current_id = root.get("children", [None])[0] if root.get("children") else None

    while current_id and current_id in mapping:
        node = mapping[current_id]
        msg = node.get("message")

        if msg:
            for fragment in msg.get("fragments", []):
                fragment_type = fragment.get("type", "")
                sender = "human" if fragment_type == "REQUEST" else "assistant"

                messages.append(
                    {
                        "sender": sender,
                        "text": fragment.get("content", ""),
                        "created_at": msg.get("inserted_at"),
                        "files": msg.get("files", []),
                    }
                )

        children = node.get("children", [])
        current_id = children[0] if children else None

    return messages


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
