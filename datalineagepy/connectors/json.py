"""JSON file connector."""

import pandas as pd

from datalineagepy.connectors.file_base import FileConnector


class JSONConnector(FileConnector):
    """Read a JSON file of records and record it in the lineage graph."""

    file_format = "json"

    def _read_frame(self) -> pd.DataFrame:
        return pd.read_json(self.file_path)

    def read_file(self):
        return self._tracked_frame()
