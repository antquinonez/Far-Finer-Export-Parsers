"""Integration tests for batch processor."""

import json
import shutil
from pathlib import Path

from batch_processor import process_single_file


class TestBatchProcessor:
    """Tests for batch processing functions."""

    def test_process_single_file(self, sample_export_path, tmp_path):
        """Test processing a single file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        input_file = tmp_path / "conversations.json"
        shutil.copy(sample_export_path, input_file)

        result = process_single_file(input_file, output_dir)

        assert result is not None
        assert result["total_conversations"] == 1
        assert result["processed_successfully"] == 1
        assert result["skipped_due_to_errors"] == 0
        assert Path(result["output_directory"]).exists()

    def test_process_single_file_creates_json(self, sample_export_path, tmp_path):
        """Test processing creates JSON output files."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        input_file = tmp_path / "conversations.json"
        shutil.copy(sample_export_path, input_file)

        result = process_single_file(input_file, output_dir)

        output_path = Path(result["output_directory"])
        json_files = list(output_path.glob("*.json"))

        assert len(json_files) >= 1
        assert any("Simple_Test" in f.name for f in json_files)

    def test_process_single_file_creates_summary(self, sample_export_path, tmp_path):
        """Test processing creates summary file."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        input_file = tmp_path / "conversations.json"
        shutil.copy(sample_export_path, input_file)

        result = process_single_file(input_file, output_dir)

        output_path = Path(result["output_directory"])
        summary_path = output_path / "processing_summary.json"

        assert summary_path.exists()

        with open(summary_path) as f:
            summary = json.load(f)

        assert summary["total_conversations"] == 1
        assert "output_directory" in summary

    def test_process_single_file_complex_data(self, complex_export_path, tmp_path):
        """Test processing complex export with multiple conversations."""
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        input_file = tmp_path / "conversations.json"
        shutil.copy(complex_export_path, input_file)

        result = process_single_file(input_file, output_dir)

        assert result["total_conversations"] == 3
        assert result["processed_successfully"] == 3
