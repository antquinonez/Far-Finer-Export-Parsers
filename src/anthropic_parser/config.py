"""
Configuration management for Anthropic chat export parser.

Provides simple configuration for input/output directories.
Config file is auto-created with defaults if not found.
"""

import json
from pathlib import Path


class Config:
    """
    Configuration for input/output directories.

    Config file format (config.json):
    {
        "input_dir": "./input",
        "output_dir": "./output"
    }

    The done directory is always {input_dir}/done
    """

    def __init__(self, input_dir: Path, output_dir: Path):
        """
        Initialize configuration.

        Args:
            input_dir: Directory containing conversation*.json files
            output_dir: Directory for processed output files
        """
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.done_dir = input_dir / "done"

    @classmethod
    def load(cls, config_path: Path | None = None) -> "Config":
        """
        Load configuration from file or create defaults.

        Args:
            config_path: Path to config.json. If None, uses project root.

        Returns:
            Config instance
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config.json"

        if config_path.exists():
            return cls._from_file(config_path)

        return cls._create_defaults(config_path)

    @classmethod
    def _from_file(cls, config_path: Path) -> "Config":
        """Load configuration from JSON file."""
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)

        # Resolve paths relative to config file location
        base_dir = config_path.parent
        input_dir = (base_dir / data.get("input_dir", "./input")).resolve()
        output_dir = (base_dir / data.get("output_dir", "./output")).resolve()

        return cls(input_dir=input_dir, output_dir=output_dir)

    @classmethod
    def _create_defaults(cls, config_path: Path) -> "Config":
        """Create default configuration and save to file."""
        project_root = config_path.parent

        config = cls(
            input_dir=project_root / "input",
            output_dir=project_root / "output",
        )

        config.save(config_path)
        print(f"Created config file: {config_path}")
        return config

    def save(self, config_path: Path) -> None:
        """Save configuration to JSON file with relative paths."""
        base_dir = config_path.parent

        # Store paths relative to config file
        try:
            input_rel = self.input_dir.relative_to(base_dir)
            input_str = f"./{input_rel}"
        except ValueError:
            input_str = str(self.input_dir)

        try:
            output_rel = self.output_dir.relative_to(base_dir)
            output_str = f"./{output_rel}"
        except ValueError:
            output_str = str(self.output_dir)

        data = {
            "input_dir": input_str,
            "output_dir": output_str,
        }

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def ensure_directories(self) -> None:
        """Create all configured directories if they don't exist."""
        self.input_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.done_dir.mkdir(parents=True, exist_ok=True)

    def get_input_files(self) -> list[Path]:
        """
        Get all conversation*.json files in input directory.

        Returns:
            List of Path objects for matching files, sorted by name
        """
        if not self.input_dir.exists():
            return []

        return sorted(self.input_dir.glob("conversation*.json"))


def main():
    """CLI entry point to create/show config."""
    import argparse

    parser = argparse.ArgumentParser(description="Manage configuration")
    parser.add_argument("--show", "-s", action="store_true", help="Show current config")
    parser.add_argument("--create-dirs", action="store_true", help="Create configured directories")

    args = parser.parse_args()

    config = Config.load()

    print(f"Input directory: {config.input_dir}")
    print(f"Output directory: {config.output_dir}")
    print(f"Done directory: {config.done_dir}")

    if args.create_dirs:
        config.ensure_directories()
        print("Directories created.")


if __name__ == "__main__":
    main()
