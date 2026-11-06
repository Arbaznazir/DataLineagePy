"""Parquet file connector."""

import pandas as pd

from datalineagepy.connectors.file_base import FileConnector


class ParquetConnector(FileConnector):
    """Read a Parquet file and record it in the lineage graph."""

    file_format = "parquet"

    def _read_frame(self) -> pd.DataFrame:
        return pd.read_parquet(self.file_path)

    def read_file(self):
        return self._tracked_frame()
