"""Markdown formatting utilities."""

from .formatting import format_timestamp
from .models import ConversationMetadata


class MarkdownFormatter:
    """Formats conversation data as markdown."""

    def __init__(self, assistant_display_name: str = "Assistant"):
        """
        Initialize formatter with provider-specific settings.

        Args:
            assistant_display_name: Display name for assistant (e.g., "Claude", "DeepSeek")
        """
        self.assistant_display_name = assistant_display_name
        self._sender_map = self._build_sender_map()

    def _build_sender_map(self) -> dict[str, str]:
        """Build sender name mapping."""
        return {
            "human": "👤 Human",
            "assistant": f"🤖 {self.assistant_display_name}",
            "system": "⚙️ System",
            "user": "👤 User",
            "unknown": "❓ Unknown",
        }

    def format_sender_name(self, sender: str) -> str:
        """
        Format sender name for display.

        Args:
            sender: Raw sender identifier

        Returns:
            Formatted sender name with emoji
        """
        return self._sender_map.get(sender.lower(), f"💬 {sender.title()}")

    def create_markdown_header(
        self, metadata: ConversationMetadata, latest_message_time: str | None
    ) -> str:
        """
        Create the markdown header with conversation metadata.

        Args:
            metadata: Conversation metadata
            latest_message_time: ISO timestamp of latest message

        Returns:
            Markdown formatted header string
        """
        header_parts = []

        header_parts.append(f"# {metadata.name}\n")

        header_parts.append("## 📋 Conversation Details\n")
        header_parts.append(f"- **Conversation ID:** `{metadata.conversation_id}`")
        header_parts.append(f"- **Total Messages:** {metadata.message_count}")

        if metadata.created_at:
            formatted_created = format_timestamp(metadata.created_at)
            header_parts.append(f"- **Started:** {formatted_created}")

        if latest_message_time:
            formatted_latest = format_timestamp(latest_message_time)
            header_parts.append(f"- **Last Message:** {formatted_latest}")
        elif metadata.updated_at:
            formatted_updated = format_timestamp(metadata.updated_at)
            header_parts.append(f"- **Last Updated:** {formatted_updated}")

        header_parts.append("\n---\n")
        header_parts.append("## 💬 Conversation\n")

        return "\n".join(header_parts)

    def format_message(self, message: dict, index: int) -> str:
        """
        Format a single message as markdown.

        Args:
            message: Message dictionary with sender, text, created_at
            index: Message index (unused, for potential future use)

        Returns:
            Markdown formatted message string
        """
        sender = self.format_sender_name(message.get("sender", "unknown"))
        text = message.get("text", "[No content]")
        timestamp = message.get("created_at")

        formatted_text = text.strip()

        message_parts = []

        message_parts.append(f"### {sender}")

        if timestamp:
            formatted_time = format_timestamp(timestamp)
            message_parts.append(f"*{formatted_time}*")

        message_parts.append("")

        message_parts.append(formatted_text)
        message_parts.append("")

        return "\n".join(message_parts)
