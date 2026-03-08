"""Unit tests for common modules."""

import tempfile
from pathlib import Path

from common import Config, ProviderConfig, move_to_done
from common.formatting import sanitize_filename


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

    def test_config_default_providers(self):
        """Test default provider configurations."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(input_dir=Path(tmpdir) / "input", output_dir=Path(tmpdir) / "output")

            anthropic_config = config.get_provider_config("anthropic")
            assert anthropic_config.output_prefix == "anthropic"
            assert anthropic_config.assistant_display_name == "Claude"

            deepseek_config = config.get_provider_config("deepseek")
            assert deepseek_config.output_prefix == "deepseek"
            assert deepseek_config.assistant_display_name == "DeepSeek"

    def test_config_unknown_provider(self):
        """Test unknown provider returns sensible defaults."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config = Config(input_dir=Path(tmpdir) / "input", output_dir=Path(tmpdir) / "output")

            unknown_config = config.get_provider_config("unknown_provider")
            assert unknown_config.output_prefix == "unknown_provider"
            assert unknown_config.assistant_display_name == "Unknown_Provider"


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


class TestFormatting:
    """Tests for formatting utilities."""

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
