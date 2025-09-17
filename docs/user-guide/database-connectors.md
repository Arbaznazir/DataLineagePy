# 🗄️ Database Connectors User Guide

DataLineagePy provides production-ready, enterprise-grade connectors for SQL databases—each with full lineage tracking for every query and operation.

---

## 🚀 Supported Connectors

- **MySQL**
- **PostgreSQL**
- **SQLite**
- (More coming soon: S3, Azure, GCP, Oracle, MongoDB, ...)

---

## 🔌 MySQL Connector Example

```python
from datalineagepy.connectors.database.mysql_connector import MySQLConnector
from datalineagepy.core import LineageTracker

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'password',
    'database': 'test_db'
}
tracker = LineageTracker()
conn = MySQLConnector(**db_config, lineage_tracker=tracker)
conn.execute_query('CREATE TABLE IF NOT EXISTS test_table (id INT PRIMARY KEY, name VARCHAR(50))')
conn.execute_query('INSERT INTO test_table (id, name) VALUES (%s, %s)', (1, 'Alice'))
result = conn.execute_query('SELECT * FROM test_table')
print('Query Result:', result)
conn.close()
```

---

## 🐘 PostgreSQL Connector Example

```python
from datalineagepy.connectors.database.postgresql_connector import PostgreSQLConnector
from datalineagepy.core import LineageTracker

db_config = {
    'host': 'localhost',
    'user': 'postgres',
    'password': 'password',
    'database': 'test_db'
}
tracker = LineageTracker()
conn = PostgreSQLConnector(**db_config, lineage_tracker=tracker)
conn.execute_query('CREATE TABLE IF NOT EXISTS test_table (id SERIAL PRIMARY KEY, name VARCHAR(50))')
conn.execute_query('INSERT INTO test_table (name) VALUES (%s)', ('Bob',))
result = conn.execute_query('SELECT * FROM test_table')
print('Query Result:', result)
conn.close()
```

---

## 🗃️ SQLite Connector Example

```python
from datalineagepy.connectors.database.sqlite_connector import SQLiteConnector
from datalineagepy.core import LineageTracker

tracker = LineageTracker()
conn = SQLiteConnector('test_sqlite.db', lineage_tracker=tracker)
conn.execute_query('CREATE TABLE IF NOT EXISTS test_table (id INTEGER PRIMARY KEY, name TEXT)')
conn.execute_query('INSERT INTO test_table (id, name) VALUES (?, ?)', (1, 'Charlie'))
result = conn.execute_query('SELECT * FROM test_table')
print('Query Result:', result)
conn.close()
```

---

## 🛡️ Best Practices & Troubleshooting

- Always pass a `LineageTracker` to your connector for full tracking
- Use parameterized queries to prevent SQL injection
- Close connections after use to free resources
- For advanced usage (transactions, batch operations), see the `examples/` directory
- If you encounter connection errors, check your database credentials and network settings

---

## 🏁 Next Steps

- [Concepts Guide](concepts.md)
- [DataFrame Wrapper Guide](dataframe-wrapper.md)
- [Full Documentation Index](index.md)
