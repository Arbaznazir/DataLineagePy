"""
DataLineagePy - Enterprise-grade Python data lineage tracking library
====================================================================

A comprehensive solution for tracking data lineage with automatic pandas integration,
memory optimization, and enterprise-ready features.
"""

__version__ = "3.0.1"
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

__all__ = [
    'AutoMLTracker',
    'LineageTracker',
    'DataNode', 'FileNode', 'DatabaseNode',
    'LineageEdge',
    'LineageDataFrame',
    'read_csv', 'read_json', 'read_parquet', 'read_excel', 'read_multiple_files',
    'Operation',
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
