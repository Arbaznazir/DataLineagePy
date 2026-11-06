"""CSV file connector."""

import pandas as pd

from datalineagepy.connectors.file_base import FileConnector


class CSVConnector(FileConnector):
    """Read a CSV file and record it in the lineage graph."""

    file_format = "csv"

    def _read_frame(self) -> pd.DataFrame:
        return pd.read_csv(self.file_path)

    def read_file(self):
        return self._tracked_frame()
