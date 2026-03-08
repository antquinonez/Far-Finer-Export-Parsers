"""
Anthropic Chat Export Parser - Streamlined Message Format

Parses large Anthropic chat export JSON files and extracts conversations
with only essential message data: sender, text, and timestamp.
"""

import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from anthropic_parser.config import Config
from anthropic_parser.file_manager import move_to_done
from anthropic_parser.message_utils import sort_messages_by_timestamp


@dataclass
class ConversationMetadata:
    """Metadata for a parsed conversation."""

    conversation_id: str
    name: str
    sanitized_filename: str
    message_count: int
    created_at: str | None = None
    updated_at: str | None = None


@dataclass
class MessageData:
    """Streamlined message data structure."""

    sender: str
    text: str
    created_at: str | None = None


class MessageExtractor:
    """
    Extracts and normalizes message data from various Anthropic export formats.

    Handles different possible message structures and extracts only
    the essential information needed for AI processing.
    """

    def __init__(self):
        """Initialize the message extractor."""
        pass

    def extract_message_text(self, message: dict[str, Any]) -> str:
        """
        Extract text content from a message, handling various formats.

        Args:
            message: Raw message data from export

        Returns:
            Extracted text content
        """
        # For Anthropic exports, text is directly in the 'text' field
        if "text" in message and isinstance(message["text"], str):
            return message["text"]

        # Try other possible text field names
        text_fields = ["content", "body", "message"]

        for field in text_fields:
            if field in message:
                content = message[field]

                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # Handle structured content (like Claude's format)
                    text_parts = []
                    for part in content:
                        if isinstance(part, dict):
                            if "text" in part:
                                text_parts.append(part["text"])
                            elif "content" in part:
                                text_parts.append(str(part["content"]))
                        elif isinstance(part, str):
                            text_parts.append(part)
                    return "\n".join(text_parts)
                elif isinstance(content, dict):
                    # Handle nested content structures
                    if "text" in content:
                        return content["text"]
                    elif "content" in content:
                        return str(content["content"])

        # Fallback: try to find any text-like content
        for key, value in message.items():
            if isinstance(value, str) and len(value) > 10:  # Assume substantial text
                return value

        return "[No text content found]"

    def extract_sender_info(self, message: dict[str, Any]) -> str:
        """
        Extract sender information from message.

        Args:
            message: Raw message data from export

        Returns:
            Sender identifier (human, assistant, system, etc.)
        """
        # For Anthropic exports, sender is directly in the 'sender' field
        if "sender" in message and isinstance(message["sender"], str):
            return message["sender"].lower()

        # Try other possible sender field names
        sender_fields = ["author", "role", "from", "user"]

        for field in sender_fields:
            if field in message:
                sender = message[field]

                if isinstance(sender, str):
                    return sender.lower()
                elif isinstance(sender, dict) and "name" in sender:
                    return sender["name"].lower()
                elif isinstance(sender, dict) and "role" in sender:
                    return sender["role"].lower()

        # Try to infer from message structure or content
        message_str = str(message).lower()
        if "assistant" in message_str:
            return "assistant"
        elif "human" in message_str or "user" in message_str:
            return "human"

        return "unknown"

    def extract_timestamp(self, message: dict[str, Any]) -> str | None:
        """
        Extract timestamp from message.

        Args:
            message: Raw message data from export

        Returns:
            ISO format timestamp or None
        """
        timestamp_fields = ["created_at", "timestamp", "time", "date"]

        for field in timestamp_fields:
            if field in message and message[field]:
                return message[field]

        return None

    def process_message(self, message: dict[str, Any]) -> MessageData:
        """
        Process a raw message into streamlined format.

        Args:
            message: Raw message data from export

        Returns:
            MessageData with essential information
        """
        return MessageData(
            sender=self.extract_sender_info(message),
            text=self.extract_message_text(message),
            created_at=self.extract_timestamp(message),
        )


class ConversationParser:
    """
    Parses Anthropic chat export data and extracts individual conversations
    with streamlined message format.
    """

    def __init__(self, max_filename_length: int = 100):
        """
        Initialize the parser.

        Args:
            max_filename_length: Maximum length for generated filenames
        """
        self.max_filename_length = max_filename_length
        self.message_extractor = MessageExtractor()

    def sanitize_filename(self, name: str) -> str:
        """
        Convert conversation name to safe filename.

        Args:
            name: Original conversation name

        Returns:
            Sanitized filename without extension
        """
        # Remove/replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', "_", name)
        sanitized = re.sub(r"\s+", "_", sanitized.strip())
        sanitized = re.sub(r"_+", "_", sanitized)
        sanitized = sanitized.strip("_.")

        # Handle empty names
        if not sanitized:
            sanitized = "untitled_conversation"

        # Truncate if too long
        if len(sanitized) > self.max_filename_length:
            sanitized = sanitized[: self.max_filename_length].rstrip("_")

        return sanitized

    def extract_conversations(self, export_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract conversations from export data structure.

        Args:
            export_data: Parsed JSON export data

        Returns:
            List of conversation dictionaries

        Raises:
            KeyError: If expected data structure is not found
            ValueError: If no conversations found in export
        """
        # Handle different possible export structures
        conversations = None

        if "conversations" in export_data:
            conversations = export_data["conversations"]
        elif "data" in export_data and "conversations" in export_data["data"]:
            conversations = export_data["data"]["conversations"]
        elif isinstance(export_data, list):
            conversations = export_data
        else:
            # Try to find conversation-like structures
            for key, value in export_data.items():
                if (
                    isinstance(value, list)
                    and value
                    and any(field in str(value[0]) for field in ["messages", "chat_messages"])
                ):
                    conversations = value
                    break

        if not conversations:
            raise ValueError("No conversations found in export data")

        return conversations

    def get_conversation_metadata(
        self, conversation: dict[str, Any], index: int
    ) -> ConversationMetadata:
        """
        Extract metadata from a conversation object.

        Args:
            conversation: Single conversation data
            index: Conversation index for fallback naming

        Returns:
            ConversationMetadata object
        """
        # Extract conversation ID - handle both direct and nested structures
        conv_id = (
            conversation.get("id")
            or conversation.get("uuid")
            or (conversation.get("conversation", {}).get("uuid"))
            or f"conversation_{index:04d}"
        )

        # Extract conversation name with fallbacks - handle nested structure
        name = (
            conversation.get("name")
            or conversation.get("title")
            or conversation.get("summary")
            or (conversation.get("conversation", {}).get("name"))
            or f"Conversation {index + 1}"
        )

        # Count messages - handle both 'messages' and 'chat_messages'
        messages = (
            conversation.get("messages", [])
            or conversation.get("chat_messages", [])
            or conversation.get("conversation", {}).get("chat_messages", [])
        )
        message_count = len(messages) if isinstance(messages, list) else 0

        # Extract timestamps - handle nested structure
        created_at = conversation.get("created_at") or conversation.get("conversation", {}).get(
            "created_at"
        )
        updated_at = conversation.get("updated_at") or conversation.get("conversation", {}).get(
            "updated_at"
        )

        return ConversationMetadata(
            conversation_id=conv_id,
            name=name,
            sanitized_filename=self.sanitize_filename(name),
            message_count=message_count,
            created_at=created_at,
            updated_at=updated_at,
        )

    def process_conversation_messages(self, conversation: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Process conversation messages into streamlined format.

        Args:
            conversation: Raw conversation data

        Returns:
            List of processed messages with only essential data
        """
        # Handle both direct and nested message structures
        messages = (
            conversation.get("messages", [])
            or conversation.get("chat_messages", [])
            or conversation.get("conversation", {}).get("chat_messages", [])
        )

        # Sort messages by timestamp before processing
        messages = sort_messages_by_timestamp(messages)

        processed_messages = []

        for message in messages:
            try:
                message_data = self.message_extractor.process_message(message)

                # Convert to dictionary for JSON serialization
                message_dict = {"sender": message_data.sender, "text": message_data.text}

                # Only include timestamp if available
                if message_data.created_at:
                    message_dict["created_at"] = message_data.created_at

                processed_messages.append(message_dict)

            except Exception as e:
                print(f"Warning: Failed to process message: {e}")
                # Include a placeholder for failed messages
                processed_messages.append(
                    {"sender": "unknown", "text": "[Message processing failed]", "error": str(e)}
                )

        return processed_messages

    def find_latest_message_timestamp(self, messages: list[dict[str, Any]]) -> str | None:
        """
        Find the latest created_at timestamp from a list of messages.

        Args:
            messages: List of message dictionaries

        Returns:
            Latest ISO format timestamp or None if no timestamps found
        """
        timestamps = []

        for message in messages:
            if "created_at" in message and message["created_at"]:
                timestamps.append(message["created_at"])

        if not timestamps:
            return None

        # Sort timestamps and return the latest one
        try:
            # Convert to datetime objects for proper sorting
            datetime_objects = []
            for ts in timestamps:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    datetime_objects.append((dt, ts))
                except (ValueError, AttributeError):
                    continue

            if datetime_objects:
                # Sort by datetime and return the original timestamp string
                datetime_objects.sort(key=lambda x: x[0])
                return datetime_objects[-1][1]  # Return the latest timestamp
            else:
                # Fallback to string sorting if datetime parsing fails
                return sorted(timestamps)[-1]

        except Exception:
            # If all else fails, just return the last timestamp
            return timestamps[-1] if timestamps else None


class ChatExportProcessor:
    """
    Main processor for handling Anthropic chat export files.

    Processes exports into streamlined conversation files containing
    only essential message data.
    """

    def __init__(self, export_file_path: str | Path, output_dir: Path | None = None):
        """
        Initialize processor with export file path.

        Args:
            export_file_path: Path to the Anthropic export JSON file
            output_dir: Optional output directory (uses input file's dir if not provided)
        """
        self.export_path = Path(export_file_path)

        if not self.export_path.exists():
            raise FileNotFoundError(f"Export file not found: {self.export_path}")

        self.base_dir = output_dir if output_dir else self.export_path.parent
        self.output_dir: Path | None = None
        self.parser = ConversationParser()

    def load_export_data(self) -> dict[str, Any]:
        """
        Load and parse the export JSON file.

        Returns:
            Parsed JSON data

        Raises:
            json.JSONDecodeError: If file is not valid JSON
            MemoryError: If file is too large for available memory
        """
        print(f"Loading export file: {self.export_path}")
        print(f"File size: {self.export_path.stat().st_size / (1024 * 1024):.1f} MB")

        try:
            with open(self.export_path, encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in export file: {e.msg}", e.doc, e.pos)

    def _get_export_timestamp(self, conversations: list[dict[str, Any]]) -> str | None:
        """
        Find the latest updated_at timestamp from all conversations.

        Args:
            conversations: List of conversation dictionaries

        Returns:
            Latest ISO format timestamp or None if not found
        """
        timestamps = []
        for conv in conversations:
            if conv.get("updated_at"):
                timestamps.append(conv["updated_at"])

        if not timestamps:
            return None

        return max(timestamps)

    def _format_timestamp_for_dir(self, timestamp: str | None) -> str:
        """
        Format timestamp for directory name as YYYYMMDD_HHMMSS.

        Args:
            timestamp: ISO format timestamp or None

        Returns:
            Formatted timestamp string or fallback to file creation time
        """
        if timestamp:
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                return dt.strftime("%Y%m%d_%H%M%S")
            except (ValueError, AttributeError):
                pass

        file_stat = self.export_path.stat()
        return datetime.fromtimestamp(file_stat.st_ctime).strftime("%Y%m%d_%H%M%S")

    def create_output_directory(self) -> None:
        """Create output directory for individual conversation files."""
        self.output_dir.mkdir(exist_ok=True)
        print(f"Output directory: {self.output_dir}")

    def save_conversation(
        self, conversation: dict[str, Any], metadata: ConversationMetadata
    ) -> Path:
        """
        Save individual conversation to JSON file with streamlined format.

        Args:
            conversation: Raw conversation data
            metadata: Conversation metadata for naming

        Returns:
            Path to saved file
        """
        processed_messages = self.parser.process_conversation_messages(conversation)

        latest_timestamp = self.parser.find_latest_message_timestamp(processed_messages)

        timestamp_for_filename = latest_timestamp or metadata.created_at

        date_prefix = ""
        if timestamp_for_filename:
            try:
                dt = datetime.fromisoformat(timestamp_for_filename.replace("Z", "+00:00"))
                date_prefix = dt.strftime("%Y%m%d_%H%M%S_")
            except (ValueError, AttributeError):
                date_prefix = ""

        filename = f"{date_prefix}{metadata.sanitized_filename}.json"
        output_path = self.output_dir / filename

        counter = 1
        while output_path.exists():
            base_name = f"{date_prefix}{metadata.sanitized_filename}"
            filename = f"{base_name}_{counter:02d}.json"
            output_path = self.output_dir / filename
            counter += 1

        streamlined_conversation = {
            "conversation_id": metadata.conversation_id,
            "name": metadata.name,
            "messages": processed_messages,
        }

        if metadata.created_at:
            streamlined_conversation["created_at"] = metadata.created_at
        if metadata.updated_at:
            streamlined_conversation["updated_at"] = metadata.updated_at

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(streamlined_conversation, file, indent=2, ensure_ascii=False)

        return output_path

    def process_export(self) -> dict[str, Any]:
        """
        Main processing method that orchestrates the entire operation.

        Returns:
            Summary statistics of the processing operation
        """
        print("Starting Anthropic chat export processing...")

        export_data = self.load_export_data()

        conversations = self.parser.extract_conversations(export_data)
        print(f"Found {len(conversations)} conversations")

        export_timestamp = self._get_export_timestamp(conversations)
        timestamp_str = self._format_timestamp_for_dir(export_timestamp)
        self.output_dir = (
            self.base_dir / f"anthropic_{self.export_path.stem}_{timestamp_str}_simple"
        )

        self.create_output_directory()

        processed_count = 0
        skipped_count = 0
        total_messages = 0

        for index, conversation in enumerate(conversations):
            try:
                metadata = self.parser.get_conversation_metadata(conversation, index)
                output_path = self.save_conversation(conversation, metadata)

                processed_count += 1
                total_messages += metadata.message_count

                print(f"Saved: {output_path.name} ({metadata.message_count} messages)")

            except Exception as e:
                print(f"Warning: Failed to process conversation {index}: {e}")
                skipped_count += 1
                continue

        summary = {
            "total_conversations": len(conversations),
            "processed_successfully": processed_count,
            "skipped_due_to_errors": skipped_count,
            "total_messages": total_messages,
            "output_directory": str(self.output_dir),
        }

        print("\nProcessing completed!")
        print(f"Successfully processed: {processed_count} conversations")
        print(f"Total messages: {total_messages}")
        print(f"Output directory: {self.output_dir}")

        if skipped_count > 0:
            print(f"Skipped due to errors: {skipped_count}")

        return summary


def main():
    """
    CLI entry point for the chat export processor.

    Usage:
            python parse_anthropic_json_simple.py                      # Uses config.json
            python parse_anthropic_json_simple.py <path_to_export>     # Process specific file
    """
    import sys
    from pathlib import Path

    export_file_path = sys.argv[1] if len(sys.argv) > 1 else None

    if export_file_path:
        process_specific_file(Path(export_file_path))
    else:
        process_from_config()


def process_specific_file(export_file_path: Path):
    """Process a specific export file."""
    # Try to load config for output directory, fallback to None (old behavior)
    output_dir = None
    try:
        config = Config.load()
        output_dir = config.output_dir
    except Exception:
        pass  # No config or config error - use old behavior

    try:
        processor = ChatExportProcessor(export_file_path, output_dir=output_dir)
        summary = processor.process_export()

        summary_path = processor.output_dir / "processing_summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        print(f"Processing summary saved to: {summary_path}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


def process_from_config():
    """Process all files using config.json settings."""
    config = Config.load()
    config.ensure_directories()

    input_files = config.get_input_files()
    if not input_files:
        print(f"No conversation*.json files found in {config.input_dir}")
        print("Run with a specific file, or add files to the input directory.")
        sys.exit(0)

    print(f"Input directory: {config.input_dir}")
    print(f"Output directory: {config.output_dir}")
    print(f"Found {len(input_files)} file(s) to process\n")

    for input_file in input_files:
        print(f"{'=' * 60}")
        print(f"Processing: {input_file.name}")
        print(f"{'=' * 60}")

        try:
            processor = ChatExportProcessor(input_file, output_dir=config.output_dir)
            processor.process_export()

            move_to_done(input_file, config.done_dir)
            print(f"Moved to: {config.done_dir / input_file.name}\n")

        except Exception as e:
            print(f"Error processing {input_file.name}: {e}\n")
            continue


if __name__ == "__main__":
    main()
