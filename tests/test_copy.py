from datetime import datetime

from soundtrack_analyzer.batch_copy import exists, get_filelist


def test_exist_nofile(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("sample text")

    dest = tmp_path / "destination.txt"

    assert exists(source, dest) is False


def test_exist(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("sample text")

    dest = tmp_path / "destination.txt"
    dest.write_text("sample text")

    assert exists(source, dest) is True


def test_exist_size_diff(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("sample text")

    dest = tmp_path / "destination.txt"

    assert exists(source, dest) is False


def test_filename_skip(tmp_path):
    root = tmp_path / "root"
    root.mkdir(exist_ok=True, parents=True)

    dest = tmp_path / "dest"
    dest.mkdir(exist_ok=True, parents=True)

    cutoff_date = datetime(year=2023, month=2, day=16)

    valid_name = "20231215_093653_tp00033.mp4"
    (root / valid_name).touch()
    (root / "xxxxxxxx_xxxxxx_tp00033.mp4").touch()
    (root / "20221215_093653_tp00033.mp4").touch()
    (root / "20230215_093653_tp00033.mp4").touch()

    files = get_filelist(root, dest, cutoff_date)

    assert len(files) == 1
    assert files[0].name == valid_name
