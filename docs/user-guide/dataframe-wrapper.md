# 🧮 DataFrame Wrapper User Guide

The `LineageDataFrame` (DataFrame Wrapper) is the heart of DataLineagePy. It transparently wraps your pandas DataFrames, automatically tracking every operation for full lineage and auditability—while remaining 100% pandas-compatible.

---

## ✨ Why Use LineageDataFrame?

- **Zero code changes**: Use your DataFrames as usual
- **Automatic lineage**: Every transformation, filter, join, and aggregation is tracked
- **Rich metadata**: Attach source, owner, schema, and more
- **Seamless integration**: Works with all pandas methods and DataLineagePy features

---

## 🚀 Getting Started

```python
from datalineagepy import LineageTracker, LineageDataFrame
import pandas as pd

tracker = LineageTracker(name="my_pipeline")
df = pd.DataFrame({'name': ['Alice', 'Bob'], 'age': [25, 30]})
ldf = LineageDataFrame(df, name="users", tracker=tracker)
```

---

## 🛠️ Core Operations

### Column Selection

```python
# Single column
name_col = ldf['name']
# Multiple columns
subset = ldf[['name', 'age']]
```

### Row Filtering

```python
adults = ldf[ldf['age'] >= 18]
```

### Assignment & Transformation

```python
ldf2 = ldf.assign(is_adult=ldf._df['age'] >= 18)
```

### GroupBy & Aggregation

```python
grouped = ldf.groupby('age').agg({'name': 'count'})
```

### Chaining Operations

```python
result = ldf[ldf['age'] > 20].assign(category='senior')
```

---

## 🏷️ Metadata & Advanced Usage

```python
ldf = LineageDataFrame(df, name="customers", tracker=tracker, metadata={
    'source': 'database',
    'table': 'customers',
    'schema': 'public',
    'last_updated': '2025-09-17',
    'owner': 'data_team'
})
```

---

## 🔍 Under the Hood

- **All operations** (selection, assignment, filtering, joins, merges, groupby, etc.) are tracked as nodes and edges in the lineage graph.
- **Access the underlying DataFrame** with `. _df` if you need raw pandas methods.
- **Export lineage** at any time:

  ```python
  print(tracker.export_graph())
  tracker.visualize()
  ```

---

## 🧑‍💻 Best Practices

- Always use `LineageDataFrame` for any data you want to track
- Use meaningful `name` and `metadata` for each DataFrame
- Chain operations for clear, auditable pipelines
- Use `.visualize()` and `.export_graph()` to review your lineage

---

## 🏁 Next Steps

- [Concepts Guide](concepts.md)
- [Database Connectors Guide](database-connectors.md)
- [Full Documentation Index](index.md)
