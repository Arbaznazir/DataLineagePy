# AutoMLTracker for DataLineagePy
from datalineagepy import LineageTracker


class AutoMLTracker(LineageTracker):
    """
    Tracks ML/AutoML pipeline steps and logs them as lineage operations.
    Usage:
        tracker = AutoMLTracker(name="automl_pipeline")
        tracker.log_step("fit", model="LogisticRegression", params={...})
    """

    def __init__(self, name="automl_pipeline", **kwargs):
        super().__init__(name=name, **kwargs)
        self.pipeline_steps = []

    def log_step(self, step_type, **kwargs):
        step = {"step_type": step_type, **kwargs}
        self.pipeline_steps.append(step)
        # Add a node for this step
        node_id = f"ml_step_{len(self.pipeline_steps)}"
        node = {
            "id": node_id,
            "type": "MLStep",
            "step_type": step_type,
            "details": kwargs
        }
        if not hasattr(self, "_custom_nodes"):
            self._custom_nodes = []
        self._custom_nodes.append(node)
        # Add an operation for this step
        if not hasattr(self, "_custom_operations"):
            self._custom_operations = []
        op = {
            "id": f"ml_op_{len(self.pipeline_steps)}",
            "type": step_type,
            "node_id": node_id,
            "details": kwargs
        }
        self._custom_operations.append(op)
        # Optionally, add to the lineage graph as an operation if available
        if hasattr(self, 'add_operation') and callable(getattr(self, 'add_operation')):
            self.add_operation(step_type, details=kwargs)

    def get_pipeline(self):
        return self.pipeline_steps

    def export_ai_ready_format(self):
        base = super().export_ai_ready_format()
        base["automl_pipeline_steps"] = self.pipeline_steps
        # Add ML steps as nodes and operations in the export
        if hasattr(self, "_custom_nodes"):
            base.setdefault("nodes", []).extend(self._custom_nodes)
        if hasattr(self, "_custom_operations"):
            base.setdefault("operations", []).extend(self._custom_operations)
        return base
