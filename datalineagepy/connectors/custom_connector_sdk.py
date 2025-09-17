"""
Custom Connector SDK for DataLineagePy
Provides a base class and utilities for building custom data connectors with full lineage tracking support.
"""
from datalineagepy.core.tracker import LineageTracker
from typing import Any, Dict, Optional


class BaseCustomConnector:
    """Base class for custom connectors."""

    def __init__(self, tracker: Optional[LineageTracker] = None, name: str = "custom_connector"):
        self.tracker = tracker or LineageTracker(name=name)
        self.name = name

    def connect(self, *args, **kwargs):
        """Establish connection to the data source (override in subclass)."""
        raise NotImplementedError(
            "connect() must be implemented in your custom connector.")

    def execute(self, operation: str, *args, **kwargs) -> Any:
        """Execute an operation (query, read, write, etc.) and track lineage."""
        # Track operation in lineage
        node = self.tracker.create_node("custom_operation", operation)
        node.add_metadata("args", args)
        node.add_metadata("kwargs", kwargs)
        # Actual operation logic should be implemented in subclass
        raise NotImplementedError(
            "execute() must be implemented in your custom connector.")

    def close(self):
        """Close the connection (override in subclass if needed)."""
        pass

    def export_lineage(self) -> Dict:
        """Export the tracked lineage graph."""
        return self.tracker.export_graph(format="dict")
