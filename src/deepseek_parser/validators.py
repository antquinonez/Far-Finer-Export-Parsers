"""Validators for detecting DeepSeek export file formats."""

from typing import Any


def is_deepseek_export(data: list[dict[str, Any]] | dict[str, Any]) -> bool:
    """
    Check if export data is in DeepSeek format.

    DeepSeek exports have:
    - mapping object with tree structure
    - fragments array with REQUEST/RESPONSE types

    Args:
        data: Parsed JSON data from export file

    Returns:
        True if data appears to be DeepSeek export format
    """
    conversations = data if isinstance(data, list) else data.get("conversations", [])
    if not conversations:
        return False

    first_conv = conversations[0]

    if "mapping" not in first_conv:
        return False

    mapping = first_conv.get("mapping", {})

    for node_id, node in mapping.items():
        if isinstance(node, dict) and node.get("message"):
            fragments = node["message"].get("fragments", [])
            if fragments and isinstance(fragments, list):
                if "type" in fragments[0] and "content" in fragments[0]:
                    return True

    return False
