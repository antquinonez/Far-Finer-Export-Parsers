"""Unit tests for DeepSeek parser modules."""

import pytest

from deepseek_parser import (
    extract_messages_from_mapping,
    is_deepseek_export,
    sort_messages_by_timestamp,
)


class TestDeepSeekValidators:
    """Tests for DeepSeek format detection."""

    def test_is_deepseek_export_valid(self):
        """Test detection of valid DeepSeek export."""
        data = [
            {
                "id": "test-id",
                "title": "Test",
                "mapping": {
                    "root": {"children": ["1"]},
                    "1": {"message": {"fragments": [{"type": "REQUEST", "content": "Hello"}]}},
                },
            }
        ]

        assert is_deepseek_export(data) is True

    def test_is_deepseek_export_invalid_anthropic(self):
        """Test rejection of Anthropic export."""
        data = {
            "conversations": [
                {
                    "id": "test-id",
                    "chat_messages": [{"sender": "human", "text": "Hello"}],
                }
            ]
        }

        assert is_deepseek_export(data) is False

    def test_is_deepseek_export_empty(self):
        """Test rejection of empty data."""
        assert is_deepseek_export([]) is False


class TestDeepSeekMessageExtraction:
    """Tests for message extraction from mapping."""

    def test_extract_messages_linear_chain(self):
        """Test extraction from linear message chain."""
        mapping = {
            "root": {"id": "root", "parent": None, "children": ["1"], "message": None},
            "1": {
                "id": "1",
                "parent": "root",
                "children": ["2"],
                "message": {
                    "files": [],
                    "inserted_at": "2024-01-01T10:00:00+08:00",
                    "fragments": [{"type": "REQUEST", "content": "Hello human"}],
                },
            },
            "2": {
                "id": "2",
                "parent": "1",
                "children": [],
                "message": {
                    "files": [],
                    "inserted_at": "2024-01-01T10:01:00+08:00",
                    "fragments": [{"type": "RESPONSE", "content": "Hello assistant"}],
                },
            },
        }

        messages = extract_messages_from_mapping(mapping)

        assert len(messages) == 2
        assert messages[0]["sender"] == "human"
        assert messages[0]["text"] == "Hello human"
        assert messages[1]["sender"] == "assistant"
        assert messages[1]["text"] == "Hello assistant"

    def test_extract_messages_empty_mapping(self):
        """Test extraction from empty mapping."""
        messages = extract_messages_from_mapping({})
        assert messages == []

    def test_extract_messages_no_root(self):
        """Test extraction when no root node."""
        messages = extract_messages_from_mapping({"1": {"children": []}})
        assert messages == []

    def test_extract_messages_with_files(self):
        """Test extraction preserves file attachments."""
        mapping = {
            "root": {"children": ["1"], "message": None},
            "1": {
                "children": [],
                "message": {
                    "files": [{"id": "file-1", "file_name": "test.pdf"}],
                    "inserted_at": "2024-01-01T10:00:00+08:00",
                    "fragments": [{"type": "REQUEST", "content": "See attached file"}],
                },
            },
        }

        messages = extract_messages_from_mapping(mapping)

        assert len(messages) == 1
        assert len(messages[0]["files"]) == 1
        assert messages[0]["files"][0]["file_name"] == "test.pdf"


class TestDeepSeekMessageSorting:
    """Tests for message sorting."""

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
