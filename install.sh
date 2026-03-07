#!/bin/bash
# Installation script for Anthropic Chat Parser
# Creates a virtual environment and installs the package in editable mode

set -e

VENV_DIR=".venv"
PYTHON_CMD="${PYTHON_CMD:-python3}"

echo "=== Anthropic Chat Parser Installation ==="
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Found Python $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ -d "$VENV_DIR" ]; then
    echo ""
    echo "Virtual environment '$VENV_DIR' already exists."
    read -p "Recreate it? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing virtual environment."
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo "Virtual environment created."
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip --quiet

# Install package in editable mode with dev dependencies
echo ""
echo "Installing package in editable mode with dev dependencies..."
pip install -e ".[dev]" --quiet

echo ""
echo "=== Installation Complete ==="
echo ""
echo "To activate the virtual environment, run:"
echo "    source $VENV_DIR/bin/activate"
echo ""
echo "Available commands after activation:"
echo "    parse-anthropic-json <file>        # Full JSON output"
echo "    parse-anthropic-json-simple <file> # Simplified JSON output"
echo "    parse-anthropic-markdown <file>    # Markdown output"
echo ""
echo "Or run directly:"
echo "    python src/parse_anthropic_json.py <file>"
echo ""
