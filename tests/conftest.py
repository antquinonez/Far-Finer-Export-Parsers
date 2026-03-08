"""Pytest configuration and fixtures."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def sample_export_path():
    """Path to sample Anthropic export JSON file."""
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
def sample_deepseek_export():
    """Sample DeepSeek export data."""
    return [
        {
            "id": "test-conv-1",
            "title": "Test DeepSeek Conversation",
            "inserted_at": "2024-01-01T10:00:00+08:00",
            "updated_at": "2024-01-01T11:00:00+08:00",
            "mapping": {
                "root": {"id": "root", "parent": None, "children": ["1"], "message": None},
                "1": {
                    "id": "1",
                    "parent": "root",
                    "children": ["2"],
                    "message": {
                        "files": [],
                        "model": "deepseek-chat",
                        "inserted_at": "2024-01-01T10:00:00+08:00",
                        "fragments": [{"type": "REQUEST", "content": "Hello from human"}],
                    },
                },
                "2": {
                    "id": "2",
                    "parent": "1",
                    "children": [],
                    "message": {
                        "files": [],
                        "model": "deepseek-chat",
                        "inserted_at": "2024-01-01T10:01:00+08:00",
                        "fragments": [{"type": "RESPONSE", "content": "Hello from assistant"}],
                    },
                },
            },
        }
    ]


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory."""
    return tmp_path
