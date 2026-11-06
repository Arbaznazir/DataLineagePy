"""Command-line entry point for datalineage-viz."""

import argparse
import sys

from datalineagepy.cli import load_csv


def build_parser():
    parser = argparse.ArgumentParser(
        prog="datalineage-viz",
        description="Write an HTML lineage view for a CSV file.",
    )
    parser.add_argument("csv", help="CSV file to read.")
    parser.add_argument(
        "--output",
        "-o",
        default="lineage.html",
        help="HTML output path. Defaults to lineage.html.",
    )
    parser.add_argument("--name", help="Tracker name. Defaults to datalineage.")
    return parser


def run(argv=None) -> int:
    """Run the visualization CLI and return a process status code."""
    args = build_parser().parse_args(argv)
    try:
        tracker, _frame = load_csv(args.csv, name=args.name)
    except FileNotFoundError as exc:
        print("CSV file not found: {}".format(exc.filename or args.csv), file=sys.stderr)
        return 1
    written = tracker.visualize(args.output)
    print("Wrote {}".format(written))
    return 0


def main(argv=None):
    """Console-script entry point."""
    sys.exit(run(argv))
