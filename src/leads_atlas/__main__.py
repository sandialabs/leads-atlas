import argparse
import sys
import tomllib
from pathlib import Path


def get_version() -> str:
    """Read version from pyproject.toml."""
    try:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject = tomllib.load(f)
        return pyproject["project"]["version"]
    except (FileNotFoundError, KeyError):
        return "unknown"


def build_parser() -> argparse.ArgumentParser:
    """Build and return the argument parser for LEADS Atlas."""
    parser = argparse.ArgumentParser(
        prog="leads-atlas",
        description="Load and process Vista data files",
        epilog="For more information, visit the documentation",
    )

    # Global options
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="enable verbose output"
    )

    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {get_version()}"
    )

    parser.add_argument(
        "-c", "--config", type=str, metavar="FILE", help="path to configuration file"
    )

    # Create subparsers for commands
    subparsers = parser.add_subparsers(
        dest="command", help="available commands", required=True
    )

    # Describe command
    describe_parser = subparsers.add_parser(
        "describe", help="describe data source or file"
    )
    describe_parser.add_argument(
        "source", type=str, help="source file or directory path to describe"
    )
    describe_parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["json", "yaml", "text"],
        default="text",
        help="output format (default: text)",
    )
    describe_parser.add_argument(
        "--detailed", action="store_true", help="show detailed information"
    )

    return parser


def handle_describe(args: argparse.Namespace) -> None:
    """Handle the describe command."""
    print(f"Describing: {args.source}")
    print(f"Format: {args.format}")
    print(f"Detailed: {args.detailed}")
    # TODO: Implement describe functionality
    pass


def process_args(args: argparse.Namespace) -> None:
    """Process parsed arguments and route to appropriate handler."""
    if args.command == "describe":
        handle_describe(args)


def main() -> int:
    """Main entry point for LEADS Atlas application."""
    parser = build_parser()
    args = parser.parse_args()
    process_args(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
