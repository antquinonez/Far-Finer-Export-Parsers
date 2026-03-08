"""
Anthropic Chat Export Parser

Parses Anthropic chat export JSON files and organizes conversations
into separate files with proper naming conventions.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))

from anthropic_parser import is_anthropic_export, sort_messages_by_timestamp
from common import (
    Config,
    ConversationMetadata,
    MessageData,
    move_to_done,
    sanitize_filename,
)


class ConversationParser:
    """
    Parses Anthropic chat export data and extracts individual conversations.
    """

    def extract_conversations(self, export_data: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Extract conversations from export data structure.

        Args:
            export_data: Parsed JSON export data

        Returns:
            List of conversation dictionaries

        Raises:
            ValueError: If no conversations found in export
        """
        conversations = None

        if "conversations" in export_data:
            conversations = export_data["conversations"]
        elif "data" in export_data and "conversations" in export_data["data"]:
            conversations = export_data["data"]["conversations"]
        elif isinstance(export_data, list):
            conversations = export_data
        else:
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

    def find_latest_message_timestamp(self, conversation: dict[str, Any]) -> str | None:
        """
        Find the latest created_at timestamp from messages in a conversation.

        Args:
            conversation: Conversation data

        Returns:
            Latest ISO format timestamp or None if no timestamps found
        """
        messages = (
            conversation.get("messages", [])
            or conversation.get("chat_messages", [])
            or conversation.get("conversation", {}).get("chat_messages", [])
        )

        if not isinstance(messages, list):
            return None

        timestamps = []

        for message in messages:
            if isinstance(message, dict):
                timestamp_fields = ["created_at", "timestamp", "time", "date"]
                for field in timestamp_fields:
                    if field in message and message[field]:
                        timestamps.append(message[field])
                        break

        if not timestamps:
            return None

        try:
            datetime_objects = []
            for ts in timestamps:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    datetime_objects.append((dt, ts))
                except (ValueError, AttributeError):
                    continue

            if datetime_objects:
                datetime_objects.sort(key=lambda x: x[0])
                return datetime_objects[-1][1]
            else:
                return sorted(timestamps)[-1]

        except Exception:
            return timestamps[-1] if timestamps else None

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
        conv_id = (
            conversation.get("id")
            or conversation.get("uuid")
            or (conversation.get("conversation", {}).get("uuid"))
            or f"conversation_{index:04d}"
        )

        name = (
            conversation.get("name")
            or conversation.get("title")
            or conversation.get("summary")
            or (conversation.get("conversation", {}).get("name"))
            or f"Conversation {index + 1}"
        )

        messages = (
            conversation.get("messages", [])
            or conversation.get("chat_messages", [])
            or conversation.get("conversation", {}).get("chat_messages", [])
        )
        message_count = len(messages) if isinstance(messages, list) else 0

        created_at = conversation.get("created_at") or conversation.get("conversation", {}).get(
            "created_at"
        )
        updated_at = conversation.get("updated_at") or conversation.get("conversation", {}).get(
            "updated_at"
        )

        latest_message_at = self.find_latest_message_timestamp(conversation)

        return ConversationMetadata(
            conversation_id=conv_id,
            name=name,
            sanitized_filename=sanitize_filename(name),
            message_count=message_count,
            created_at=created_at,
            updated_at=updated_at,
            latest_message_at=latest_message_at,
        )


class ChatExportProcessor:
    """
    Main processor for handling Anthropic chat export files.
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
        self.provider_name = "anthropic"

    def load_export_data(self) -> dict[str, Any]:
        """
        Load and parse the export JSON file.

        Returns:
            Parsed JSON data

        Raises:
            json.JSONDecodeError: If file is not valid JSON
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

    def create_output_directory(self, output_prefix: str) -> None:
        """Create output directory for individual conversation files."""
        self.output_dir.mkdir(exist_ok=True)
        print(f"Output directory: {self.output_dir}")

    def save_conversation(
        self, conversation: dict[str, Any], metadata: ConversationMetadata
    ) -> Path:
        """
        Save individual conversation to JSON file.

        Args:
            conversation: Conversation data to save
            metadata: Conversation metadata for naming

        Returns:
            Path to saved file
        """
        timestamp_for_filename = metadata.latest_message_at or metadata.created_at

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

        sorted_conversation = self._sort_conversation_messages(conversation)

        conversation_with_metadata = {
            "metadata": {
                "conversation_id": metadata.conversation_id,
                "original_name": metadata.name,
                "message_count": metadata.message_count,
                "created_at": metadata.created_at,
                "updated_at": metadata.updated_at,
                "latest_message_at": metadata.latest_message_at,
                "exported_at": datetime.now().isoformat(),
            },
            "conversation": sorted_conversation,
        }

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(conversation_with_metadata, file, indent=2, ensure_ascii=False)

        return output_path

    def _sort_conversation_messages(self, conversation: dict[str, Any]) -> dict[str, Any]:
        """
        Sort messages within a conversation by timestamp.

        Args:
            conversation: Raw conversation data

        Returns:
            Conversation with sorted messages
        """
        result = dict(conversation)

        if "conversation" in conversation and isinstance(conversation["conversation"], dict):
            nested = dict(conversation["conversation"])
            if "chat_messages" in nested and isinstance(nested["chat_messages"], list):
                nested["chat_messages"] = sort_messages_by_timestamp(nested["chat_messages"])
            result["conversation"] = nested
        elif "chat_messages" in conversation and isinstance(conversation["chat_messages"], list):
            result["chat_messages"] = sort_messages_by_timestamp(conversation["chat_messages"])
        elif "messages" in conversation and isinstance(conversation["messages"], list):
            result["messages"] = sort_messages_by_timestamp(conversation["messages"])

        return result

    def process_export(self, output_prefix: str = "anthropic") -> dict[str, Any]:
        """
        Main processing method that orchestrates the entire operation.

        Args:
            output_prefix: Prefix for output directory name

        Returns:
            Summary statistics of the processing operation
        """
        print("Starting Anthropic chat export processing...")

        export_data = self.load_export_data()

        conversations = self.parser.extract_conversations(export_data)
        print(f"Found {len(conversations)} conversations")

        export_timestamp = self._get_export_timestamp(conversations)
        timestamp_str = self._format_timestamp_for_dir(export_timestamp)
        self.output_dir = self.base_dir / f"{output_prefix}_{self.export_path.stem}_{timestamp_str}"

        self.create_output_directory(output_prefix)

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
            python parse_anthropic_json.py                      # Uses config.json
            python parse_anthropic_json.py <path_to_export>     # Process specific file
    """
    from pathlib import Path

    export_file_path = sys.argv[1] if len(sys.argv) > 1 else None

    if export_file_path:
        process_specific_file(Path(export_file_path))
    else:
        process_from_config()


def process_specific_file(export_file_path: Path):
    """Process a specific export file."""
    config = Config.load()
    output_dir = config.output_dir

    with open(export_file_path, encoding="utf-8") as f:
        data = json.load(f)

    if not is_anthropic_export(data):
        print(f"Skipping {export_file_path}: Not an Anthropic export format")
        sys.exit(0)

    try:
        processor = ChatExportProcessor(export_file_path, output_dir=output_dir)
        provider_config = config.get_provider_config("anthropic")
        summary = processor.process_export(output_prefix=provider_config.output_prefix)

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

    provider_config = config.get_provider_config("anthropic")

    print(f"Input directory: {config.input_dir}")
    print(f"Output directory: {config.output_dir}")
    print(f"Found {len(input_files)} file(s) to process\n")

    processed_files: list[str] = []
    skipped_files: list[str] = []

    for input_file in input_files:
        print(f"{'=' * 60}")
        print(f"Processing: {input_file.name}")
        print(f"{'=' * 60}")

        with open(input_file, encoding="utf-8") as f:
            data = json.load(f)

        if not is_anthropic_export(data):
            print(f"Skipping: Not an Anthropic export format\n")
            skipped_files.append(input_file.name)
            continue

        try:
            processor = ChatExportProcessor(input_file, output_dir=config.output_dir)
            processor.process_export(output_prefix=provider_config.output_prefix)

            move_to_done(input_file, config.done_dir)
            print(f"Moved to: {config.done_dir / input_file.name}\n")
            processed_files.append(input_file.name)

        except Exception as e:
            print(f"Error processing {input_file.name}: {e}\n")
            continue

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    if processed_files:
        print(f"\nPROCESSED ({len(processed_files)} file(s)):")
        for f in processed_files:
            print(f"  - {f}")

    if skipped_files:
        print(f"\nSKIPPED ({len(skipped_files)} file(s)):")
        for f in skipped_files:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
