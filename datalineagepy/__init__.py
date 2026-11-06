"""
DataLineagePy - Enterprise-grade Python data lineage tracking library
====================================================================

A comprehensive solution for tracking data lineage with automatic pandas integration,
memory optimization, and enterprise-ready features.
"""

__version__ = "3.0.4"
__author__ = "Arbaz Nazir"
__email__ = "arbaznazir4@gmail.com"

# Core imports
try:
    from .core.tracker import LineageTracker
    from .core.nodes import DataNode, FileNode, DatabaseNode
    from .core.edges import LineageEdge
    from .core.dataframe_wrapper import (
        LineageDataFrame, read_csv, read_json, read_parquet,
        read_excel, read_multiple_files
    )
    from .core.operations import Operation
except ImportError:
    # Graceful fallback if core modules aren't available yet
    pass

# Connector imports
try:
    from .connectors.database import DatabaseConnector
    from .connectors.file import FileConnector
    from .connectors.cloud import CloudStorageConnector
except ImportError:
    pass

# Visualization imports
try:
    from .visualization.graph_visualizer import GraphVisualizer
    from .visualization.report_generator import ReportGenerator

except ImportError:
    pass


def configure_lineage(enabled=True, name=None, tracker=None):
    """Turn lineage tracking on or off for the active tracker.

    Args:
        enabled: Whether the tracker should record new operations.
        name: Optional replacement name for the tracker.
        tracker: Tracker to configure. Defaults to the global tracker.

    Returns:
        The configured tracker.
    """
    active = tracker or LineageTracker.get_global_instance()
    active.active = bool(enabled)
    if name is not None:
        active.name = name
    return active


# ML/AutoML imports (must be top-level for direct import)
from .ml.automl_tracker import AutoMLTracker

# Testing imports
try:
    from .testing.validators import LineageValidator
    from .testing.benchmarks import BenchmarkSuite
except ImportError:
    pass

# Benchmarks imports
try:
    from .benchmarks.performance_benchmarks import PerformanceBenchmarkSuite
    from .benchmarks.competitive_analysis import CompetitiveAnalyzer
    from .benchmarks.memory_profiler import MemoryProfiler
except ImportError:
    pass

_PUBLIC_API = [
    'AutoMLTracker',
    'LineageTracker',
    'DataNode', 'FileNode', 'DatabaseNode',
    'LineageEdge',
    'LineageDataFrame',
    'read_csv', 'read_json', 'read_parquet', 'read_excel', 'read_multiple_files',
    'Operation',
    'configure_lineage',
    'DatabaseConnector',
    'FileConnector',
    'CloudStorageConnector',
    'GraphVisualizer',
    'ReportGenerator',
    'LineageValidator',
    'BenchmarkSuite',
    'PerformanceBenchmarkSuite',
    'CompetitiveAnalyzer',
    'MemoryProfiler',
]
__all__ = [name for name in _PUBLIC_API if name in globals()]
