"""
Utility functions for sound analyzer. When run as a script will
generate timestamps of given length and save them as a resource file.
"""
import csv
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from tqdm.auto import tqdm


def extract_timestamp(file_path: str) -> datetime:
    """
    Extract timestamp from TAPO file name.
    """
    filename = Path(file_path).name
    filename = "_".join(filename.split("_")[:2])
    result = datetime.strptime(filename, "%Y%m%d_%H%M%S")

    return result


BASE_DATE = datetime.strptime("2000-01-01 00:00:00.00", "%Y-%m-%d %H:%M:%S.%f")


@np.vectorize
def to_datetime(seconds: float) -> datetime:
    """Convert seconds to datetime"""
    return BASE_DATE + timedelta(seconds=seconds)


def save_time(time: list[datetime], file: str):
    with open(file, "wt", encoding="utf-8") as handle:
        for item in tqdm(time, desc="Saving"):
            line = item.strftime("%Y-%m-%d %H:%M:%S.%f") + "\n"
            handle.write(line)


def load_time(file: str) -> list:
    with open(file, encoding="utf-8") as handle:
        result = [
            datetime.strptime(line.strip(), "%Y-%m-%d %H:%M:%S.%f")
            for line in handle
        ]
    return result


def write_csv(rows: list, file: Path, overwrite: bool = False) -> None:
    if file.is_file() and not overwrite:
        mode = "a"
    else:
        header = ["timestamp", "total_time", "bark_time"]
        rows.insert(0, header)
        mode = "w"

    with file.open(mode, encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument("hours", type=float)
    parser.add_argument("output_file", type=str)

    return parser.parse_args()


def main(args: Namespace):
    start = 0
    stop = args.hours * 60**2
    step = 0.000125

    values = np.arange(start, stop, step)
    result = to_datetime(values)

    save_time(result, args.output_file)


if __name__ == "__main__":
    main(parse_args())
