"""Command-line entry point for datalineage-export."""

import argparse
import sys

from datalineagepy.export import export_lineage_file


def build_parser():
    parser = argparse.ArgumentParser(
        prog="datalineage-export",
        description="Export lineage for a CSV file as JSON or DOT.",
    )
    parser.add_argument("csv", help="CSV file to read.")
    parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Destination path for the lineage graph.",
    )
    parser.add_argument(
        "--format",
        choices=("json", "dot"),
        default="json",
        help="Graph format. Defaults to json.",
    )
    parser.add_argument("--name", help="Tracker name. Defaults to datalineage.")
    return parser


def run(argv=None) -> int:
    """Run the export CLI and return a process status code."""
    args = build_parser().parse_args(argv)
    try:
        tracker, _frame = export_lineage_file(
            args.csv,
            args.output,
            export_format=args.format,
            name=args.name,
        )
    except FileNotFoundError as exc:
        print("CSV file not found: {}".format(exc.filename or args.csv), file=sys.stderr)
        return 1
    print(
        "Wrote {} ({} nodes, {} edges).".format(
            args.output, len(tracker.nodes), len(tracker.edges)
        )
    )
    return 0


def main(argv=None):
    """Console-script entry point."""
    sys.exit(run(argv))
