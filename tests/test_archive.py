from argparse import Namespace
from pathlib import Path

from soundtrack_analyzer.archive import archive_dir
from soundtrack_analyzer.archive import main as archive_main


def create_tree(temp_path: Path) -> Path:
    root = temp_path / "root"
    root.mkdir(exist_ok=True, parents=True)

    for name in range(3):
        folder = root / str(name)
        folder.mkdir()

        (folder / "file1.mp4").touch()
        (folder / "file1.jpg").touch()

        (folder / "file2.mp4").touch()
        (folder / "file2.jpg").touch()

        (folder / "file3.mp4").touch()
        (folder / "file3.jpg").touch()

        (folder / "summary.csv").touch()

    return root


def test_archive_dir(tmp_path):
    root = create_tree(tmp_path)
    folder = root / "1"

    archive_dir(folder)

    assert not any(folder.glob("*.mp4"))
    assert (folder / "recordings.tgz").is_file()


def test_archive_superdir(tmp_path):
    root = create_tree(tmp_path)
    args = Namespace(directory=str(root), archive_all=False)

    archive_main(args)

    for name in range(2):
        folder = root / str(name)
        assert not any(folder.glob("*.mp4"))
        assert (folder / "recordings.tgz").is_file()

    folder = root / "2"
    assert len(list(folder.glob("*.mp4"))) == 3
    assert not (folder / "recordings.tgz").is_file()


def test_archive_superdir_all(tmp_path):
    root = create_tree(tmp_path)
    args = Namespace(directory=str(root), archive_all=True)

    archive_main(args)

    for name in range(3):
        folder = root / str(name)
        assert not any(folder.glob("*.mp4"))
        assert (folder / "recordings.tgz").is_file()
