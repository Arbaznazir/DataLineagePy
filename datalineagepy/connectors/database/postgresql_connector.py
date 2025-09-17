import psycopg2
from datalineagepy.core import LineageTracker


class PostgreSQLConnector:
    def __init__(self, host, user, password, database, lineage_tracker=None):
        self.conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            dbname=database
        )
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
            operation_type='postgresql_query',
            inputs=[],
            outputs=[],
            metadata={'query': query}
        )
        return result

    def close(self):
        self.cursor.close()
        self.conn.close()
