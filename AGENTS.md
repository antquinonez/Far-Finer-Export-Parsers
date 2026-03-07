# AGENTS.md

Guidelines for agentic coding assistants working in this repository.

## Project Overview

Python 3.10+ project for parsing Anthropic chat export JSON files into structured formats (JSON, simplified JSON, or Markdown). Source files are located in `src/`.

## Installation

```bash
# Quick install (creates venv and installs package)
./install.sh

# Activate virtual environment
source .venv/bin/activate

# Or manual install
pip install -e ".[dev]"
```

## Commands

### Running Parsers

After installation, commands are available:

```bash
parse-anthropic-json <file>        # Full JSON output
parse-anthropic-json-simple <file> # Simplified JSON output
parse-anthropic-markdown <file>    # Markdown output
```

Or run directly without installation:

```bash
# Full JSON output (preserves all data)
python src/parse_anthropic_json.py <path_to_export.json>

# Simplified JSON output (sender, text, timestamp only)
python src/parse_anthropic_json_simple.py <path_to_export.json>

# Markdown output (human-readable)
python src/parse_anthropic_markdown.py <path_to_export.json>
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parser.py

# Run single test with verbose output
pytest tests/test_parser.py::test_extract_message_text -v

# Run with coverage
pytest --cov=src tests/
```

### Linting & Formatting

```bash
# Check for issues
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .

# Check formatting without changes
ruff format . --check
```

### Type Checking

```bash
mypy src/
```

## Code Style

### Python Version

- Target Python 3.10+ (use modern union syntax `str | None` instead of `Optional[str]`)

### Imports

Group and order imports as follows:

```python
# Standard library (alphabetical)
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
```

- Use `from typing` for type hints when needed
- Import `dataclass` decorator from `dataclasses`
- Use `Path` from `pathlib` for file operations

### Type Hints

```python
# Use typing module for complex types
def process(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    ...

# Use | for unions (Python 3.10+)
def load_file(path: str | Path) -> Dict[str, Any]:
    ...

# Use Optional for optional parameters
def get_item(id: str, default: Optional[str] = None) -> str:
    ...

# Use dataclasses for data structures
@dataclass
class MessageData:
    sender: str
    text: str
    created_at: Optional[str] = None
```

### Naming Conventions

- **Variables/functions**: `snake_case` (e.g., `extract_message_text`, `processed_messages`)
- **Classes**: `PascalCase` (e.g., `ConversationParser`, `ChatExportProcessor`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `MAX_FILENAME_LENGTH`)
- **Private methods**: prefix with underscore (e.g., `_internal_helper`)

### Docstrings

Use Google-style docstrings:

```python
def extract_message_text(self, message: Dict[str, Any]) -> str:
    """
    Extract text content from a message, handling various formats.
    
    Args:
        message: Raw message data from export
        
    Returns:
        Extracted text content
    """
```

- Module-level docstrings at top of file with triple quotes
- Class docstrings describe purpose
- Method docstrings include Args and Returns sections

### Data Structures

- Use `@dataclass` for simple data containers
- Group related data in classes with clear responsibilities

```python
@dataclass
class ConversationMetadata:
    conversation_id: str
    name: str
    sanitized_filename: str
    message_count: int
    created_at: Optional[str] = None
```

### Error Handling

```python
# Catch specific exceptions
try:
    data = json.load(file)
except json.JSONDecodeError as e:
    raise json.JSONDecodeError(f"Invalid JSON: {e.msg}", e.doc, e.pos)

# Warn and continue pattern for batch processing
for item in items:
    try:
        process(item)
    except Exception as e:
        print(f"Warning: Failed to process item: {e}")
        continue
```

- Raise exceptions with descriptive messages
- Use `FileNotFoundError` for missing files
- Print warnings for recoverable errors in batch operations

### Formatting

- 4-space indentation
- Max line length: 100 characters
- Blank lines between class methods
- No trailing whitespace

### CLI Entry Point

Use standard pattern:

```python
def main():
    """CLI entry point."""
    import sys
    
    if len(sys.argv) != 2:
        print("Usage: python script.py <path>")
        sys.exit(1)
    
    # Process and handle errors
    try:
        processor = Processor(sys.argv[1])
        processor.run()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

## Architecture

- **Separation of concerns**: Parser classes handle data extraction, Processor classes orchestrate I/O
- **Single responsibility**: Each class has one clear purpose
- **Progress reporting**: Print status messages to stdout during processing
- **Output organization**: Create timestamped output directories

## File Organization

```
src/
  parse_anthropic_json.py        # Full JSON output parser
  parse_anthropic_json_simple.py # Simplified JSON output parser
  parse_anthropic_markdown.py    # Markdown output parser
tests/
  test_parser.py                 # Unit tests
pyproject.toml                   # Package config, dependencies, tool settings
install.sh                       # Installation script
README.md                        # Project documentation
```
