# Advanced ML/AI Pipeline Integration with DataLineagePy

DataLineagePy now supports direct tracking and export of ML/AI pipeline steps using the `AutoMLTracker` class. This enables full auditability and explainability for machine learning workflows, including AutoML and custom pipelines.

## Key Features

- **AutoMLTracker**: Log and track each ML pipeline step (fit, transform, predict, etc.)
- **Lineage Graph Export**: ML steps appear as nodes and operations in the lineage export
- **AI-ready Export**: Export pipeline steps for downstream AI/ML explainability
- **Notebook Integration**: Seamless use in Jupyter and Python scripts

## How to Use

### 1. Import and Initialize

```python
from datalineagepy import AutoMLTracker
from sklearn.linear_model import LogisticRegression

# Create an AutoMLTracker
tracker = AutoMLTracker(name="automl_pipeline")
```

### 2. Log ML Pipeline Steps

```python
# Log each step in your ML pipeline
tracker.log_step("fit", model="LogisticRegression", params={"solver": "lbfgs"})
tracker.log_step("predict", model="LogisticRegression")
```

### 3. Export and Visualize Lineage

```python
# Export AI-ready lineage
automl_export = tracker.export_ai_ready_format()
print("AutoML pipeline steps:", automl_export.get("automl_pipeline_steps", []))

# Show nodes and operations
print("ML Step Nodes:", automl_export.get("nodes", []))
print("ML Step Operations:", automl_export.get("operations", []))
```

### 4. Visualize in Notebooks

```python
# Visualize as a simple graph (text-based)
for node in automl_export.get("nodes", []):
    print(f"Node: {node['id']} | Type: {node['type']} | Step: {node.get('step_type')} | Details: {node.get('details')}")
for op in automl_export.get("operations", []):
    print(f"Operation: {op['id']} | Type: {op['type']} | Node: {op['node_id']} | Details: {op['details']}")
```

## Example Output

```
AutoML pipeline steps: [{'step_type': 'fit', 'model': 'LogisticRegression', 'params': {'solver': 'lbfgs'}}, ...]
ML Step Nodes: [{'id': 'ml_step_1', 'type': 'MLStep', ...}]
ML Step Operations: [{'id': 'ml_op_1', 'type': 'fit', ...}]
```

## When to Use

- ML/AI pipelines requiring full auditability
- AutoML workflows
- Regulatory and compliance reporting for ML
- Explainable AI (XAI) scenarios

## See Also

- [Quickstart Guide](../quickstart.md)
- [API Reference](../api/index.md)
- [Jupyter Notebook Example](../../examples/notebooks/ml_pipeline_integration_example.ipynb)

_Last updated: September 16, 2025_
