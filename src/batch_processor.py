"""
Batch processor for Anthropic chat exports.

Processes all conversation*.json files from configured input directory,
outputs to configured output directory, and moves processed files to done/.

Usage:
    python src/batch_processor.py                    # Uses config.json
    python src/batch_processor.py --input ./exports  # Override input
    python src/batch_processor.py conversations.json # Process specific file
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from anthropic_parser.config import Config
from anthropic_parser.file_manager import move_to_done
from parse_anthropic_json import ConversationParser as Parser


def process_single_file(input_file: Path, output_dir: Path) -> dict:
    """
    Process a single conversation export file.

    Args:
        input_file: Path to conversations.json file
        output_dir: Directory for output files

    Returns:
        Processing summary
    """
    print(f"Loading: {input_file}")
    print(f"File size: {input_file.stat().st_size / (1024 * 1024):.1f} MB")

    with open(input_file, encoding="utf-8") as f:
        export_data = json.load(f)

    parser = Parser()
    conversations = parser.extract_conversations(export_data)
    print(f"Found {len(conversations)} conversations")

    file_ts = datetime.fromtimestamp(input_file.stat().st_ctime).strftime("%Y%m%d")
    base_output_dir = output_dir / f"{input_file.stem}_{file_ts}"
    base_output_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output directory: {base_output_dir}")

    processed = 0
    skipped = 0
    total_messages = 0

    for idx, conv in enumerate(conversations):
        try:
            metadata = parser.get_conversation_metadata(conv, idx)
            ts_prefix = _get_timestamp_prefix(metadata.latest_message_at or metadata.created_at)
            filename = f"{ts_prefix}{metadata.sanitized_filename}.json"
            output_path = _resolve_filename(base_output_dir, filename)

            conversation_data = {
                "metadata": {
                    "conversation_id": metadata.conversation_id,
                    "original_name": metadata.name,
                    "message_count": metadata.message_count,
                    "created_at": metadata.created_at,
                    "updated_at": metadata.updated_at,
                    "latest_message_at": metadata.latest_message_at,
                    "exported_at": datetime.now().isoformat(),
                },
                "conversation": conv,
            }

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)

            processed += 1
            total_messages += metadata.message_count

            if processed <= 5 or processed % 100 == 0:
                print(f"Saved: {output_path.name} ({metadata.message_count} messages)")

        except Exception as e:
            print(f"Warning: Failed to process conversation {idx}: {e}")
            skipped += 1

    summary_path = base_output_dir / "processing_summary.json"
    summary = {
        "source_file": str(input_file),
        "total_conversations": len(conversations),
        "processed_successfully": processed,
        "skipped_due_to_errors": skipped,
        "total_messages": total_messages,
        "output_directory": str(base_output_dir),
    }
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\nCompleted: {processed} conversations, {total_messages} messages")
    if skipped:
        print(f"Skipped: {skipped}")

    return summary


def _get_timestamp_prefix(timestamp: str | None) -> str:
    """Format timestamp as YYYYMMDD_HHMMSS_ prefix."""
    if not timestamp:
        return ""
    try:
        ts = timestamp.replace("Z", "+00:00")
        dt = datetime.fromisoformat(ts)
        return dt.strftime("%Y%m%d_%H%M%S_")
    except (ValueError, AttributeError):
        return ""


def _resolve_filename(directory: Path, filename: str) -> Path:
    """Handle filename conflicts by adding counter."""
    output_path = directory / filename
    if not output_path.exists():
        return output_path

    stem = output_path.stem
    suffix = output_path.suffix
    counter = 1
    while output_path.exists():
        output_path = directory / f"{stem}_{counter:02d}{suffix}"
        counter += 1
    return output_path


def process_all_files(config: Config) -> dict:
    """
    Process all conversation files in input directory.

    Args:
        config: Config instance

    Returns:
        Summary of batch processing results
    """
    config.ensure_directories()
    input_files = config.get_input_files()

    if not input_files:
        print(f"No conversation*.json files found in {config.input_dir}")
        return {"processed": 0, "failed": 0, "files": []}

    results = {"processed": 0, "failed": 0, "files": []}

    for input_file in input_files:
        print(f"\n{'=' * 60}")
        print(f"Processing: {input_file.name}")
        print(f"{'=' * 60}")

        try:
            summary = process_single_file(input_file, config.output_dir)

            move_to_done(input_file, config.done_dir)
            print(f"Moved to: {config.done_dir / input_file.name}")

            results["processed"] += 1
            results["files"].append(
                {
                    "input": str(input_file),
                    "output": summary["output_directory"],
                    "conversations": summary["total_conversations"],
                    "messages": summary["total_messages"],
                    "status": "success",
                }
            )

        except Exception as e:
            print(f"ERROR: Failed to process {input_file.name}: {e}")
            results["failed"] += 1
            results["files"].append({"input": str(input_file), "status": "failed", "error": str(e)})

    return results


def main():
    """CLI entry point for batch processor."""
    import argparse

    parser = argparse.ArgumentParser(description="Batch process Anthropic chat exports")
    parser.add_argument(
        "file", nargs="?", type=Path, help="Specific file to process (uses config if not specified)"
    )
    parser.add_argument("--input", "-i", type=Path, help="Input directory (overrides config)")
    parser.add_argument("--output", "-o", type=Path, help="Output directory (overrides config)")
    parser.add_argument("--config", "-c", type=Path, help="Path to config.json")

    args = parser.parse_args()

    # Load config
    config = Config.load(args.config)

    # Apply CLI overrides
    if args.input:
        config.input_dir = args.input
    if args.output:
        config.output_dir = args.output

    print(f"Input directory: {config.input_dir}")
    print(f"Output directory: {config.output_dir}")
    print(f"Done directory: {config.done_dir}")

    # Process specific file or all files from config
    if args.file:
        print(f"\nProcessing specific file: {args.file}")
        if not args.file.exists():
            print(f"Error: File not found: {args.file}")
            sys.exit(1)

        try:
            summary = process_single_file(args.file, config.output_dir)
            results = {
                "processed": 1,
                "failed": 0,
                "files": [
                    {
                        "input": str(args.file),
                        "output": summary["output_directory"],
                        "conversations": summary["total_conversations"],
                        "messages": summary["total_messages"],
                        "status": "success",
                    }
                ],
            }

            move_to_done(args.file, config.done_dir)
            print(f"Moved to: {config.done_dir / args.file.name}")

        except Exception as e:
            print(f"ERROR: {e}")
            results = {
                "processed": 0,
                "failed": 1,
                "files": [{"input": str(args.file), "status": "failed", "error": str(e)}],
            }
    else:
        results = process_all_files(config)

    print(f"\n{'=' * 60}")
    print("BATCH PROCESSING COMPLETE")
    print(f"{'=' * 60}")
    print(f"Files processed: {results['processed']}")
    print(f"Files failed: {results['failed']}")

    results_path = config.output_dir / "batch_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {results_path}")

    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
