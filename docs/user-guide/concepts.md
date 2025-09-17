# 🌐 DataLineagePy Concepts Guide

Welcome to the DataLineagePy Concepts Guide! This page explains the core ideas, architecture, and mental models behind DataLineagePy, with beautiful structure and practical code for every concept.

---

## 🧩 What is Data Lineage?

**Data lineage** is the complete, auditable history of how your data moves, transforms, and evolves across your pipelines. It answers:

- Where did this data come from?
- What operations were performed?
- Who/what changed it, and when?
- How do changes propagate downstream?

**Visual Diagram:**

```
[Source Data] → [Transform 1] → [Join] → [Aggregate] → [ML Model] → [Report]
```

---

## 🏗️ Core Architecture

- **LineageTracker**: The brain. Tracks all operations, nodes, and edges in your data pipeline.
- **LineageDataFrame**: A pandas-compatible DataFrame wrapper that automatically logs every transformation.
- **GraphVisualizer**: Renders beautiful, interactive lineage graphs and dashboards.
- **Connectors**: Plug-and-play modules for databases, files, and cloud sources.
- **Validation & Analytics**: Built-in data quality, profiling, and validation tools.
- **Security**: RBAC, encryption, and audit trail for compliance.

---

## 🔄 How Lineage Tracking Works

1. **Wrap your DataFrame:**
   ```python
   from datalineagepy import LineageTracker, LineageDataFrame
   import pandas as pd
   tracker = LineageTracker(name="my_pipeline")
   df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
   ldf = LineageDataFrame(df, name="input", tracker=tracker)
   ```
2. **Perform operations as usual:**
   ```python
   ldf2 = ldf.assign(c=ldf._df['a'] + ldf._df['b'])
   ldf3 = ldf2.filter(ldf2._df['c'] > 5)
   ```
3. **Lineage is tracked automatically:**
   ```python
   print(tracker.export_graph())
   tracker.visualize()
   ```

---

## 🗺️ The Lineage Graph Model

- **Nodes**: Represent data objects (tables, DataFrames, files, ML steps)
- **Edges**: Represent operations (transform, join, filter, aggregate)
- **Metadata**: Every node/edge can store rich metadata (source, timestamp, user, etc.)

**Example:**

```python
node = tracker.create_node('table', 'sales')
node.add_metadata('source', 'mysql')
```

---

## 🧠 Operation Hooks & Custom Logic

You can register custom hooks to track business logic, enrich lineage, or trigger alerts.

```python
def my_custom_hook(data):
    # Custom transformation logic
    return data * 2
tracker.add_operation_hook('double', my_custom_hook)
ldf2 = ldf.apply_custom_operation('double')
```

---

## 🔒 Security & Compliance Concepts

- **RBAC**: Role-based access control for users and actions
- **Encryption**: AES-256 at-rest and in-transit
- **Audit Trail**: Every operation is logged for compliance

---

## 🤝 Real-Time Collaboration

- **WebSocket server/client** for live lineage editing and viewing
- **Team workflows**: Share, comment, and co-edit lineage graphs

```python
from datalineagepy.collaboration.realtime_collaboration import CollaborationServer, CollaborationClient
CollaborationServer().run()  # In one terminal
CollaborationClient().run()  # In another terminal
```

---

## 🧬 ML/AI Pipeline Tracking

- **AutoMLTracker**: Log, audit, and export every ML pipeline step
- **Explainability**: Export pipeline steps for downstream analysis

```python
from datalineagepy import AutoMLTracker
tracker = AutoMLTracker(name='ml_pipeline')
tracker.log_step('fit', model='LogisticRegression', params={'solver': 'lbfgs'})
tracker.log_step('predict', model='LogisticRegression')
print(tracker.export_ai_ready_format())
```

---

## 📈 Visualizing Your Lineage

- **Interactive HTML dashboards**: `tracker.visualize()`
- **Custom visualizations**: Use `GraphVisualizer` for advanced needs

---

## 🏁 Next Steps

- [DataFrame Wrapper Guide](dataframe-wrapper.md)
- [Database Connectors Guide](database-connectors.md)
- [Full Documentation Index](index.md)
