"""Unit tests for anthropic_parser modules."""

import tempfile
from pathlib import Path

from anthropic_parser.config import Config
from anthropic_parser.file_manager import move_to_done
from anthropic_parser.message_utils import sort_messages_by_timestamp


class TestConfig:
    """Tests for Config class."""

    def test_config_initialization(self):
        """Test Config initializes with correct directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            output_dir = Path(tmpdir) / "output"

            config = Config(input_dir=input_dir, output_dir=output_dir)

            assert config.input_dir == input_dir
            assert config.output_dir == output_dir
            assert config.done_dir == input_dir / "done"

    def test_config_ensure_directories(self):
        """Test directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(input_dir=Path(tmpdir) / "input", output_dir=Path(tmpdir) / "output")

            config.ensure_directories()

            assert config.input_dir.exists()
            assert config.output_dir.exists()
            assert config.done_dir.exists()

    def test_config_get_input_files_empty(self):
        """Test get_input_files returns empty list when directory empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(input_dir=Path(tmpdir) / "input", output_dir=Path(tmpdir) / "output")
            config.ensure_directories()

            files = config.get_input_files()

            assert files == []

    def test_config_get_input_files_finds_matching_files(self):
        """Test get_input_files finds conversation*.json files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(input_dir=Path(tmpdir) / "input", output_dir=Path(tmpdir) / "output")
            config.ensure_directories()

            (config.input_dir / "conversations.json").touch()
            (config.input_dir / "conversation_2024.json").touch()
            (config.input_dir / "other.json").touch()

            files = config.get_input_files()

            assert len(files) == 2
            assert all("conversation" in f.name for f in files)


class TestFileManager:
    """Tests for file_manager module."""

    def test_move_to_done_moves_file(self):
        """Test moving file to done directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            done_dir = Path(tmpdir) / "done"
            input_dir.mkdir()
            done_dir.mkdir()

            test_file = input_dir / "test.json"
            test_file.write_text("test content")

            result = move_to_done(test_file, done_dir)

            assert not test_file.exists()
            assert result.exists()
            assert result.parent == done_dir
            assert result.read_text() == "test content"

    def test_move_to_done_handles_conflict(self):
        """Test filename conflict resolution."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_dir = Path(tmpdir) / "input"
            done_dir = Path(tmpdir) / "done"
            input_dir.mkdir()
            done_dir.mkdir()

            test_file = input_dir / "test.json"
            test_file.write_text("new content")

            existing_file = done_dir / "test.json"
            existing_file.write_text("existing content")

            result = move_to_done(test_file, done_dir)

            assert not test_file.exists()
            assert result.exists()
            assert result.name != "test.json"
            assert existing_file.read_text() == "existing content"


class TestMessageUtils:
    """Tests for message_utils module."""

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
