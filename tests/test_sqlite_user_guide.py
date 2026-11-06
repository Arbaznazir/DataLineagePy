"""The database user guide snippet must run against a local SQLite file."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datalineagepy.connectors.database.sqlite_connector import SQLiteConnector
from datalineagepy.core.tracker import LineageTracker


def test_sqlite_user_guide_round_trip(tmp_path):
    database_path = tmp_path / "test_sqlite.db"
    tracker = LineageTracker(name="user-guide")
    conn = SQLiteConnector(str(database_path), lineage_tracker=tracker)
    conn.execute_query(
        "CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)"
    )
    conn.execute_query(
        "INSERT INTO test_table (id, name) VALUES (?, ?)",
        (1, "Charlie"),
    )
    result = conn.execute_query("SELECT * FROM test_table")
    conn.close()

    assert list(result.columns) == ["id", "name"]
    assert len(result) == 1
    assert result._df.loc[0, "name"] == "Charlie"
    assert conn.lineage_tracker is tracker
    assert len(tracker.nodes) >= 1
    assert conn.connection is None
