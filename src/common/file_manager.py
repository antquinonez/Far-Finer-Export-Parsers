"""
File management utilities for processed conversation files.
"""

import shutil
from datetime import datetime
from pathlib import Path


def move_to_done(source_file: Path, done_dir: Path) -> Path:
    """
    Move a processed file to the done directory with conflict handling.

    Naming convention for conflicts:
    1. If file exists in done, use creation date: conversation_20250407.json
    2. If still conflicts, add suffix: conversation_20250407_1.json

    Args:
        source_file: Path to the file to move
        done_dir: Path to the done directory

    Returns:
        Path to the moved file in done directory
    """
    done_dir.mkdir(parents=True, exist_ok=True)

    target_name = _resolve_target_name(source_file, done_dir)
    target_path = done_dir / target_name

    shutil.move(str(source_file), str(target_path))
    return target_path


def _resolve_target_name(source_file: Path, done_dir: Path) -> str:
    """
    Resolve the target filename, handling conflicts.

    Args:
        source_file: Original file path
        done_dir: Destination directory

    Returns:
        Resolved filename
    """
    original_name = source_file.name
    target_path = done_dir / original_name

    if not target_path.exists():
        return original_name

    date_based_name = _create_date_based_name(source_file)
    target_path = done_dir / date_based_name

    if not target_path.exists():
        return date_based_name

    return _create_numbered_name(date_based_name, done_dir)


def _create_date_based_name(source_file: Path) -> str:
    """
    Create filename using file's creation date.

    Args:
        source_file: Path to source file

    Returns:
        Filename with date prefix (e.g., conversation_20250407.json)
    """
    stat = source_file.stat()
    creation_date = datetime.fromtimestamp(stat.st_ctime).strftime("%Y%m%d")

    stem = source_file.stem
    suffix = source_file.suffix

    return f"{stem}_{creation_date}{suffix}"


def _create_numbered_name(base_name: str, done_dir: Path) -> str:
    """
    Create numbered filename to resolve conflicts.

    Args:
        base_name: Base filename to number
        done_dir: Destination directory

    Returns:
        Numbered filename (e.g., conversation_20250407_1.json)
    """
    stem = Path(base_name).stem
    suffix = Path(base_name).suffix

    counter = 1
    while True:
        numbered_name = f"{stem}_{counter}{suffix}"
        if not (done_dir / numbered_name).exists():
            return numbered_name
        counter += 1
