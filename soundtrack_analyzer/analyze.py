"""
Analyze the soundtrack of a video.

Extracts the sound signal, patches it and analysis the volume values 
summarizing how much of the sound samples are considered high.

Produces both raw value and plot summary.
"""

import subprocess
import wave
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from datetime import datetime
from itertools import repeat
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import NamedTuple, Optional

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import DateFormatter
from python_utils.timer import format_delta, timer
from tqdm.contrib.concurrent import process_map

from .utils import extract_timestamp, to_datetime, write_csv


def read_sound_file(
    file: str, samples: int | float = -1
) -> tuple[np.ndarray, np.ndarray]:
    """Load .wav file"""

    signal_wave = wave.open(file, "r")
    if signal_wave.getnchannels() == 2:
        raise ValueError("Only mono files supported.")

    if isinstance(samples, float):
        if samples.is_integer():
            samples = int(samples)
        else:
            samples = int(signal_wave.getnframes() * samples)

    signal = np.frombuffer(signal_wave.readframes(samples), dtype=np.int16)
    signal = np.abs(signal)

    frame_rate = signal_wave.getframerate()
    time = np.linspace(0, len(signal) / frame_rate, num=len(signal))

    return time, signal


def extract_sound(input_file: str, output_file: str, verbose: bool = False):
    """
    Extract soundtrack from .mp4 file
    """
    if verbose:
        kwargs = {}
    else:
        kwargs = {"stdout": subprocess.DEVNULL, "stderr": subprocess.STDOUT}

    subprocess.run(
        ["ffmpeg", "-i", str(input_file), str(output_file)],
        check=True,
        **kwargs,
    )


def plot(
    time: list,
    signal: list,
    cutoff: int,
    message: str,
    undersample: Optional[int] = None,
):
    """
    Create summary plot

    Parameters
    ----------
    undersample : Optional[int]
        Undersample the signal to reduce computational complexity.

    """

    formatter = DateFormatter("%H:%M:%S")
    fig, (ax1, ax2) = plt.subplots(2, figsize=(15, 6))
    plt.suptitle(message, fontweight="bold", y=0.99)

    if undersample:
        signal = signal[::undersample]
        time = time[::undersample]

    half = len(signal) // 2
    time = to_datetime(time)

    ax1.plot(time[:half], signal[:half])
    ax1.axhline(y=cutoff, color="r", linestyle="--")
    ax1.xaxis.set_major_formatter(formatter)
    ax1.set_yticks([])

    ax2.plot(time[half:], signal[half:])
    ax2.axhline(y=cutoff, color="r", linestyle="--")
    ax2.xaxis.set_major_formatter(formatter)
    ax2.set_yticks([])

    fig.supxlabel("Time")
    fig.supylabel("Volume")

    plt.tight_layout()


def patch_signal(signal: list, cutoff: int, max_gap: int = 0) -> np.ndarray:
    """
    Patch given signal: if at most 'max_gap' values between samples are below
    cutoff value - fill them with 'cutoff + 1'
    """

    if signal[0] > cutoff:
        mask = signal > cutoff
        below = False
    else:
        mask = signal <= cutoff
        below = True

    index = 0
    gaps = []

    result = np.diff(
        np.where(np.concatenate(([mask[0]], mask[:-1] != mask[1:], [True])))[0]
    )
    for item in result:
        if below is True and item <= max_gap:
            gaps += list(range(index, index + item))

        index += item
        below = not below

    signal[gaps] = cutoff + 1

    return signal


def get_bark_fraction(signal: list, cutoff: int, max_gap: float = 0) -> float:
    """
    Patch the signal and calculate bark fraction.

    Parameters
    ----------
    max_gap : float
        Maximal distance between samples required to patch the signal.
        Should be provided in SECONDS, not number of samples.
    """

    if max_gap <= 0:
        return np.count_nonzero(signal > cutoff) / len(signal)

    max_gap /= 0.000125  # convert seconds gap to n-samples gap
    signal = patch_signal(signal.copy(), cutoff, max_gap)
    return np.count_nonzero(signal > cutoff) / len(signal)


class AnalysisResult(NamedTuple):
    timestamp: datetime
    total_time: float
    bark_time: float


def analyze_file(
    input_file: str,
    cutoff: int = 5_000,
    max_gap: float = 0,
    undersample: Optional[int] = None,
    output_file: Optional[str] = None,
) -> AnalysisResult:
    """
    Perform full analysis of file (.mp4 or .wav).

    Extracts signal, patches it, produces AnalysisResult and a summary plot.

    Parameters
    ----------
    output_file : Optional[str]
        Provide a path to save summary plot to a file. Provide 'auto' for
        automatic filename generation.

    undersample : Optional[int]
        Undersample the signal to reduce computational complexity.
        Parameter applies only to plotting.
    """
    if input_file.endswith(".wav"):
        time, signal = read_sound_file(input_file)
    else:
        with TemporaryDirectory() as tempdir:
            tempfile = Path(tempdir) / "sound.wav"
            extract_sound(input_file, str(tempfile))
            time, signal = read_sound_file(str(tempfile))

    total_time = time[-1]
    bark_fraction = get_bark_fraction(signal, cutoff, max_gap)
    bark_time = total_time * bark_fraction

    message = (
        f"{extract_timestamp(input_file)}\n\n"
        f"Barking: {format_delta(bark_time, digits=0)} of {format_delta(total_time, digits=0)}"
        f" ({np.round(bark_fraction * 100, 2)}%)"
    )

    plot(
        time=time,
        signal=signal,
        cutoff=cutoff,
        message=message,
        undersample=undersample,
    )

    if output_file:
        if output_file == "auto":
            output_file = Path(input_file).with_suffix(".png")

        plt.savefig(output_file)

    return AnalysisResult(extract_timestamp(input_file), total_time, bark_time)


def get_filelist(input_path: Path, rewrite: bool = False) -> list[str]:
    """
    Generate file list for directory input.

    Skip processed files unless 'rewrite' argument is set.
    """

    if rewrite:
        return [str(file) for file in input_path.glob("*.mp4")]

    result = []
    for file in input_path.glob("*.mp4"):
        if not file.with_suffix(".png").is_file():
            result.append(str(file))

    return result


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input_path", type=str, help="Input file or a directory"
    )
    parser.add_argument(
        "-c",
        "--cutoff",
        type=int,
        default=5_000,
        help="Volume value considered as high",
    )
    parser.add_argument(
        "-g",
        "--max-gap",
        type=float,
        default=5,
        help="Maximal gap (in seconds) between sound samples "
        "for them to be considered continual",
    )
    parser.add_argument(
        "-r",
        "--rewrite",
        default=False,
        action="store_true",
        help="Rewire already analyzed files (directory mode only)",
    )
    parser.add_argument(
        "-u",
        "--undersample",
        type=int,
        default=10,
        help="Undersample the signal - take every n-th value"
        " (USED ONLY FOR PLOTTING)",
    )
    parser.add_argument(
        "--no-display",
        default=False,
        action="store_true",
        help="Suppress the display of interactive plot "
        "(Only for file input)",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        help="Number of processes for concurrent format conversion",
    )

    return parser.parse_args()


def main(args: Namespace):
    input_path = Path(args.input_path)

    if input_path.is_file():
        with timer("Analysis time"):
            result = analyze_file(
                input_file=args.input_path,
                cutoff=args.cutoff,
                max_gap=args.max_gap,
                undersample=args.undersample,
                output_file="auto",
            )
        summary_file = input_path.parent / "summary.csv"
        write_csv([result], summary_file)
        if not args.no_display:
            plt.show()

    elif input_path.is_dir():
        input_files = get_filelist(input_path, args.rewrite)

        results = process_map(
            analyze_file,
            input_files,
            repeat(args.cutoff),
            repeat(args.max_gap),
            repeat(args.undersample),
            repeat("auto"),
            max_workers=args.n_jobs,
            desc="Analyzing",
        )
        summary_file = input_path / "summary.csv"
        write_csv(results, summary_file, overwrite=args.rewrite)
    else:
        raise FileNotFoundError(f"Path {input_path} does not exist.")


def cli():
    main(parse_args())


if __name__ == "__main__":
    cli()
