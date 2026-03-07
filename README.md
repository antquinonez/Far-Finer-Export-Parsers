# Anthropic Chat Export Parser

Parse Anthropic chat export JSON files into structured formats: full JSON, simplified JSON, or Markdown.

## Installation

### Quick Install

```bash
./install.sh
```

This creates a virtual environment (`.venv`) and installs the package in editable mode with dev dependencies.

### Manual Install

```bash
# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install in editable mode
pip install -e .

# With dev dependencies (pytest, ruff, mypy)
pip install -e ".[dev]"
```

## Usage

### Command Line

After installation, use the installed commands:

```bash
# Full JSON output (preserves all data)
parse-anthropic-json <path_to_export.json>

# Simplified JSON output (sender, text, timestamp only)
parse-anthropic-json-simple <path_to_export.json>

# Markdown output (human-readable)
parse-anthropic-markdown <path_to_export.json>
```

Or run directly without installation:

```bash
python src/parse_anthropic_json.py <path_to_export.json>
python src/parse_anthropic_json_simple.py <path_to_export.json>
python src/parse_anthropic_markdown.py <path_to_export.json>
```

### Output Formats

| Format | Script | Description |
|--------|--------|-------------|
| Full JSON | `parse_anthropic_json.py` | Preserves all original data with metadata |
| Simple JSON | `parse_anthropic_json_simple.py` | Only sender, text, timestamp per message |
| Markdown | `parse_anthropic_markdown.py` | Human-readable with formatting |

### Output Location

Each parser creates a timestamped output directory next to the input file:

```
<path_to_export.json>_conversations_YYYYMMDD/
```

With subdirectories:
- `_simple/` for simplified JSON
- `_markdown/` for markdown files

## Development

### Running Tests

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

## Requirements

- Python 3.10+

## License

MIT License - see [LICENSE](LICENSE)
