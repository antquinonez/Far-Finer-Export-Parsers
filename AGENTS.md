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

## Structured Analysis & Planning

For complex refactoring or architectural changes, create structured documentation in `working_docs/` (not tracked in git).

### Recommended Document Structure

```
working_docs/
  01-analysis.md    # Current state, duplication, issues
  02-plan.md        # Proposed architecture, implementation phases
  03-test-plan.md   # Test fixtures, unit tests, integration tests
  README.md         # Summary and next steps
```

### Analysis Document Template

1. **Executive Summary** - High-level findings
2. **Current State** - File statistics, line counts
3. **Duplication Analysis** - Identical code, near-identical code
4. **Dependency Graph** - Class relationships
5. **Issues Identified** - Problems to address
6. **Complexity Metrics** - Cyclomatic complexity, method lengths
7. **Risk Assessment** - Before/after comparison

### Planning Document Template

1. **Overview** - Goals and approach
2. **Proposed Architecture** - Directory structure
3. **Implementation Phases** - Numbered steps with code examples
4. **Estimated Line Counts** - Before/after comparison

### Test Plan Template

1. **Test Structure** - Directory layout
2. **Test Fixtures** - Shared test data (pytest fixtures)
3. **Unit Tests** - Per-module test specifications
4. **Integration Tests** - End-to-end test scenarios
5. **Coverage Goals** - Per-module targets

### Example: Refactoring Request

When asked to analyze and plan a refactoring:

1. Read all relevant source files
2. Calculate duplication metrics
3. Identify shared vs unique code
4. Create `working_docs/01-analysis.md` with findings
5. Design modular architecture
6. Create `working_docs/02-plan.md` with code examples
7. Define comprehensive test suite
8. Create `working_docs/03-test-plan.md` with pytest specs
9. Create `working_docs/README.md` summarizing next steps

## File Organization

```
src/
  parse_anthropic_json.py        # Full JSON output parser (CLI)
  parse_anthropic_json_simple.py # Simplified JSON output parser (CLI)
  parse_anthropic_markdown.py    # Markdown output parser (CLI)
  batch_processor.py             # Batch processing with config support
  anthropic_parser/              # Shared modules package
    __init__.py
    config.py                    # Configuration management
    file_manager.py              # File moving with conflict handling
tests/
  test_parser.py                 # Unit tests
pyproject.toml                   # Package config, dependencies, tool settings
install.sh                       # Installation script
README.md                        # Project documentation
working_docs/                    # Analysis & planning (not tracked in git)
config.json                      # Input/output directory config (auto-created)
input/                           # Default input directory
  done/                          # Processed files moved here
output/                          # Default output directory
```

## Batch Processing

For processing multiple files with automatic file management:

```bash
# Process all conversation*.json files in input directory
python src/batch_processor.py

# Override input/output directories
python src/batch_processor.py --input ./my_exports --output ./results

# First run creates config.json with defaults
```

### Batch Processing Features

- **Auto-discovery**: Finds all `conversation*.json` files in input directory
- **Config-based**: Uses `config.json` for default paths (auto-created)
- **File management**: Moves processed files to `input/done/`
- **Conflict handling**: Renames duplicates using file creation date or `_N` suffix
- **Summary output**: Creates `batch_results.json` and `processing_summary.json`

### Conflict Resolution

When moving files to `done/`, conflicts are handled by:
1. If file exists, append creation date: `conversations_20250407.json`
2. If still conflicts, add counter: `conversations_20250407_1.json`
