"""
Utility script - copies all mp4 files from source to destination.
All files that are already in the destination are skipped
(both filename and size must match).

WARNING: Script written for specific filenames format (TAPO cameras recordings)
"""

import shutil
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from datetime import datetime
from itertools import repeat
from pathlib import Path

from tqdm.auto import tqdm
from tqdm.contrib.concurrent import thread_map


def copy_file(source_file: Path, destination: Path):
    shutil.copy(source_file, destination / source_file.name)


def process_file(file: Path, destination_root: Path):
    filename = "_".join(file.name.split("_")[:2])
    date = datetime.strptime(filename, "%Y%m%d_%H%M%S")

    destination_dir = destination_root / str(date.year) / str(date.month)
    if not destination_dir.is_dir():
        destination_dir.mkdir(parents=True, exist_ok=True)

    copy_file(file, destination_dir)


def exists(
    source: Path, destination: Path, max_size_diff: float = 0.05
) -> bool:
    """
    Check if target file exists - both name and size must match.
    (size difference has a flexibility parameter.)
    """
    if not destination.is_file():
        return False

    source_size = source.stat().st_size
    dest_size = destination.stat().st_size

    # check the difference in size
    diff = abs(dest_size - source_size)
    if (diff / source_size) > max_size_diff:
        tqdm.write(f"File: {destination} - size missmatch, copying")
        return False

    return True


def get_filelist(
    source_dir: Path, destination_root: Path, cutoff_date: datetime
) -> list[Path]:
    result = []

    for file in source_dir.glob("*.mp4"):
        if "xx" in str(file):
            continue

        filename = "_".join(file.name.split("_")[:2])
        date = datetime.strptime(filename, "%Y%m%d_%H%M%S")

        if date < cutoff_date:
            continue

        destination_dir = destination_root / str(date.year) / str(date.month)
        destination = destination_dir / file.name

        if not exists(file, destination):
            result.append(file)

    return result


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument("source_dir")
    parser.add_argument("destination_root")

    return parser.parse_args()


def main(args: Namespace):
    source_dir = Path(args.source_dir)
    destination_root = Path(args.destination_root)

    cutoff_date = datetime(year=2023, month=3, day=1)
    files = get_filelist(source_dir, destination_root, cutoff_date)

    thread_map(process_file, files, repeat(destination_root), desc="Copying")


def cli():
    main(parse_args())


if __name__ == "__main__":
    cli()
