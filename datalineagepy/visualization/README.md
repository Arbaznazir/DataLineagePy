# Advanced Visualization Module

## Overview

The Advanced Visualization module provides enterprise-grade visualization capabilities for DataLineagePy, enabling immersive 3D visualization, interactive dashboards, mobile-optimized UI components, and comprehensive export management.

## Features

### 🎯 Core Components

- **3D Visualizer**: Interactive 3D graphs with physics simulation and clustering
- **Dashboard Builder**: Responsive dashboards with 12+ widget types
- **Mobile UI Renderer**: Touch-optimized mobile interfaces
- **Export Manager**: Multi-format export with batch processing

### 🚀 Key Capabilities

- **Real-time Updates**: Live data streaming and visualization updates
- **Physics Simulation**: Force-directed layouts with gravity and springs
- **Multi-format Export**: PNG, PDF, SVG, HTML, JSON, Excel, and more
- **Mobile Optimization**: Touch gestures, offline support, responsive design
- **Enterprise Features**: Batch processing, async operations, performance monitoring

## Quick Start

### Installation

```bash
pip install -r requirements-visualization.txt
```

### Basic Usage

```python
import asyncio
from datalineagepy.visualization import (
    create_3d_visualizer,
    create_dashboard_builder,
    create_export_manager,
    Node3D,
    ExportConfig,
    ExportFormat
)

async def basic_example():
    # Create components
    visualizer = create_3d_visualizer()
    exporter = create_export_manager()
    
    # Start services
    await visualizer.start()
    await exporter.start()
    
    # Add data
    node = Node3D("node1", "Data Source", "source")
    await visualizer.add_node(node)
    
    # Render and export
    figure = await visualizer.render()
    config = ExportConfig(format=ExportFormat.PNG, filename="lineage")
    job_id = await exporter.export_visualization(figure, config)
    
    # Wait for completion
    job = await exporter.wait_for_job(job_id)
    print(f"Exported: {job.output_path}")
    
    # Cleanup
    await visualizer.stop()
    await exporter.stop()

asyncio.run(basic_example())
```

## Module Structure

```
datalineagepy/visualization/
├── __init__.py                 # Main module exports
├── threed_visualizer.py        # 3D visualization engine
├── dashboard_builder.py        # Dashboard creation and management
├── mobile_renderer.py          # Mobile UI components
├── export_manager.py           # Export functionality
├── interactive_graph.py        # Interactive graph components
└── README.md                   # This file
```

## Component Documentation

### 3D Visualizer

Interactive 3D visualization with physics simulation:

```python
from datalineagepy.visualization import create_3d_visualizer, ThreeDConfig

config = ThreeDConfig(
    width=1200,
    height=800,
    physics_enabled=True,
    clustering_enabled=True,
    animation_enabled=True
)

visualizer = create_3d_visualizer(config)
```

**Key Features:**
- Physics simulation with force-directed layouts
- Automatic node clustering by type
- Multiple camera modes (orbit, fly, first-person)
- Level-of-detail rendering for performance
- Real-time animation and updates

### Dashboard Builder

Create responsive dashboards with multiple widget types:

```python
from datalineagepy.visualization import create_dashboard_builder, WidgetConfig, WidgetType

dashboard = create_dashboard_builder()

widget = WidgetConfig(
    id="metrics",
    title="Pipeline Metrics",
    widget_type=WidgetType.KPI_CARD,
    position=(0, 0),
    size=(6, 4)
)

await dashboard.add_widget(widget)
html = await dashboard.render()
```

**Widget Types:**
- Lineage graphs
- Charts (line, bar, pie, scatter)
- KPI cards
- Tables
- Timelines
- Heatmaps
- Gauges

### Mobile UI Renderer

Touch-optimized mobile interfaces:

```python
from datalineagepy.visualization import create_mobile_renderer, MobileCard

mobile = create_mobile_renderer()

cards = [
    MobileCard("id1", "Pipeline 1", "Active", "Processing data...")
]

html = await mobile.render_card_view(cards, "Pipelines")
```

**Mobile Views:**
- Card view for pipelines
- List view for lineage items
- Simplified graph view
- Search and pagination
- Touch gesture support

### Export Manager

Multi-format export with batch processing:

```python
from datalineagepy.visualization import create_export_manager, ExportConfig, ExportFormat

exporter = create_export_manager()
await exporter.start()

config = ExportConfig(
    format=ExportFormat.PNG,
    quality=ExportQuality.HIGH,
    filename="export"
)

job_id = await exporter.export_visualization(figure, config)
job = await exporter.wait_for_job(job_id)
```

**Export Formats:**
- Images: PNG, JPEG, SVG
- Documents: PDF, HTML
- Data: JSON, CSV, Excel
- Archives: ZIP

## Configuration

### Default Configurations

```python
# 3D Visualization
DEFAULT_3D_CONFIG = {
    "width": 1000,
    "height": 700,
    "physics_enabled": True,
    "clustering_enabled": True,
    "animation_enabled": True,
    "camera_mode": "orbit"
}

# Dashboard
DEFAULT_DASHBOARD_CONFIG = {
    "title": "Data Lineage Dashboard",
    "theme": "dark",
    "layout_type": "grid",
    "auto_refresh": True,
    "refresh_interval": 60
}

# Export
DEFAULT_EXPORT_CONFIG = {
    "quality": "high",
    "format": "png",
    "include_metadata": True,
    "background_color": "white"
}
```

### Environment Variables

```bash
# Performance settings
VISUALIZATION_MAX_NODES=10000
VISUALIZATION_MAX_EDGES=50000
VISUALIZATION_CACHE_SIZE=1000

# Export settings
EXPORT_MAX_WORKERS=3
EXPORT_TIMEOUT=300
EXPORT_QUALITY=high

# Mobile settings
MOBILE_TOUCH_ENABLED=true
MOBILE_OFFLINE_SUPPORT=true
```

## Performance Optimization

### Large Graph Handling

```python
# Optimize for large graphs
config = ThreeDConfig(
    physics_enabled=False,      # Disable physics for speed
    lod_enabled=True,          # Enable level-of-detail
    clustering_enabled=True,    # Group nodes for performance
    max_nodes=5000            # Limit node count
)
```

### Memory Management

```python
# Process nodes in batches
async def add_nodes_batch(visualizer, nodes, batch_size=100):
    for i in range(0, len(nodes), batch_size):
        batch = nodes[i:i + batch_size]
        for node in batch:
            await visualizer.add_node(node)
        await asyncio.sleep(0.1)  # Allow garbage collection
```

### Export Optimization

```python
# Faster exports
config = ExportConfig(
    quality=ExportQuality.MEDIUM,  # Reduce quality for speed
    size=ExportSize.MEDIUM,        # Smaller size
    compression=False              # Skip compression
)
```

## Integration Examples

### Complete Workflow

```python
async def complete_workflow():
    # Initialize components
    visualizer = create_3d_visualizer()
    dashboard = create_dashboard_builder()
    exporter = create_export_manager()
    
    # Start services
    await visualizer.start()
    await exporter.start()
    
    try:
        # Add data to 3D visualization
        await visualizer.add_node(Node3D("node1", "Source", "source"))
        figure = await visualizer.render()
        
        # Create dashboard
        widget = WidgetConfig("widget1", "3D View", WidgetType.LINEAGE_GRAPH)
        await dashboard.add_widget(widget)
        dashboard_html = await dashboard.render()
        
        # Export both
        exports = [
            (figure, ExportFormat.PNG, "3d_view"),
            (dashboard_html, ExportFormat.HTML, "dashboard")
        ]
        
        for content, format_type, filename in exports:
            config = ExportConfig(format=format_type, filename=filename)
            if hasattr(content, 'to_dict'):
                job_id = await exporter.export_visualization(content, config)
            else:
                job_id = await exporter.export_dashboard(content, config)
            
            job = await exporter.wait_for_job(job_id)
            print(f"Exported {filename}: {job.output_path}")
    
    finally:
        await visualizer.stop()
        await exporter.stop()
```

### Real-time Updates

```python
async def real_time_demo():
    dashboard = create_dashboard_builder(
        DashboardConfig(real_time_updates=True)
    )
    
    # Enable real-time updates
    await dashboard.enable_real_time_updates()
    
    # Update data periodically
    while True:
        await dashboard.update_widget_data(
            "metrics",
            {"timestamp": datetime.now().isoformat()}
        )
        await asyncio.sleep(10)
```

## Error Handling

### Common Patterns

```python
async def robust_visualization():
    try:
        result = await visualizer.render()
    except MemoryError:
        # Reduce complexity and retry
        await visualizer.reduce_complexity()
        result = await visualizer.render()
    except TimeoutError:
        # Use cached result
        result = await visualizer.get_cached_result()
    except Exception as e:
        logger.error(f"Visualization error: {e}")
        result = await visualizer.render_fallback()
    
    return result
```

### Export Error Handling

```python
async def safe_export(exporter, figure, config):
    try:
        job_id = await exporter.export_visualization(figure, config)
        job = await exporter.wait_for_job(job_id, timeout=120)
        
        if job.status == "failed":
            # Retry with lower quality
            config.quality = ExportQuality.LOW
            job_id = await exporter.export_visualization(figure, config)
            job = await exporter.wait_for_job(job_id, timeout=60)
        
        return job.output_path if job.status == "completed" else None
    
    except Exception as e:
        logger.error(f"Export failed: {e}")
        return None
```

## Testing

### Unit Tests

```bash
# Run visualization tests
python -m pytest datalineagepy/testing/visualization_tests.py -v

# Run specific test class
python -m pytest datalineagepy/testing/visualization_tests.py::TestThreeDVisualizer -v

# Run with coverage
python -m pytest datalineagepy/testing/visualization_tests.py --cov=datalineagepy.visualization
```

### Performance Tests

```python
# Test large graph performance
async def test_performance():
    visualizer = create_3d_visualizer()
    await visualizer.start()
    
    # Add 1000 nodes
    for i in range(1000):
        node = Node3D(f"node_{i}", f"Node {i}", "source")
        await visualizer.add_node(node)
    
    # Measure render time
    start_time = time.time()
    figure = await visualizer.render()
    render_time = time.time() - start_time
    
    assert render_time < 30  # Should render within 30 seconds
    await visualizer.stop()
```

## Examples

Complete examples are available in the `examples/` directory:

- `advanced_visualization_example.py` - Comprehensive demo
- `complete_visualization_integration.py` - Full integration example
- `3d_visualization_example.py` - 3D visualization focus
- `dashboard_example.py` - Dashboard building
- `mobile_ui_example.py` - Mobile interface
- `export_example.py` - Export functionality

## Dependencies

### Required

```
plotly>=5.17.0
dash>=2.14.0
networkx>=3.2.0
pandas>=2.1.0
numpy>=1.24.0
```

### Optional

```
pillow>=10.0.0          # Image processing
reportlab>=4.0.0        # PDF generation
openpyxl>=3.1.0         # Excel export
redis>=5.0.0            # Caching
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Install visualization requirements
2. **Memory Issues**: Reduce graph complexity or enable batching
3. **Slow Rendering**: Disable physics or reduce node count
4. **Export Failures**: Check disk space and reduce quality

### Debug Mode

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable component debug modes
visualizer = create_3d_visualizer(ThreeDConfig(debug_mode=True))
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This module is part of DataLineagePy and is licensed under the MIT License.

## Support

- Documentation: [Full Documentation](https://datalineagepy.readthedocs.io)
- Issues: [GitHub Issues](https://github.com/DataLineagePy/issues)
- Community: [Discord Server](https://discord.gg/datalineagepy)
