# 📚 DataLineagePy 3.0 Core API Reference

> **Version:** 3.0 &nbsp; | &nbsp; **Last Updated:** September 2025

---

Welcome to the official API reference for the DataLineagePy 3.0 core module. This guide provides detailed documentation for all primary classes, methods, and usage patterns in the core library.

## ✨ Core Components

- **LineageTracker**: Central object for tracking, visualizing, and exporting data lineage.
- **LineageDataFrame**: Drop-in replacement for pandas DataFrame with full lineage tracking.
- **DataFrameWrapper**: Lightweight wrapper for pandas DataFrames to enable lineage.
- **Validation & Profiling**: Built-in data validation, profiling, and quality checks.

---

## 🚀 Quick Start Example

```python
from datalineagepy import LineageTracker, LineageDataFrame

# Initialize tracker
tracker = LineageTracker()

# Wrap your DataFrame
ldf = LineageDataFrame(df, "source_data", tracker)

# Perform operations as usual
result = ldf.groupby('category').mean()

# Visualize lineage
tracker.visualize()
```

---

## 🏷️ Class & Method Reference

### LineageTracker

- `add_node(name, metadata=None)`
- `add_edge(source, target, operation=None)`
- `visualize(output_format='html')`
- `export_lineage(format, path)`
- `cleanup()`

### LineageDataFrame

- Inherits all pandas DataFrame methods
- Tracks all operations and transformations
- `get_lineage()`
- `validate(validation_rules)`

---

For a complete, auto-generated API reference, see the [full documentation site](../user-guide/index.md).
