"""Unit tests for parser scripts."""

import pytest

from parse_anthropic_json import ChatExportProcessor as FullJsonProcessor
from parse_anthropic_json import ConversationParser as FullJsonParser
from parse_anthropic_json_simple import ChatExportProcessor as SimpleJsonProcessor
from parse_anthropic_json_simple import ConversationParser as SimpleJsonParser
from parse_anthropic_json_simple import MessageExtractor
from parse_anthropic_markdown import ChatExportProcessor as MarkdownProcessor
from parse_anthropic_markdown import ConversationParser as MarkdownParser
from parse_anthropic_markdown import MarkdownFormatter


class TestFullJsonParser:
    """Tests for ConversationParser (full JSON output)."""

    def test_sanitize_filename_special_chars(self):
        """Test filename sanitization removes special characters."""
        parser = FullJsonParser()

        assert parser.sanitize_filename("Test: <Special> Chars") == "Test_Special_Chars"
        assert parser.sanitize_filename("Test/Path|Chars") == "Test_Path_Chars"

    def test_sanitize_filename_whitespace(self):
        """Test filename sanitization handles whitespace."""
        parser = FullJsonParser()

        assert parser.sanitize_filename("  Test  Name  ") == "Test_Name"

    def test_sanitize_filename_empty(self):
        """Test filename sanitization handles empty string."""
        parser = FullJsonParser()

        assert parser.sanitize_filename("") == "untitled_conversation"

    def test_sanitize_filename_truncation(self):
        """Test filename sanitization truncates long names."""
        parser = FullJsonParser(max_filename_length=10)

        result = parser.sanitize_filename("A" * 100)
        assert len(result) <= 10

    def test_extract_conversations(self, sample_export_data):
        """Test conversation extraction."""
        parser = FullJsonParser()
        conversations = parser.extract_conversations(sample_export_data)

        assert len(conversations) == 1
        assert conversations[0]["id"] == "conv_simple"
        assert conversations[0]["name"] == "Simple Test"

    def test_get_conversation_metadata(self, sample_export_data):
        """Test conversation metadata extraction."""
        parser = FullJsonParser()
        conversation = sample_export_data["conversations"][0]

        metadata = parser.get_conversation_metadata(conversation, 0)

        assert metadata.conversation_id == "conv_simple"
        assert metadata.name == "Simple Test"
        assert metadata.sanitized_filename == "Simple_Test"
        assert metadata.message_count == 2
        assert metadata.created_at == "2024-01-01T10:00:00Z"

    def test_processor_creates_output(self, sample_export_path, tmp_path):
        """Test processor creates output files."""
        processor = FullJsonProcessor(sample_export_path, output_dir=tmp_path)
        summary = processor.process_export()

        assert summary["total_conversations"] == 1
        assert summary["processed_successfully"] == 1
        assert summary["skipped_due_to_errors"] == 0
        assert processor.output_dir.exists()


class TestSimpleJsonParser:
    """Tests for SimpleConversationParser (simplified JSON output)."""

    def test_message_extractor_text(self):
        """Test message text extraction."""
        extractor = MessageExtractor()

        message = {"type": "user", "text": "Hello", "created_at": "2024-01-01T10:00:00Z"}
        result = extractor.extract_message_text(message)
        assert result == "Hello"

    def test_message_extractor_sender(self):
        """Test sender extraction with sender field."""
        extractor = MessageExtractor()

        message = {"sender": "Human", "text": "Hello"}
        result = extractor.extract_sender_info(message)
        assert result == "human"

    def test_message_extractor_sender_from_string(self):
        """Test sender extraction infers from string representation."""
        extractor = MessageExtractor()

        message = {"type": "user", "text": "Hello"}
        result = extractor.extract_sender_info(message)
        assert result == "human"

    def test_get_conversation_metadata(self, sample_export_data):
        """Test conversation metadata extraction."""
        parser = SimpleJsonParser()
        conversation = sample_export_data["conversations"][0]

        metadata = parser.get_conversation_metadata(conversation, 0)

        assert metadata.sanitized_filename == "Simple_Test"
        assert metadata.message_count == 2

    def test_processor_creates_output(self, sample_export_path, tmp_path):
        """Test processor creates output files."""
        processor = SimpleJsonProcessor(sample_export_path, output_dir=tmp_path)
        summary = processor.process_export()

        assert summary["total_conversations"] == 1
        assert summary["processed_successfully"] == 1


class TestMarkdownParser:
    """Tests for MarkdownConversationParser (markdown output)."""

    def test_markdown_formatter_timestamp(self):
        """Test timestamp formatting."""
        result = MarkdownFormatter.format_timestamp("2024-01-01T10:00:00Z")
        assert "January 01, 2024" in result

    def test_markdown_formatter_sender_names(self):
        """Test sender name formatting."""
        assert "Human" in MarkdownFormatter.format_sender_name("human")
        assert "Assistant" in MarkdownFormatter.format_sender_name("assistant")

    def test_markdown_formatter_message(self):
        """Test message formatting."""
        message = {"sender": "user", "text": "Hello", "created_at": "2024-01-01T10:00:00Z"}
        result = MarkdownFormatter.format_message(message, 0)

        assert "Hello" in result
        assert "January 01, 2024" in result

    def test_get_conversation_metadata(self, sample_export_data):
        """Test conversation metadata extraction."""
        parser = MarkdownParser()
        conversation = sample_export_data["conversations"][0]

        metadata = parser.get_conversation_metadata(conversation, 0)

        assert metadata.sanitized_filename == "Simple_Test"
        assert metadata.message_count == 2

    def test_processor_creates_output(self, sample_export_path, tmp_path):
        """Test processor creates output files."""
        processor = MarkdownProcessor(sample_export_path, output_dir=tmp_path)
        summary = processor.process_export()

        assert summary["total_conversations"] == 1
        assert summary["processed_successfully"] == 1


class TestComplexExports:
    """Tests with complex export data."""

    def test_full_json_special_characters(self, complex_export_data):
        """Test handling special characters in names."""
        parser = FullJsonParser()
        conversation = complex_export_data["conversations"][0]

        metadata = parser.get_conversation_metadata(conversation, 0)

        assert "Special" in metadata.sanitized_filename
        assert "<" not in metadata.sanitized_filename
        assert "/" not in metadata.sanitized_filename

    def test_empty_conversation_name(self, complex_export_data):
        """Test handling empty conversation name."""
        parser = FullJsonParser()
        conversation = complex_export_data["conversations"][1]

        metadata = parser.get_conversation_metadata(conversation, 1)

        assert metadata.sanitized_filename == "Conversation_2"

    def test_empty_messages(self, complex_export_data):
        """Test handling conversation with no messages."""
        parser = FullJsonParser()
        conversation = complex_export_data["conversations"][2]

        metadata = parser.get_conversation_metadata(conversation, 2)

        assert metadata.message_count == 0

    @pytest.mark.parametrize("parser_class", [FullJsonParser, SimpleJsonParser, MarkdownParser])
    def test_all_parsers_handle_complex_data(self, parser_class, complex_export_data):
        """Test all parsers handle complex export data."""
        parser = parser_class()
        conversation = complex_export_data["conversations"][0]

        metadata = parser.get_conversation_metadata(conversation, 0)

        assert metadata.message_count == 4
