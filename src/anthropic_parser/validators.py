"""Validators for detecting export file formats."""

from typing import Any


def is_anthropic_export(data: list[dict[str, Any]] | dict[str, Any]) -> bool:
    """
    Check if export data is in Anthropic format.

    Anthropic exports have:
    - chat_messages array with sender field
    - NOT mapping/fragments (DeepSeek indicator)

    Args:
        data: Parsed JSON data from export file

    Returns:
        True if data appears to be Anthropic export format
    """
    conversations = data if isinstance(data, list) else data.get("conversations", [])
    if not conversations:
        return False

    first_conv = conversations[0]

    if "mapping" in first_conv:
        return False

    messages = first_conv.get("chat_messages", [])
    if messages and isinstance(messages, list):
        first_msg = messages[0]
        if "sender" in first_msg:
            return True

    return False
