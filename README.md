# Chat Export Parsers

Parse Anthropic and DeepSeek chat export JSON files into structured formats: full JSON, simplified JSON, or Markdown.

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

### CLI Commands (After Installation)

**Anthropic Exports:**
```bash
parse-anthropic-json <file>        # Full JSON output
parse-anthropic-json-simple <file> # Simplified JSON output
parse-anthropic-markdown <file>    # Markdown output
```

**DeepSeek Exports:**
```bash
parse-deepseek-json <file>        # Full JSON output
parse-deepseek-json-simple <file> # Simplified JSON output
parse-deepseek-markdown <file>    # Markdown output
```

### Direct Execution (Without Installation)

**Anthropic Exports:**
```bash
python src/parse_anthropic_json.py <file>
python src/parse_anthropic_json_simple.py <file>
python src/parse_anthropic_markdown.py <file>
```

**DeepSeek Exports:**
```bash
python src/parse_deepseek_json.py <file>
python src/parse_deepseek_json_simple.py <file>
python src/parse_deepseek_markdown.py <file>
```

### Output Formats

| Format | Description | Anthropic Script | DeepSeek Script |
|--------|-------------|------------------|-----------------|
| Full JSON | Preserves all original data with metadata | `parse_anthropic_json.py` | `parse_deepseek_json.py` |
| Simple JSON | Only sender, text, timestamp per message | `parse_anthropic_json_simple.py` | `parse_deepseek_json_simple.py` |
| Markdown | Human-readable with formatting | `parse_anthropic_markdown.py` | `parse_deepseek_markdown.py` |

### Output Location

Each parser creates a timestamped output directory:

**Anthropic:**
```
anthropic_{stem}_{YYYYMMDD_HHMMSS}/           # Full JSON
anthropic_{stem}_{YYYYMMDD_HHMMSS}_simple/    # Simple JSON
anthropic_{stem}_{YYYYMMDD_HHMMSS}_markdown/  # Markdown
```

**DeepSeek:**
```
deepseek_{stem}_{YYYYMMDD_HHMMSS}/           # Full JSON
deepseek_{stem}_{YYYYMMDD_HHMMSS}_simple/    # Simple JSON
deepseek_{stem}_{YYYYMMDD_HHMMSS}_markdown/  # Markdown
```

### Batch Processing

Process all `conversation*.json` files in the input directory using `config.json`:

```bash
# Anthropic (no arguments = use config.json)
python src/parse_anthropic_json.py
python src/parse_anthropic_json_simple.py
python src/parse_anthropic_markdown.py

# DeepSeek (no arguments = use config.json)
python src/parse_deepseek_json.py
python src/parse_deepseek_json_simple.py
python src/parse_deepseek_markdown.py
```

The parsers automatically detect the export format (Anthropic vs DeepSeek) and will skip files that don't match their expected format.

## Supported Export Formats

### Anthropic Exports

Anthropic exports have a flat `chat_messages` array structure:

```json
{
  "conversations": [
    {
      "id": "...",
      "name": "Conversation Name",
      "chat_messages": [
        {
          "sender": "human",
          "text": "message content",
          "created_at": "2024-01-01T00:00:00Z"
        }
      ]
    }
  ]
}
```

### DeepSeek Exports

DeepSeek exports use a tree-based `mapping` structure:

```json
[
  {
    "id": "uuid",
    "title": "Conversation Title",
    "mapping": {
      "root": {"children": ["1"]},
      "1": {
        "message": {
          "fragments": [
            {"type": "REQUEST", "content": "User message"}
          ],
          "inserted_at": "2026-01-01T00:00:00+08:00"
        }
      }
    }
  }
]
```

The parser traverses the tree and maps `REQUEST` → human, `RESPONSE` → assistant.

## Configuration

A `config.json` is auto-created on first run:

```json
{
  "input_dir": "./input",
  "output_dir": "./output",
  "providers": {
    "anthropic": {
      "output_prefix": "anthropic",
      "assistant_display_name": "Claude"
    },
    "deepseek": {
      "output_prefix": "deepseek",
      "assistant_display_name": "DeepSeek"
    }
  }
}
```

### Provider Configuration Options

- `output_prefix`: Prefix for output directory names (e.g., `anthropic_conversations_...`)
- `assistant_display_name`: Display name for assistant in markdown output (e.g., "🤖 Claude")

You can customize these to change branding or organize outputs differently.

### Default Directories

- Input directory: `./input/`
- Output directory: `./output/`
- Processed files moved to: `./input/done/`

## Project Structure

```
src/
  # Shared utilities
  common/                        # Shared across all parsers
    __init__.py
    config.py                    # Configuration with ProviderConfig
    file_manager.py              # File moving with conflict handling
    formatting.py                # sanitize_filename, format_timestamp
    markdown.py                  # Provider-aware MarkdownFormatter
    models.py                    # ConversationMetadata, MessageData

  # Anthropic parsers
  parse_anthropic_json.py        # Full JSON output
  parse_anthropic_json_simple.py # Simplified JSON output
  parse_anthropic_markdown.py    # Markdown output
  anthropic_parser/              # Anthropic-specific modules
    __init__.py
    message_utils.py             # Message sorting utilities
    validators.py                # Anthropic format detection

  # DeepSeek parsers
  parse_deepseek_json.py         # Full JSON output
  parse_deepseek_json_simple.py  # Simplified JSON output
  parse_deepseek_markdown.py     # Markdown output
  deepseek_parser/               # DeepSeek-specific modules
    __init__.py
    validators.py                # DeepSeek format detection
    message_utils.py             # Tree traversal & message extraction

input/                           # Default input directory
  done/                          # Processed files moved here
output/                          # Default output directory
config.json                      # Configuration file
```

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
