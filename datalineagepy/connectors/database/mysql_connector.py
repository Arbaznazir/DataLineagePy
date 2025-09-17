import mysql.connector
from datalineagepy.core import LineageTracker


class MySQLConnector:
    def __init__(self, host, user, password, database, lineage_tracker=None):
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor(dictionary=True)
        self.lineage_tracker = lineage_tracker or LineageTracker()

    def execute_query(self, query, params=None):
        self.cursor.execute(query, params or ())
        if query.strip().lower().startswith('select'):
            result = self.cursor.fetchall()
        else:
            self.conn.commit()
            result = self.cursor.rowcount
        self.lineage_tracker.track_operation(
            operation_type='mysql_query',
            inputs=[],  # Could be enhanced to track actual input nodes
            outputs=[],
            metadata={'query': query}
        )
        return result

    def close(self):
        self.cursor.close()
        self.conn.close()
