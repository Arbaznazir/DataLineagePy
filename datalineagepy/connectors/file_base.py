"""File connectors that record a lineage node for each read."""

from pathlib import Path

import pandas as pd

from datalineagepy.core.dataframe_wrapper import LineageDataFrame
from datalineagepy.core.tracker import LineageTracker


class FileConnector:
    """Base class for reading a local file into a LineageDataFrame."""

    file_format = "file"

    def __init__(self, file_path, tracker=None):
        self.file_path = Path(file_path)
        self.tracker = tracker or LineageTracker.get_global_instance()

    def read_file(self) -> LineageDataFrame:
        """Read the file and return a tracked frame."""
        raise NotImplementedError

    def _read_frame(self) -> pd.DataFrame:
        raise NotImplementedError

    def _tracked_frame(self) -> LineageDataFrame:
        frame = self._read_frame()
        node = self.tracker.create_node(
            "file",
            str(self.file_path),
            {
                "file_path": str(self.file_path),
                "file_format": self.file_format,
                "operation": "read_file",
            },
        )
        node.set_schema({column: str(frame[column].dtype) for column in frame.columns})
        return LineageDataFrame(
            frame,
            name=self.file_path.stem or self.file_format,
            tracker=self.tracker,
            source_node=node,
        )
