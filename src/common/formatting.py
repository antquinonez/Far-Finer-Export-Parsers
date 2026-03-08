"""Shared formatting utilities."""

import re
from datetime import datetime


def sanitize_filename(name: str, max_length: int = 100) -> str:
    """
    Convert conversation name to safe filename.

    Args:
        name: Original conversation name
        max_length: Maximum length for generated filename

    Returns:
        Sanitized filename without extension
    """
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
    sanitized = re.sub(r"\s+", "_", sanitized.strip())
    sanitized = re.sub(r"_+", "_", sanitized)
    sanitized = sanitized.strip("_.")

    if not sanitized:
        sanitized = "untitled_conversation"

    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip("_")

    return sanitized


def format_timestamp(timestamp: str | None) -> str:
    """
    Format ISO timestamp to readable format.

    Args:
        timestamp: ISO format timestamp or None

    Returns:
        Human-readable timestamp string
    """
    if not timestamp:
        return "N/A"

    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        return dt.strftime("%B %d, %Y at %I:%M %p")
    except (ValueError, AttributeError):
        return timestamp
