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

Each parser creates a timestamped output directory in the same location as the input file (or in the configured output directory):

```
anthropic_{stem}_{YYYYMMDD_HHMMSS}/           # Full JSON
anthropic_{stem}_{YYYYMMDD_HHMMSS}_simple/    # Simple JSON
anthropic_{stem}_{YYYYMMDD_HHMMSS}_markdown/  # Markdown
```

For example, processing `conversations.json` creates:
- `anthropic_conversations_20260305_160057/`
- `anthropic_conversations_20260305_160057_simple/`
- `anthropic_conversations_20260305_160057_markdown/`

The timestamp is extracted from the export data (latest `updated_at` field) with a fallback to file creation time.

### Batch Processing

Process all `conversation*.json` files in the input directory using `config.json`:

```bash
# Without arguments, uses config.json for input/output paths
python src/parse_anthropic_json.py
python src/parse_anthropic_json_simple.py
python src/parse_anthropic_markdown.py
```

A `config.json` is auto-created on first run with defaults:
- Input: `./input/`
- Output: `./output/`
- Processed files moved to: `./input/done/`

For `conversations.json`, the output directories would be:
- `anthropic_conversations_20260305_160057/` (full JSON)
- `anthropic_conversations_20260305_160057_simple/` (simple JSON)
- `anthropic_conversations_20260305_160057_markdown/` (markdown)

### Batch Processing

Process all `conversation*.json` files in the input directory using `config.json`:

```bash
# Without arguments, processes all files in input directory
python src/parse_anthropic_json.py
python src/parse_anthropic_json_simple.py
python src/parse_anthropic_markdown.py
```

A `config.json` file is auto-created on first run with defaults:
- Input directory: `./input/`
- Output directory: `./output/`
- Processed files moved to: `./input/done/`

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_parsers.py

# Run single test with verbose output
pytest tests/test_parsers.py::TestFullJsonParser::test_sanitize_filename_special_chars -v

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
