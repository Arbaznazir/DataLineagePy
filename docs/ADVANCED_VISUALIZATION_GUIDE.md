# Advanced Visualization Guide for DataLineagePy

## Overview

DataLineagePy provides comprehensive advanced visualization capabilities designed for enterprise-grade data lineage analysis. This guide covers the complete visualization ecosystem including 3D visualization, interactive dashboards, mobile-optimized UI components, and flexible export management.

## Table of Contents

1. [Quick Start](#quick-start)
2. [3D Visualization](#3d-visualization)
3. [Dashboard Builder](#dashboard-builder)
4. [Mobile UI Components](#mobile-ui-components)
5. [Export Manager](#export-manager)
6. [Integration Examples](#integration-examples)
7. [Performance Optimization](#performance-optimization)
8. [Troubleshooting](#troubleshooting)

## Quick Start

### Installation

```bash
# Install visualization dependencies
pip install -r requirements-visualization.txt

# Or install specific components
pip install plotly dash networkx pandas pillow reportlab
```

### Basic Usage

```python
import asyncio
from datalineagepy.visualization import (
    create_3d_visualizer,
    create_dashboard_builder,
    create_mobile_renderer,
    create_export_manager
)

async def basic_example():
    # Initialize components
    visualizer_3d = create_3d_visualizer()
    dashboard = create_dashboard_builder()
    mobile_ui = create_mobile_renderer()
    exporter = create_export_manager()
    
    # Start services
    await visualizer_3d.start()
    await exporter.start()
    
    # Your visualization code here
    
    # Cleanup
    await visualizer_3d.stop()
    await exporter.stop()

# Run the example
asyncio.run(basic_example())
```

## 3D Visualization

### Features

- **Immersive 3D Rendering**: Interactive 3D graphs using Plotly and WebGL
- **Physics Simulation**: Real-time physics with gravity, springs, and repulsion
- **Clustering**: Automatic node grouping and layering
- **Camera Controls**: Multiple camera modes (orbit, fly, first-person)
- **Performance Optimization**: Level-of-detail rendering for large graphs

### Configuration

```python
from datalineagepy.visualization import ThreeDConfig, Camera3DMode, Physics3DMode

config = ThreeDConfig(
    width=1200,
    height=800,
    camera_mode=Camera3DMode.ORBIT,
    physics_enabled=True,
    physics_mode=Physics3DMode.FORCE_DIRECTED,
    clustering_enabled=True,
    layer_separation=150.0,
    animation_enabled=True,
    node_size_range=(5.0, 30.0),
    edge_width_range=(1.0, 10.0)
)
```

### Basic 3D Visualization

```python
from datalineagepy.visualization import create_3d_visualizer, Node3D, Edge3D

async def create_3d_visualization():
    # Create visualizer
    visualizer = create_3d_visualizer(config)
    await visualizer.start()
    
    # Add nodes
    node1 = Node3D(
        id="source",
        label="Data Source",
        node_type="source",
        size=20.0,
        color="#4CAF50"
    )
    
    node2 = Node3D(
        id="transform",
        label="Transformation",
        node_type="transformation",
        size=15.0,
        color="#2196F3"
    )
    
    await visualizer.add_node(node1)
    await visualizer.add_node(node2)
    
    # Add edge
    edge = Edge3D(
        source_id="source",
        target_id="transform",
        edge_type="data_flow",
        width=2.0,
        color="#666666"
    )
    
    await visualizer.add_edge(edge)
    
    # Start physics simulation
    await visualizer.start_physics()
    
    # Render visualization
    figure = await visualizer.render()
    
    return figure
```

### Advanced 3D Features

```python
# Clustering nodes by type
await visualizer.cluster_nodes_by_type()

# Create layers for hierarchical data
await visualizer.create_layer("input", z_position=0)
await visualizer.create_layer("processing", z_position=150)
await visualizer.create_layer("output", z_position=300)

# Animate camera movement
await visualizer.animate_camera_to_position(
    position=(100, 100, 100),
    target=(0, 0, 0),
    duration=2000
)

# Apply custom physics forces
await visualizer.apply_custom_force(
    force_type="gravity",
    strength=-50,
    direction=(0, -1, 0)
)
```

## Dashboard Builder

### Features

- **Widget System**: 10+ widget types (graphs, charts, KPIs, tables)
- **Grid Layout**: Responsive grid-based layout management
- **Real-time Updates**: Live data updates and refresh capabilities
- **Theming**: Light/dark themes with customization
- **Export Ready**: Built-in export functionality

### Widget Types

```python
from datalineagepy.visualization import WidgetType, ChartType

# Available widget types
widget_types = [
    WidgetType.LINEAGE_GRAPH,    # Interactive lineage graph
    WidgetType.CHART,            # Various chart types
    WidgetType.TABLE,            # Data tables
    WidgetType.KPI_CARD,         # Key performance indicators
    WidgetType.TIMELINE,         # Timeline visualization
    WidgetType.HEATMAP,          # Heatmap visualization
    WidgetType.TREEMAP,          # Treemap visualization
    WidgetType.SANKEY,           # Sankey diagram
    WidgetType.GAUGE,            # Gauge charts
    WidgetType.TEXT,             # Text content
    WidgetType.IMAGE,            # Images
    WidgetType.IFRAME            # Embedded content
]

# Chart types for CHART widgets
chart_types = [
    ChartType.LINE,
    ChartType.BAR,
    ChartType.SCATTER,
    ChartType.PIE,
    ChartType.HISTOGRAM,
    ChartType.BOX,
    ChartType.VIOLIN,
    ChartType.AREA
]
```

### Creating a Dashboard

```python
from datalineagepy.visualization import (
    create_dashboard_builder,
    DashboardConfig,
    WidgetConfig,
    LayoutType
)

async def create_dashboard():
    # Configure dashboard
    config = DashboardConfig(
        title="Data Lineage Analytics",
        theme="dark",
        layout_type=LayoutType.GRID,
        grid_columns=12,
        auto_refresh=True,
        refresh_interval=30,
        real_time_updates=True
    )
    
    # Create dashboard builder
    dashboard = create_dashboard_builder(config)
    
    # Create lineage graph widget
    lineage_widget = WidgetConfig(
        id="main_lineage",
        title="Data Lineage Graph",
        widget_type=WidgetType.LINEAGE_GRAPH,
        position=(0, 0),
        size=(8, 6),
        data_source="lineage_tracker",
        interactive=True,
        refresh_interval=60
    )
    
    # Create metrics widget
    metrics_widget = WidgetConfig(
        id="kpi_metrics",
        title="Pipeline Metrics",
        widget_type=WidgetType.KPI_CARD,
        position=(8, 0),
        size=(4, 3),
        chart_config={
            "metrics": [
                {"name": "Total Nodes", "value": 150, "trend": "+5%"},
                {"name": "Active Pipelines", "value": 12, "trend": "+2"},
                {"name": "Data Quality", "value": "98.5%", "trend": "+0.3%"},
                {"name": "Processing Time", "value": "2.3s", "trend": "-0.1s"}
            ]
        }
    )
    
    # Create performance chart
    performance_widget = WidgetConfig(
        id="performance_chart",
        title="Performance Trends",
        widget_type=WidgetType.CHART,
        chart_type=ChartType.LINE,
        position=(0, 6),
        size=(12, 4),
        chart_config={
            "data": {
                "x": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
                "y": [1200, 1100, 1500, 1800, 1600, 1300]
            },
            "title": "Throughput (records/hour)",
            "xaxis_title": "Time",
            "yaxis_title": "Records/Hour"
        }
    )
    
    # Add widgets to dashboard
    await dashboard.add_widget(lineage_widget)
    await dashboard.add_widget(metrics_widget)
    await dashboard.add_widget(performance_widget)
    
    # Generate dashboard HTML
    html = await dashboard.render()
    
    return html
```

### Real-time Dashboard Updates

```python
# Enable real-time updates
await dashboard.enable_real_time_updates()

# Update widget data
await dashboard.update_widget_data(
    widget_id="kpi_metrics",
    data={
        "metrics": [
            {"name": "Total Nodes", "value": 155, "trend": "+8%"}
        ]
    }
)

# Refresh specific widget
await dashboard.refresh_widget("performance_chart")

# Broadcast update to all connected clients
await dashboard.broadcast_update({
    "type": "data_update",
    "widget_id": "main_lineage",
    "timestamp": datetime.utcnow().isoformat()
})
```

## Mobile UI Components

### Features

- **Responsive Design**: Optimized for mobile, tablet, and desktop
- **Touch Gestures**: Swipe, pinch, tap, and long-press support
- **Offline Support**: Caching and offline functionality
- **Performance**: Virtual scrolling and lazy loading
- **Accessibility**: WCAG 2.1 AA compliance

### Mobile Views

```python
from datalineagepy.visualization import (
    create_mobile_renderer,
    MobileConfig,
    MobileViewType,
    ScreenSize
)

# Configure mobile renderer
config = MobileConfig(
    screen_size=ScreenSize.MOBILE,
    touch_enabled=True,
    navigation_type="bottom_tabs",
    theme="dark",
    performance_mode=True,
    offline_support=True,
    accessibility_enabled=True
)

mobile_renderer = create_mobile_renderer(config)
```

### Card View

```python
from datalineagepy.visualization import MobileCard

# Create mobile cards
cards = [
    MobileCard(
        id="card1",
        title="Customer Data Pipeline",
        subtitle="Active • 1.2M records/day",
        content="Real-time customer data processing with ML enrichment",
        image_url="/static/pipeline-icon.png",
        action_url="/pipeline/customer-data",
        metadata={
            "status": "active",
            "last_run": "2024-01-15T10:30:00Z",
            "success_rate": 99.8
        }
    ),
    MobileCard(
        id="card2",
        title="Analytics Dashboard",
        subtitle="Updated 5 min ago",
        content="Executive dashboard with key business metrics",
        action_url="/dashboard/analytics"
    )
]

# Render card view
card_html = await mobile_renderer.render_card_view(
    cards,
    title="Data Pipelines",
    enable_search=True,
    enable_filter=True,
    enable_pagination=True
)
```

### List View

```python
from datalineagepy.visualization import MobileListItem

# Create list items
items = [
    MobileListItem(
        id="item1",
        title="Data Ingestion → Cleaning",
        subtitle="Transformation • 99.5% success",
        description="Raw data cleaning and validation pipeline",
        icon="arrow-right",
        action_url="/lineage/ingestion-cleaning",
        metadata={"confidence": 0.95}
    ),
    MobileListItem(
        id="item2",
        title="ML Training → Model Deploy",
        subtitle="Model Pipeline • Active",
        description="Machine learning model training and deployment",
        icon="cpu",
        action_url="/lineage/ml-pipeline"
    )
]

# Render list view
list_html = await mobile_renderer.render_list_view(
    items,
    title="Data Lineage",
    enable_search=True,
    enable_grouping=True,
    group_by="subtitle"
)
```

### Mobile Graph View

```python
# Render simplified graph for mobile
graph_html = await mobile_renderer.render_graph_view(
    nodes=lineage_nodes,
    edges=lineage_edges,
    title="Lineage Graph",
    simplified=True,
    max_nodes=50,
    enable_clustering=True,
    touch_interactions=True
)
```

## Export Manager

### Features

- **Multiple Formats**: PNG, JPEG, SVG, PDF, HTML, JSON, CSV, Excel, ZIP
- **Quality Settings**: Low, medium, high, ultra quality options
- **Batch Processing**: Export multiple items simultaneously
- **Async Operations**: Non-blocking export processing
- **Progress Tracking**: Real-time export progress monitoring

### Export Formats

```python
from datalineagepy.visualization import ExportFormat, ExportQuality, ExportSize

# Available export formats
formats = [
    ExportFormat.PNG,        # Raster image
    ExportFormat.JPEG,       # Compressed image
    ExportFormat.SVG,        # Vector image
    ExportFormat.PDF,        # Document with metadata
    ExportFormat.HTML,       # Interactive web page
    ExportFormat.JSON,       # Data export
    ExportFormat.CSV,        # Tabular data
    ExportFormat.EXCEL,      # Excel workbook
    ExportFormat.ZIP         # Archive of multiple formats
]

# Quality settings
quality_levels = [
    ExportQuality.LOW,       # Fast, smaller files
    ExportQuality.MEDIUM,    # Balanced
    ExportQuality.HIGH,      # High quality, larger files
    ExportQuality.ULTRA      # Maximum quality
]

# Size presets
size_presets = [
    ExportSize.THUMBNAIL,    # 200x150
    ExportSize.SMALL,        # 800x600
    ExportSize.MEDIUM,       # 1200x900
    ExportSize.LARGE,        # 1920x1080
    ExportSize.EXTRA_LARGE,  # 2560x1440
    ExportSize.PRINT_LETTER, # 8.5x11 inches
    ExportSize.PRINT_A4,     # A4 size
    ExportSize.CUSTOM        # Custom dimensions
]
```

### Basic Export

```python
from datalineagepy.visualization import create_export_manager, ExportConfig

async def export_visualization():
    # Create export manager
    exporter = create_export_manager("exports")
    await exporter.start()
    
    # Configure export
    config = ExportConfig(
        format=ExportFormat.PNG,
        quality=ExportQuality.HIGH,
        size=ExportSize.LARGE,
        filename="lineage_graph",
        include_title=True,
        include_metadata=True,
        background_color="white"
    )
    
    # Export visualization
    job_id = await exporter.export_visualization(
        figure=plotly_figure,
        config=config,
        metadata={
            "title": "Data Lineage Graph",
            "description": "Complete data pipeline visualization",
            "generated_at": datetime.utcnow().isoformat()
        }
    )
    
    # Wait for completion
    job = await exporter.wait_for_job(job_id)
    
    if job.status == "completed":
        print(f"Export completed: {job.output_path}")
    else:
        print(f"Export failed: {job.error}")
    
    await exporter.stop()
```

### Batch Export

```python
async def batch_export_example():
    exporter = create_export_manager()
    await exporter.start()
    
    # Prepare multiple export items
    export_items = [
        {
            "figure": dashboard_figure,
            "metadata": {"title": "Dashboard - PNG"},
            "config_overrides": {"format": ExportFormat.PNG}
        },
        {
            "figure": dashboard_figure,
            "metadata": {"title": "Dashboard - PDF"},
            "config_overrides": {"format": ExportFormat.PDF}
        },
        {
            "data": lineage_data,
            "metadata": {"title": "Lineage Data"},
            "config_overrides": {"format": ExportFormat.JSON}
        }
    ]
    
    # Base configuration
    base_config = ExportConfig(
        quality=ExportQuality.HIGH,
        size=ExportSize.LARGE,
        filename="batch_export",
        include_metadata=True
    )
    
    # Execute batch export
    job_ids = await exporter.batch_export(export_items, base_config)
    
    # Wait for all jobs
    for job_id in job_ids:
        job = await exporter.wait_for_job(job_id)
        print(f"Batch item completed: {job.output_path}")
    
    await exporter.stop()
```

### Export Progress Monitoring

```python
async def monitor_export_progress():
    # Start export
    job_id = await exporter.export_visualization(figure, config)
    
    # Monitor progress
    while True:
        job = await exporter.get_job_status(job_id)
        
        if job.status == "completed":
            print(f"Export completed: {job.output_path}")
            break
        elif job.status == "failed":
            print(f"Export failed: {job.error}")
            break
        else:
            print(f"Progress: {job.progress:.1%}")
            await asyncio.sleep(1)
```

## Integration Examples

### Complete Workflow Example

```python
async def complete_workflow_example():
    """Demonstrates integration of all visualization components."""
    
    # Initialize components
    visualizer_3d = create_3d_visualizer()
    dashboard = create_dashboard_builder()
    mobile_ui = create_mobile_renderer()
    exporter = create_export_manager()
    
    # Start services
    await visualizer_3d.start()
    await exporter.start()
    
    try:
        # 1. Create 3D visualization
        await visualizer_3d.add_node(Node3D("node1", "Source", "source"))
        await visualizer_3d.add_node(Node3D("node2", "Transform", "transform"))
        await visualizer_3d.add_edge(Edge3D("node1", "node2", "data_flow"))
        
        figure_3d = await visualizer_3d.render()
        
        # 2. Build dashboard
        widget = WidgetConfig(
            id="3d_view",
            title="3D Lineage View",
            widget_type=WidgetType.LINEAGE_GRAPH,
            position=(0, 0),
            size=(12, 8)
        )
        
        await dashboard.add_widget(widget)
        dashboard_html = await dashboard.render()
        
        # 3. Create mobile views
        cards = [
            MobileCard("card1", "Data Pipeline", "Active", "Processing data...")
        ]
        mobile_html = await mobile_ui.render_card_view(cards, "Pipelines")
        
        # 4. Export everything
        exports = [
            (figure_3d, ExportFormat.PNG, "3d_visualization"),
            (dashboard_html, ExportFormat.HTML, "dashboard"),
            (mobile_html, ExportFormat.HTML, "mobile_view")
        ]
        
        for content, format_type, filename in exports:
            config = ExportConfig(
                format=format_type,
                filename=filename,
                quality=ExportQuality.HIGH
            )
            
            if hasattr(content, 'to_dict'):  # Plotly figure
                job_id = await exporter.export_visualization(content, config)
            else:  # HTML content
                job_id = await exporter.export_dashboard(content, config)
            
            job = await exporter.wait_for_job(job_id)
            print(f"Exported {filename}: {job.output_path}")
    
    finally:
        # Cleanup
        await visualizer_3d.stop()
        await exporter.stop()
```

### Real-time Integration

```python
async def real_time_integration():
    """Example of real-time data updates across all components."""
    
    # Setup components with real-time enabled
    dashboard = create_dashboard_builder(
        DashboardConfig(real_time_updates=True)
    )
    
    visualizer_3d = create_3d_visualizer(
        ThreeDConfig(animation_enabled=True)
    )
    
    # Simulate real-time data updates
    async def update_loop():
        while True:
            # Update 3D visualization
            new_node = Node3D(
                id=f"node_{datetime.now().timestamp()}",
                label="New Data Source",
                node_type="source"
            )
            await visualizer_3d.add_node(new_node)
            
            # Update dashboard metrics
            await dashboard.update_widget_data(
                "metrics",
                {"total_nodes": await visualizer_3d.get_node_count()}
            )
            
            # Wait before next update
            await asyncio.sleep(10)
    
    # Start update loop
    asyncio.create_task(update_loop())
```

## Performance Optimization

### 3D Visualization Performance

```python
# Optimize for large graphs
config = ThreeDConfig(
    # Reduce physics calculations
    physics_enabled=True,
    physics_iterations=50,  # Reduce from default 100
    
    # Enable level-of-detail
    lod_enabled=True,
    lod_threshold=1000,  # Switch to simplified rendering above 1000 nodes
    
    # Optimize clustering
    clustering_enabled=True,
    cluster_threshold=100,  # Cluster when more than 100 nodes
    
    # Reduce visual complexity
    node_size_range=(3.0, 15.0),  # Smaller nodes
    edge_width_range=(0.5, 3.0),  # Thinner edges
    
    # Disable expensive features for large graphs
    animation_enabled=False,
    shadows_enabled=False
)
```

### Dashboard Performance

```python
# Optimize dashboard for performance
dashboard_config = DashboardConfig(
    # Reduce refresh frequency
    refresh_interval=60,  # Refresh every minute instead of 30 seconds
    
    # Enable caching
    cache_enabled=True,
    cache_ttl=300,  # Cache for 5 minutes
    
    # Limit real-time updates
    real_time_updates=False,  # Disable for better performance
    
    # Optimize rendering
    lazy_loading=True,
    virtual_scrolling=True
)
```

### Export Performance

```python
# Optimize exports for speed
export_config = ExportConfig(
    # Use lower quality for faster exports
    quality=ExportQuality.MEDIUM,
    
    # Smaller sizes process faster
    size=ExportSize.MEDIUM,
    
    # Disable expensive features
    include_metadata=False,
    compression=False,  # Skip compression for speed
    
    # Batch processing
    batch_processing=True
)
```

### Memory Management

```python
# Memory optimization techniques
async def optimize_memory():
    # Limit concurrent operations
    exporter = create_export_manager()
    exporter.max_workers = 2  # Reduce from default 3
    
    # Clear caches periodically
    await dashboard.clear_cache()
    await visualizer_3d.clear_node_cache()
    
    # Use generators for large datasets
    async def process_nodes_in_batches(nodes, batch_size=100):
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i + batch_size]
            for node in batch:
                await visualizer_3d.add_node(node)
            
            # Process batch and clear memory
            await visualizer_3d.process_batch()
            await asyncio.sleep(0.1)  # Allow garbage collection
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```python
# Problem: Missing dependencies
ImportError: No module named 'plotly'

# Solution: Install visualization requirements
pip install -r requirements-visualization.txt
```

#### 2. Performance Issues

```python
# Problem: Slow 3D rendering
# Solution: Reduce complexity
config = ThreeDConfig(
    physics_enabled=False,  # Disable physics
    lod_enabled=True,       # Enable level-of-detail
    max_nodes=1000         # Limit node count
)
```

#### 3. Export Failures

```python
# Problem: Export timeouts
# Solution: Increase timeout and reduce quality
config = ExportConfig(
    quality=ExportQuality.MEDIUM,  # Reduce quality
    size=ExportSize.SMALL         # Reduce size
)

# Wait with longer timeout
job = await exporter.wait_for_job(job_id, timeout=300)  # 5 minutes
```

#### 4. Memory Issues

```python
# Problem: Out of memory errors
# Solution: Process in batches
async def process_large_dataset(nodes):
    batch_size = 100
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i:i + batch_size]
        await process_batch(batch)
        
        # Force garbage collection
        import gc
        gc.collect()
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable component debug modes
visualizer_3d = create_3d_visualizer(
    ThreeDConfig(debug_mode=True)
)

dashboard = create_dashboard_builder(
    DashboardConfig(debug_mode=True)
)
```

### Performance Monitoring

```python
# Monitor component performance
async def monitor_performance():
    # Get 3D visualizer stats
    stats_3d = await visualizer_3d.get_performance_stats()
    print(f"3D Render time: {stats_3d['render_time']:.2f}s")
    print(f"Node count: {stats_3d['node_count']}")
    
    # Get dashboard stats
    stats_dashboard = await dashboard.get_performance_stats()
    print(f"Dashboard render time: {stats_dashboard['render_time']:.2f}s")
    print(f"Widget count: {stats_dashboard['widget_count']}")
    
    # Get export stats
    stats_export = exporter.get_stats()
    print(f"Total exports: {stats_export['total_exports']}")
    print(f"Average export time: {stats_export['average_export_time']:.2f}s")
```

## Best Practices

### 1. Component Lifecycle Management

```python
async def proper_lifecycle():
    components = []
    
    try:
        # Initialize all components
        visualizer = create_3d_visualizer()
        dashboard = create_dashboard_builder()
        exporter = create_export_manager()
        
        components.extend([visualizer, dashboard, exporter])
        
        # Start all components
        for component in components:
            if hasattr(component, 'start'):
                await component.start()
        
        # Your application logic here
        
    finally:
        # Always cleanup
        for component in components:
            if hasattr(component, 'stop'):
                await component.stop()
```

### 2. Error Handling

```python
async def robust_error_handling():
    try:
        # Visualization operations
        result = await visualizer_3d.render()
        
    except MemoryError:
        # Handle memory issues
        await visualizer_3d.reduce_complexity()
        result = await visualizer_3d.render()
        
    except TimeoutError:
        # Handle timeouts
        logger.warning("Render timeout, using cached result")
        result = await visualizer_3d.get_cached_result()
        
    except Exception as e:
        # Log and handle unexpected errors
        logger.error(f"Visualization error: {e}")
        result = await visualizer_3d.render_fallback()
    
    return result
```

### 3. Configuration Management

```python
# Use configuration files
import json

def load_visualization_config(config_file):
    with open(config_file, 'r') as f:
        config_data = json.load(f)
    
    return {
        '3d_config': ThreeDConfig(**config_data['3d']),
        'dashboard_config': DashboardConfig(**config_data['dashboard']),
        'mobile_config': MobileConfig(**config_data['mobile']),
        'export_config': ExportConfig(**config_data['export'])
    }

# config.json
{
    "3d": {
        "width": 1200,
        "height": 800,
        "physics_enabled": true,
        "clustering_enabled": true
    },
    "dashboard": {
        "title": "Data Lineage Dashboard",
        "theme": "dark",
        "auto_refresh": true
    },
    "mobile": {
        "touch_enabled": true,
        "offline_support": true
    },
    "export": {
        "quality": "high",
        "format": "png"
    }
}
```

## API Reference

For detailed API documentation, see:
- [3D Visualizer API](api/3d_visualizer.md)
- [Dashboard Builder API](api/dashboard_builder.md)
- [Mobile UI API](api/mobile_ui.md)
- [Export Manager API](api/export_manager.md)

## Examples

Complete examples are available in the `examples/` directory:
- `advanced_visualization_example.py` - Comprehensive demo
- `3d_visualization_example.py` - 3D visualization focus
- `dashboard_example.py` - Dashboard building
- `mobile_ui_example.py` - Mobile interface
- `export_example.py` - Export functionality

## Support

For issues and questions:
- GitHub Issues: [DataLineagePy Issues](https://github.com/DataLineagePy/issues)
- Documentation: [Full Documentation](https://datalineagepy.readthedocs.io)
- Community: [Discord Server](https://discord.gg/datalineagepy)
