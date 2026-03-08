"""Unit tests for parser scripts."""

import pytest

from anthropic_parser import is_anthropic_export, sort_messages_by_timestamp
from common import ConversationMetadata, MarkdownFormatter, MessageData, sanitize_filename
from common.formatting import format_timestamp
from deepseek_parser import extract_messages_from_mapping, is_deepseek_export


class TestCommonUtilities:
    """Tests for shared utilities in common package."""

    def test_sanitize_filename_special_chars(self):
        """Test filename sanitization removes special characters."""
        assert sanitize_filename("Test: <Special> Chars") == "Test_Special_Chars"
        assert sanitize_filename("Test/Path|Chars") == "Test_Path_Chars"

    def test_sanitize_filename_whitespace(self):
        """Test filename sanitization handles whitespace."""
        assert sanitize_filename("  Test  Name  ") == "Test_Name"

    def test_sanitize_filename_empty(self):
        """Test filename sanitization handles empty string."""
        assert sanitize_filename("") == "untitled_conversation"

    def test_sanitize_filename_truncation(self):
        """Test filename sanitization truncates long names."""
        result = sanitize_filename("A" * 100, max_length=10)
        assert len(result) <= 10

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        result = format_timestamp("2024-01-01T10:00:00Z")
        assert "January 01, 2024" in result

    def test_format_timestamp_none(self):
        """Test timestamp formatting with None."""
        assert format_timestamp(None) == "N/A"


class TestMarkdownFormatter:
    """Tests for MarkdownFormatter."""

    def test_format_timestamp_method(self):
        """Test timestamp formatting via formatter."""
        formatter = MarkdownFormatter()
        result = formatter.format_sender_name("human")
        assert "Human" in result

    def test_format_sender_name_anthropic(self):
        """Test sender name formatting for Anthropic."""
        formatter = MarkdownFormatter(assistant_display_name="Claude")
        assert formatter.format_sender_name("assistant") == "🤖 Claude"
        assert formatter.format_sender_name("human") == "👤 Human"

    def test_format_sender_name_deepseek(self):
        """Test sender name formatting for DeepSeek."""
        formatter = MarkdownFormatter(assistant_display_name="DeepSeek")
        assert formatter.format_sender_name("assistant") == "🤖 DeepSeek"
        assert formatter.format_sender_name("human") == "👤 Human"

    def test_create_markdown_header(self):
        """Test markdown header creation."""
        formatter = MarkdownFormatter()
        metadata = ConversationMetadata(
            conversation_id="test-id",
            name="Test Conversation",
            sanitized_filename="Test_Conversation",
            message_count=5,
            created_at="2024-01-01T10:00:00Z",
        )

        header = formatter.create_markdown_header(metadata, None)

        assert "# Test Conversation" in header
        assert "test-id" in header
        assert "5" in header

    def test_format_message(self):
        """Test message formatting."""
        formatter = MarkdownFormatter()
        message = {"sender": "human", "text": "Hello", "created_at": "2024-01-01T10:00:00Z"}

        result = formatter.format_message(message, 0)

        assert "Hello" in result
        assert "Human" in result


class TestAnthropicValidators:
    """Tests for Anthropic format validation."""

    def test_is_anthropic_export_valid(self, sample_export_data):
        """Test detection of valid Anthropic export."""
        assert is_anthropic_export(sample_export_data) is True

    def test_is_anthropic_export_invalid(self, sample_deepseek_export):
        """Test rejection of non-Anthropic export."""
        assert is_anthropic_export(sample_deepseek_export) is False


class TestDeepSeekValidators:
    """Tests for DeepSeek format validation."""

    def test_is_deepseek_export_valid(self, sample_deepseek_export):
        """Test detection of valid DeepSeek export."""
        assert is_deepseek_export(sample_deepseek_export) is True

    def test_is_deepseek_export_invalid(self, sample_export_data):
        """Test rejection of non-DeepSeek export."""
        assert is_deepseek_export(sample_export_data) is False


class TestDeepSeekMessageExtraction:
    """Tests for DeepSeek message extraction from mapping."""

    def test_extract_messages_from_mapping(self, sample_deepseek_export):
        """Test message extraction from DeepSeek mapping structure."""
        mapping = sample_deepseek_export[0]["mapping"]
        messages = extract_messages_from_mapping(mapping)

        assert len(messages) == 2
        assert messages[0]["sender"] == "human"
        assert messages[0]["text"] == "Hello from human"
        assert messages[1]["sender"] == "assistant"
        assert messages[1]["text"] == "Hello from assistant"

    def test_extract_messages_empty_mapping(self):
        """Test extraction from empty mapping."""
        messages = extract_messages_from_mapping({})
        assert messages == []


class TestMessageSorting:
    """Tests for message sorting utilities."""

    def test_sort_messages_by_timestamp(self):
        """Test sorting messages by timestamp."""
        messages = [
            {"created_at": "2024-01-01T12:00:00Z", "text": "Middle"},
            {"created_at": "2024-01-01T10:00:00Z", "text": "First"},
            {"created_at": "2024-01-01T14:00:00Z", "text": "Last"},
        ]

        sorted_messages = sort_messages_by_timestamp(messages)

        assert sorted_messages[0]["text"] == "First"
        assert sorted_messages[1]["text"] == "Middle"
        assert sorted_messages[2]["text"] == "Last"

    def test_sort_messages_empty_list(self):
        """Test sorting empty message list."""
        sorted_messages = sort_messages_by_timestamp([])
        assert sorted_messages == []

    def test_sort_messages_missing_timestamp(self):
        """Test messages without timestamps placed at end."""
        messages = [
            {"created_at": "2024-01-01T12:00:00Z", "text": "Has timestamp"},
            {"text": "No timestamp"},
        ]

        sorted_messages = sort_messages_by_timestamp(messages)

        assert sorted_messages[0]["text"] == "Has timestamp"
        assert sorted_messages[1]["text"] == "No timestamp"


class TestModels:
    """Tests for data models."""

    def test_conversation_metadata(self):
        """Test ConversationMetadata dataclass."""
        metadata = ConversationMetadata(
            conversation_id="test-id",
            name="Test Name",
            sanitized_filename="Test_Name",
            message_count=10,
            created_at="2024-01-01T00:00:00Z",
        )

        assert metadata.conversation_id == "test-id"
        assert metadata.name == "Test Name"
        assert metadata.message_count == 10
        assert metadata.latest_message_at is None

    def test_message_data(self):
        """Test MessageData dataclass."""
        message = MessageData(sender="human", text="Hello", created_at="2024-01-01T00:00:00Z")

        assert message.sender == "human"
        assert message.text == "Hello"
        assert message.created_at == "2024-01-01T00:00:00Z"
