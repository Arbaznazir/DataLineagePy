"""
Advanced visualization module for DataLineagePy.

This module provides comprehensive visualization capabilities including:
- Interactive lineage graphs with real-time updates
- 3D visualization for complex data relationships
- Custom dashboard builder for enterprise reporting
- Mobile-optimized UI components
- Advanced graph layouts and rendering
"""

# Core visualization components
from .graph_visualizer import GraphVisualizer
from .report_generator import ReportGenerator
from .interactive_graph import (
    InteractiveGraphVisualizer,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
    create_interactive_graph
)

# Advanced visualization components
from .three_d_visualizer import ThreeDVisualizer, create_3d_visualizer
from .dashboard_builder import DashboardBuilder, create_dashboard_builder
from .mobile_ui import MobileRenderer, create_mobile_renderer
from .export_manager import ExportManager, create_export_manager

# Configuration classes
from .three_d_visualizer import ThreeDConfig, Node3D, Edge3D
from .dashboard_builder import DashboardConfig, WidgetConfig, WidgetType
from .mobile_ui import MobileConfig, MobileCard, MobileListItem
from .export_manager import ExportConfig, ExportFormat, ExportQuality

# Enums
from .three_d_visualizer import Camera3DMode, Physics3DMode
from .dashboard_builder import ChartType, LayoutType
from .mobile_ui import MobileViewType, GestureType, ScreenSize
from .export_manager import ExportSize

__all__ = [
    # Core visualization
    'GraphVisualizer',
    'ReportGenerator',

    # Interactive graph
    'InteractiveGraphVisualizer',
    'GraphNode',
    'GraphEdge',
    'NodeType',
    'EdgeType',
    'GraphLayout',
    'InteractiveGraphConfig',
    'create_interactive_graph',

    # 3D visualization
    'ThreeDVisualizer',
    'ThreeDConfig',
    'Node3D',
    'Edge3D',
    'Camera3DMode',
    'Physics3DMode',
    'create_3d_visualizer',

    # Dashboard builder
    'DashboardBuilder',
    'DashboardConfig',
    'WidgetConfig',
    'WidgetType',
    'ChartType',
    'LayoutType',
    'create_dashboard_builder',

    # Mobile UI
    'MobileRenderer',
    'MobileConfig',
    'MobileCard',
    'MobileListItem',
    'MobileViewType',
    'GestureType',
    'ScreenSize',
    'create_mobile_renderer',

    # Export management
    'ExportManager',
    'ExportConfig',
    'ExportFormat',
    'ExportQuality',
    'ExportSize',
    'create_export_manager',

    # Configuration dictionaries
    'DEFAULT_GRAPH_CONFIG',
    'DEFAULT_3D_CONFIG',
    'DEFAULT_DASHBOARD_CONFIG',
    'DEFAULT_MOBILE_CONFIG',
    'DEFAULT_EXPORT_CONFIG',

    # Supported features
    'SUPPORTED_VISUALIZATION_TYPES',
    'SUPPORTED_EXPORT_FORMATS',
    'SUPPORTED_LAYOUT_ALGORITHMS',
    'SUPPORTED_MOBILE_VIEWS',
]

DEFAULT_GRAPH_CONFIG = {
    'width': 1200,
    'height': 800,
    'node_size': 10,
    'edge_width': 2,
    'font_size': 12,
    'background_color': '#ffffff',
    'node_color': '#1f77b4',
    'edge_color': '#666666',
    'highlight_color': '#ff7f0e',
    'animation_duration': 500,
    'zoom_enabled': True,
    'pan_enabled': True,
    'selection_enabled': True,
    'tooltip_enabled': True,
}

DEFAULT_3D_CONFIG = {
    'width': 1200,
    'height': 800,
    'camera_distance': 1000,
    'node_size': 5,
    'edge_width': 1,
    'enable_physics': True,
    'gravity': -30,
    'spring_length': 100,
    'spring_strength': 0.08,
    'damping': 0.09,
    'enable_controls': True,
    'auto_rotate': False,
    'background_color': '#000000',
}

DEFAULT_DASHBOARD_CONFIG = {
    'title': 'Data Lineage Dashboard',
    'theme': 'light',
    'layout': 'grid',
    'responsive': True,
    'refresh_interval': 30,
    'enable_filters': True,
    'enable_search': True,
    'enable_export': True,
    'show_legend': True,
    'show_toolbar': True,
}

DEFAULT_MOBILE_CONFIG = {
    'responsive_breakpoints': {
        'mobile': 768,
        'tablet': 1024,
        'desktop': 1200,
    },
    'touch_enabled': True,
    'swipe_enabled': True,
    'pinch_zoom_enabled': True,
    'simplified_ui': True,
    'compact_mode': True,
    'offline_support': True,
}

DEFAULT_EXPORT_CONFIG = {
    'format': 'png',
    'quality': 'high',
    'size': 'large',
    'dpi': 300,
    'include_title': True,
    'include_legend': True,
    'include_metadata': True,
    'background_color': 'white',
    'theme': 'plotly_white',
    'compression': True,
}

# Supported visualization types
SUPPORTED_VISUALIZATION_TYPES = [
    'interactive_graph',
    '3d_visualization',
    'dashboard',
    'mobile_ui',
    'timeline',
    'heatmap',
    'sankey',
    'tree_map',
    'network_graph',
    'hierarchical_view',
]

# Supported export formats
SUPPORTED_EXPORT_FORMATS = [
    'png',
    'jpeg',
    'svg',
    'pdf',
    'html',
    'json',
    'csv',
    'excel',
    'powerpoint',
    'word',
    'zip',
]

# Supported layout algorithms
SUPPORTED_LAYOUT_ALGORITHMS = [
    'force_directed',
    'circular',
    'hierarchical',
    'grid',
    'random',
    'spring',
    'fruchterman_reingold',
    'kamada_kawai',
    'spectral',
]

# Supported mobile views
SUPPORTED_MOBILE_VIEWS = [
    'card_view',
    'list_view',
    'tree_view',
    'timeline_view',
    'search_view',
    'detail_view',
    'graph_view',
]
