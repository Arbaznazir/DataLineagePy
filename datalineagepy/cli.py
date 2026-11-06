"""Command-line entry point for datalineage."""

import argparse
import sys

from datalineagepy import __version__
from datalineagepy.core.dataframe_wrapper import read_csv
from datalineagepy.core.tracker import LineageTracker


def load_csv(csv_path, name=None):
    """Read a CSV file into a new tracker and return both."""
    tracker = LineageTracker(name=name or "datalineage")
    frame = read_csv(csv_path, name=name or "input", tracker=tracker)
    return tracker, frame


def build_parser():
    parser = argparse.ArgumentParser(
        prog="datalineage",
        description="Track column-level lineage for a CSV file.",
    )
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the installed DataLineagePy version.",
    )
    subparsers = parser.add_subparsers(dest="command")

    track = subparsers.add_parser(
        "track",
        help="Read a CSV file and write its lineage graph.",
    )
    track.add_argument("csv", help="CSV file to read.")
    track.add_argument(
        "--output",
        "-o",
        default="lineage.json",
        help="Lineage JSON path. Defaults to lineage.json.",
    )
    track.add_argument(
        "--html",
        help="Also write an HTML view of the graph to this path.",
    )
    track.add_argument("--name", help="Tracker name. Defaults to datalineage.")
    return parser


def run(argv=None) -> int:
    """Run the CLI and return a process status code."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if args.command != "track":
        parser.print_help()
        return 0

    try:
        tracker, frame = load_csv(args.csv, name=args.name)
    except FileNotFoundError as exc:
        print("CSV file not found: {}".format(exc.filename or args.csv), file=sys.stderr)
        return 1

    tracker.export_lineage(args.output)
    if args.html:
        tracker.visualize(args.html)
    print(
        "Tracked {} rows and {} columns into {} ({} nodes, {} edges).".format(
            len(frame),
            len(frame.columns),
            args.output,
            len(tracker.nodes),
            len(tracker.edges),
        )
    )
    return 0


def main(argv=None):
    """Console-script entry point."""
    sys.exit(run(argv))
