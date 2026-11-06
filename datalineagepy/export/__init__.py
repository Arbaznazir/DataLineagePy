"""Export a CSV file's lineage graph."""

from datalineagepy.cli import load_csv

__all__ = ["export_lineage_file"]


def export_lineage_file(csv_path, output_file, export_format="json", name=None):
    """Read a CSV file and write its lineage graph."""
    tracker, frame = load_csv(csv_path, name=name)
    tracker.export_lineage(output_file, format=export_format)
    return tracker, frame
