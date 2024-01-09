import shutil
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path
from tempfile import TemporaryDirectory

from python_utils.archives import create_archive
from tqdm.contrib.concurrent import thread_map


def archive_dir(path: Path):
    """
    Moves all .mp4 files in path to a 'recordings.tgz' archive.
    """
    files = list(path.glob("*.mp4"))
    if not files:
        return

    with TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir) / "recordings"
        temp_dir.mkdir()

        for file in files:
            shutil.copy(file, temp_dir / file.name)
            file.unlink()

        create_archive(str(temp_dir))

        archive = temp_dir.parent / "recordings.tgz"
        assert archive.is_file()

        shutil.copy(archive, path / archive.name)


def get_subfolders(path: Path, archive_all: bool = False) -> list[Path]:
    """
    Get list of subfolders

    Parameters
    ----------
    archive_all : bool = False
        Return a list of all subdirectories to archive. If false,
        skip the newest one
    """

    def sorting_key(file: Path) -> int:
        return int(file.name)

    subfolders = sorted(
        (folder for folder in path.glob("*") if folder.is_dir()),
        key=sorting_key,
    )

    if not archive_all:
        del subfolders[-1]

    return subfolders


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument("directory")
    parser.add_argument(
        "--archive-all",
        default=False,
        action="store_true",
        help="Archive all subdirectories. "
        "(Defalut behaviour is to leave the newest unarchived)",
    )

    return parser.parse_args()


def main(args: Namespace):
    path = Path(args.directory)
    if path.is_dir():
        is_month_dir = any(path.glob("*.mp4"))

        if is_month_dir:
            archive_dir(path)
        else:  # year input
            subfolders = get_subfolders(path, args.archive_all)
            thread_map(archive_dir, subfolders)
    else:
        raise ValueError(f"Path: {path} is not a valid target.")


def cli():
    main(parse_args())


if __name__ == "__main__":
    cli()
