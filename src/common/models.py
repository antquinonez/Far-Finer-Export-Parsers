"""Shared data models for chat export parsers."""

from dataclasses import dataclass


@dataclass
class ConversationMetadata:
    """Metadata for a parsed conversation."""

    conversation_id: str
    name: str
    sanitized_filename: str
    message_count: int
    created_at: str | None = None
    updated_at: str | None = None
    latest_message_at: str | None = None


@dataclass
class MessageData:
    """Streamlined message data structure."""

    sender: str
    text: str
    created_at: str | None = None
