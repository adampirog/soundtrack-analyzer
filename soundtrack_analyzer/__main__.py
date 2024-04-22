"""
A 'combo' script which:

    1. Copies the file from card to the archive
    2. Analysis the latest month
    3. Summarizes the latest month
"""

import subprocess
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path


def copy_files(source: str, destination: str) -> None:
    subprocess.run(
        ["soundtrack-analyzer-copy", source, destination], check=True
    )


def analyze_files(directory: str) -> None:
    subprocess.run(["soundtrack-analyzer-analyze", directory], check=True)


def summarize_files(directory: str) -> None:
    subprocess.run(["soundtrack-analyzer-summarize", directory], check=True)


def get_latest_month(directory: str) -> str:
    """
    Get the directory holding the recording from the latest month
    """

    def month(path: Path) -> int:
        try:
            result = int(path.name)
        except ValueError:
            return -1
        return result

    directory = Path(directory)
    result = max(
        (folder for folder in directory.glob("*") if folder.is_dir()),
        key=month,
    )

    if month(result) > 12:
        # year directory
        result = max(
            (folder for folder in result.glob("*") if folder.is_dir()),
            key=month,
        )

    return str(result)


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument("source", help="Path to raw recordings directory")
    parser.add_argument("destination", help="Path to the archive directory")

    return parser.parse_args()


def main(args: Namespace):
    copy_files(args.source, args.destination)

    latest_month = get_latest_month(args.destination)
    analyze_files(latest_month)
    summarize_files(latest_month)


def cli():
    main(parse_args())


if __name__ == "__main__":
    cli()
