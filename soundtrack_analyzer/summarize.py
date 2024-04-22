"""
Creates plots from aggregated summary logs.
"""
import calendar
from argparse import ArgumentParser, Namespace, RawDescriptionHelpFormatter
from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.dates import DateFormatter
from python_utils.timer import format_delta

from .utils import to_datetime


def plot_summary(df: pd.DataFrame, output_dir: Path, title: str):
    df = df.drop_duplicates()
    df = df.sort_values(by=["timestamp"])

    bark = df.bark_time.sum()
    total = df.total_time.sum()
    non_bark = total - bark

    groupped = df.groupby(by=df.timestamp.dt.floor("d"))
    groupped = groupped[["bark_time", "total_time"]]
    groupped = groupped.mean()
    groupped["bark_percentage"] = (
        groupped.bark_time / groupped.total_time
    ) * 100

    groupped.total_time = groupped.total_time.apply(to_datetime)
    groupped.bark_time = groupped.bark_time.apply(to_datetime)

    msg = (
        f"{title}\n"
        f"Barking: {format_delta(bark, digits=0)} of {format_delta(total, digits=0)}"
        f" ({((bark / total) * 100):.2f}%)"
    )

    y_formatter = DateFormatter("%H:%M:%S")
    x_formatter = DateFormatter("%d-%m-%y")

    axs = plt.subplots(2, 2, figsize=(10, 10))[1]

    # ----------------- Percentage pie -------------------------------

    axs[0][0].pie(
        [bark, non_bark], labels=["Barking", "Not barking"], autopct="%1.1f%%"
    )
    axs[0][0].title.set_text("Bark percentage")

    # --------------------- Bark percentage ----------------------
    axs[0][1].xaxis.set_major_formatter(x_formatter)

    axs[0][1].plot(
        groupped.index,
        groupped.bark_percentage,
        marker="X",
        linestyle="--",
        color="r",
    )
    axs[0][1].title.set_text("Bark percentage")
    axs[0][1].tick_params(axis="x", rotation=45)

    # --------------- Bark time --------------

    axs[1][0].xaxis.set_major_formatter(x_formatter)
    axs[1][0].yaxis.set_major_formatter(y_formatter)

    axs[1][0].plot(
        groupped.index,
        groupped.bark_time,
        marker="X",
        linestyle="--",
        color="r",
    )
    axs[1][0].title.set_text("Bark time")
    axs[1][0].tick_params(axis="x", rotation=45)

    # ------------------- Total time -----------------------------

    axs[1][1].xaxis.set_major_formatter(x_formatter)
    axs[1][1].yaxis.set_major_formatter(y_formatter)

    axs[1][1].plot(
        groupped.index,
        groupped.total_time,
        marker="X",
        linestyle="--",
        color="r",
    )
    axs[1][1].title.set_text("Total time")
    axs[1][1].tick_params(axis="x", rotation=45)

    plt.suptitle(msg, fontweight="bold", y=0.99)
    plt.tight_layout()
    plt.savefig(output_dir / "summary.png")


def get_summary(input_path: Path):
    parse_dates = {"parse_dates": ["timestamp"]}

    if input_path.is_file():  # monthly
        title = calendar.month_name[int(input_path.parent.name)]
        df = pd.read_csv(input_path, **parse_dates)
        plot_summary(df, output_dir=input_path.parent, title=title)
    elif input_path.is_dir():
        if (input_path / "summary.csv").is_file():  # monthly
            df = pd.read_csv(input_path / "summary.csv", **parse_dates)
            title = calendar.month_name[int(input_path.name)]
            plot_summary(df, output_dir=input_path, title=title)

        else:  # yearly
            frames = [
                pd.read_csv(file, **parse_dates)
                for file in input_path.rglob("*.csv")
                if file.name == "summary.csv"
            ]
            df = pd.concat(frames)
            plot_summary(df, output_dir=input_path, title=str(input_path.name))


def parse_args() -> Namespace:
    parser = ArgumentParser(
        description=__doc__,
        formatter_class=RawDescriptionHelpFormatter,
    )

    parser.add_argument("input_path", type=str)
    parser.add_argument(
        "--no-display",
        default=False,
        action="store_true",
        help="Suppress the display of interactive plot.",
    )
    return parser.parse_args()


def main(args: Namespace):
    input_path = Path(args.input_path)
    get_summary(input_path)

    if not args.no_display:
        plt.show()


def cli():
    main(parse_args())


if __name__ == "__main__":
    cli()
