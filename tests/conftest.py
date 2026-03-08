"""Pytest configuration and fixtures."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_export_path():
    """Path to sample export JSON file."""
    return Path(__file__).parent / "fixtures" / "sample_export.json"


@pytest.fixture
def sample_export_data(sample_export_path):
    """Load sample export data."""
    with open(sample_export_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def complex_export_path():
    """Path to complex export JSON file."""
    return Path(__file__).parent / "fixtures" / "complex_export.json"


@pytest.fixture
def complex_export_data(complex_export_path):
    """Load complex export data."""
    with open(complex_export_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory."""
    return tmp_path
