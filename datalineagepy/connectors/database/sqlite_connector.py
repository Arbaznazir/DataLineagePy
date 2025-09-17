import sqlite3
from datalineagepy.core import LineageTracker


class SQLiteConnector:
    def __init__(self, db_path, lineage_tracker=None):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.lineage_tracker = lineage_tracker or LineageTracker()

    def execute_query(self, query, params=None):
        self.cursor.execute(query, params or ())
        if query.strip().lower().startswith('select'):
            result = self.cursor.fetchall()
        else:
            self.conn.commit()
            result = self.cursor.rowcount
        self.lineage_tracker.track_operation(
            operation_type='sqlite_query',
            inputs=[],
            outputs=[],
            metadata={'query': query}
        )
        return result

    def close(self):
        self.cursor.close()
        self.conn.close()
