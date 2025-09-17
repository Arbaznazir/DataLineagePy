"""
Advanced Visualization Example for DataLineagePy

This example demonstrates the comprehensive visualization capabilities including:
- 3D visualization with physics simulation
- Interactive dashboard builder
- Mobile-optimized UI components
- Export manager for multiple formats
- Integration with real-time data updates
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

# DataLineagePy imports
from datalineagepy.core.lineage_tracker import LineageTracker
from datalineagepy.core.lineage_node import LineageNode, NodeType
from datalineagepy.core.lineage_edge import LineageEdge, EdgeType

# Visualization imports
from datalineagepy.visualization import (
    # 3D visualization
    ThreeDVisualizer,
    ThreeDConfig,
    Node3D,
    Edge3D,
    Camera3DMode,
    Physics3DMode,
    create_3d_visualizer,
    
    # Dashboard builder
    DashboardBuilder,
    DashboardConfig,
    WidgetConfig,
    WidgetType,
    ChartType,
    LayoutType,
    create_dashboard_builder,
    
    # Mobile UI
    MobileRenderer,
    MobileConfig,
    MobileCard,
    MobileListItem,
    MobileViewType,
    GestureType,
    ScreenSize,
    create_mobile_renderer,
    
    # Export manager
    ExportManager,
    ExportConfig,
    ExportFormat,
    ExportQuality,
    ExportSize,
    create_export_manager,
    
    # Interactive graph
    InteractiveGraphVisualizer,
    GraphNode,
    GraphEdge,
    NodeType as GraphNodeType,
    EdgeType as GraphEdgeType,
    GraphLayout,
    create_interactive_graph,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AdvancedVisualizationDemo:
    """Comprehensive demonstration of advanced visualization features."""
    
    def __init__(self):
        self.tracker = LineageTracker()
        self.export_manager = None
        self.dashboard_builder = None
        self.mobile_renderer = None
        self.three_d_visualizer = None
        self.interactive_graph = None
        
        # Sample data
        self.sample_nodes = []
        self.sample_edges = []
        self.sample_metrics = {}
        
    async def setup(self):
        """Initialize all visualization components."""
        logger.info("Setting up advanced visualization demo...")
        
        # Create sample data
        await self._create_sample_data()
        
        # Initialize export manager
        self.export_manager = create_export_manager("demo_exports")
        await self.export_manager.start()
        
        # Initialize dashboard builder
        dashboard_config = DashboardConfig(
            title="DataLineage Analytics Dashboard",
            theme="dark",
            layout_type=LayoutType.GRID,
            grid_columns=12,
            auto_refresh=True,
            refresh_interval=30,
            real_time_updates=True,
            mobile_responsive=True,
            export_enabled=True
        )
        self.dashboard_builder = create_dashboard_builder(dashboard_config)
        
        # Initialize mobile renderer
        mobile_config = MobileConfig(
            screen_size=ScreenSize.MOBILE,
            touch_enabled=True,
            navigation_type="bottom_tabs",
            theme="dark",
            performance_mode=True,
            offline_support=True
        )
        self.mobile_renderer = create_mobile_renderer(mobile_config)
        
        # Initialize 3D visualizer
        three_d_config = ThreeDConfig(
            width=1200,
            height=800,
            camera_mode=Camera3DMode.ORBIT,
            physics_enabled=True,
            physics_mode=Physics3DMode.FORCE_DIRECTED,
            clustering_enabled=True,
            layer_separation=150.0,
            animation_enabled=True
        )
        self.three_d_visualizer = create_3d_visualizer(three_d_config)
        
        # Initialize interactive graph
        self.interactive_graph = create_interactive_graph(
            width=1200,
            height=800,
            layout=GraphLayout.FORCE_DIRECTED,
            enable_physics=True,
            enable_clustering=True,
            real_time_updates=True
        )
        
        logger.info("Advanced visualization demo setup complete")
    
    async def _create_sample_data(self):
        """Create sample lineage data for demonstration."""
        # Create sample nodes
        node_configs = [
            ("raw_data", "Raw Customer Data", NodeType.SOURCE),
            ("cleaned_data", "Cleaned Customer Data", NodeType.TRANSFORMATION),
            ("aggregated_data", "Customer Aggregates", NodeType.TRANSFORMATION),
            ("ml_features", "ML Feature Set", NodeType.TRANSFORMATION),
            ("model_training", "Model Training", NodeType.PROCESS),
            ("trained_model", "Trained Model", NodeType.MODEL),
            ("predictions", "Customer Predictions", NodeType.OUTPUT),
            ("dashboard", "Customer Dashboard", NodeType.SINK),
            ("api_endpoint", "Prediction API", NodeType.SINK),
        ]
        
        for node_id, name, node_type in node_configs:
            node = LineageNode(
                id=node_id,
                name=name,
                node_type=node_type,
                metadata={
                    "created_at": datetime.utcnow().isoformat(),
                    "owner": "data_team",
                    "environment": "production",
                    "tags": ["customer", "ml", "analytics"]
                }
            )
            self.sample_nodes.append(node)
            self.tracker.add_node(node)
        
        # Create sample edges
        edge_configs = [
            ("raw_data", "cleaned_data", EdgeType.TRANSFORMATION),
            ("cleaned_data", "aggregated_data", EdgeType.TRANSFORMATION),
            ("cleaned_data", "ml_features", EdgeType.TRANSFORMATION),
            ("ml_features", "model_training", EdgeType.PROCESS),
            ("model_training", "trained_model", EdgeType.CREATION),
            ("trained_model", "predictions", EdgeType.INFERENCE),
            ("aggregated_data", "dashboard", EdgeType.VISUALIZATION),
            ("predictions", "api_endpoint", EdgeType.SERVING),
        ]
        
        for source_id, target_id, edge_type in edge_configs:
            edge = LineageEdge(
                source_id=source_id,
                target_id=target_id,
                edge_type=edge_type,
                metadata={
                    "created_at": datetime.utcnow().isoformat(),
                    "confidence": 0.95,
                    "data_volume": "1M records/day"
                }
            )
            self.sample_edges.append(edge)
            self.tracker.add_edge(edge)
        
        # Create sample metrics
        self.sample_metrics = {
            "total_nodes": len(self.sample_nodes),
            "total_edges": len(self.sample_edges),
            "data_freshness": "5 minutes",
            "pipeline_health": "healthy",
            "last_updated": datetime.utcnow().isoformat(),
            "processing_time": "2.3 seconds",
            "error_rate": "0.1%",
            "throughput": "1000 records/second"
        }
    
    async def demo_3d_visualization(self):
        """Demonstrate 3D visualization capabilities."""
        logger.info("Demonstrating 3D visualization...")
        
        # Convert lineage nodes to 3D nodes
        nodes_3d = []
        for node in self.sample_nodes:
            node_3d = Node3D(
                id=node.id,
                label=node.name,
                node_type=node.node_type.value,
                size=20.0,
                color=self._get_node_color(node.node_type),
                metadata=node.metadata
            )
            nodes_3d.append(node_3d)
        
        # Convert lineage edges to 3D edges
        edges_3d = []
        for edge in self.sample_edges:
            edge_3d = Edge3D(
                source_id=edge.source_id,
                target_id=edge.target_id,
                edge_type=edge.edge_type.value,
                width=2.0,
                color="#666666",
                metadata=edge.metadata
            )
            edges_3d.append(edge_3d)
        
        # Start 3D visualizer
        await self.three_d_visualizer.start()
        
        # Add nodes and edges
        for node in nodes_3d:
            await self.three_d_visualizer.add_node(node)
        
        for edge in edges_3d:
            await self.three_d_visualizer.add_edge(edge)
        
        # Start physics simulation
        await self.three_d_visualizer.start_physics()
        
        # Generate 3D visualization
        figure = await self.three_d_visualizer.render()
        
        # Export 3D visualization
        export_config = ExportConfig(\n            format=ExportFormat.HTML,\n            quality=ExportQuality.HIGH,\n            size=ExportSize.LARGE,\n            filename="3d_lineage_visualization",\n            include_title=True,\n            include_metadata=True\n        )\n        \n        job_id = await self.export_manager.export_visualization(\n            figure,\n            export_config,\n            metadata={\n                "title": "3D Data Lineage Visualization",\n                "description": "Interactive 3D view of data pipeline",\n                "nodes": len(nodes_3d),\n                "edges": len(edges_3d),\n                "generated_at": datetime.utcnow().isoformat()\n            }\n        )\n        \n        # Wait for export to complete\n        job = await self.export_manager.wait_for_job(job_id)\n        logger.info(f"3D visualization exported to: {job.output_path}")\n        \n        return figure\n    \n    async def demo_dashboard_builder(self):\n        """Demonstrate dashboard builder capabilities."""\n        logger.info("Demonstrating dashboard builder...")\n        \n        # Create lineage graph widget\n        lineage_widget = WidgetConfig(\n            id="lineage_graph",\n            title="Data Lineage Graph",\n            widget_type=WidgetType.LINEAGE_GRAPH,\n            position=(0, 0),\n            size=(8, 6),\n            data_source="lineage_tracker",\n            refresh_interval=30,\n            interactive=True\n        )\n        \n        # Create metrics widget\n        metrics_widget = WidgetConfig(\n            id="pipeline_metrics",\n            title="Pipeline Metrics",\n            widget_type=WidgetType.KPI_CARD,\n            position=(8, 0),\n            size=(4, 3),\n            data_source="metrics",\n            chart_config={\n                "metrics": [\n                    {"name": "Total Nodes", "value": self.sample_metrics["total_nodes"]},\n                    {"name": "Total Edges", "value": self.sample_metrics["total_edges"]},\n                    {"name": "Pipeline Health", "value": self.sample_metrics["pipeline_health"]},\n                    {"name": "Error Rate", "value": self.sample_metrics["error_rate"]}\n                ]\n            }\n        )\n        \n        # Create timeline widget\n        timeline_widget = WidgetConfig(\n            id="pipeline_timeline",\n            title="Pipeline Timeline",\n            widget_type=WidgetType.TIMELINE,\n            position=(8, 3),\n            size=(4, 3),\n            data_source="timeline",\n            chart_config={\n                "events": [\n                    {"time": "2024-01-01T10:00:00Z", "event": "Pipeline Created"},\n                    {"time": "2024-01-01T10:30:00Z", "event": "Data Ingestion Started"},\n                    {"time": "2024-01-01T11:00:00Z", "event": "Model Training Completed"},\n                    {"time": "2024-01-01T11:30:00Z", "event": "Dashboard Updated"}\n                ]\n            }\n        )\n        \n        # Create data quality widget\n        quality_widget = WidgetConfig(\n            id="data_quality",\n            title="Data Quality Metrics",\n            widget_type=WidgetType.CHART,\n            position=(0, 6),\n            size=(6, 4),\n            chart_type=ChartType.BAR,\n            data_source="quality_metrics",\n            chart_config={\n                "data": {\n                    "x": ["Completeness", "Accuracy", "Consistency", "Timeliness"],\n                    "y": [95, 98, 92, 88]\n                },\n                "title": "Data Quality Scores (%)",\n                "xaxis_title": "Quality Dimension",\n                "yaxis_title": "Score (%)"\n            }\n        )\n        \n        # Create performance widget\n        performance_widget = WidgetConfig(\n            id="performance_trends",\n            title="Performance Trends",\n            widget_type=WidgetType.CHART,\n            position=(6, 6),\n            size=(6, 4),\n            chart_type=ChartType.LINE,\n            data_source="performance_metrics",\n            chart_config={\n                "data": {\n                    "x": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],\n                    "y": [1200, 1100, 1500, 1800, 1600, 1300]\n                },\n                "title": "Throughput (records/hour)",\n                "xaxis_title": "Time",\n                "yaxis_title": "Records/Hour"\n            }\n        )\n        \n        # Add widgets to dashboard\n        await self.dashboard_builder.add_widget(lineage_widget)\n        await self.dashboard_builder.add_widget(metrics_widget)\n        await self.dashboard_builder.add_widget(timeline_widget)\n        await self.dashboard_builder.add_widget(quality_widget)\n        await self.dashboard_builder.add_widget(performance_widget)\n        \n        # Generate dashboard HTML\n        dashboard_html = await self.dashboard_builder.render()\n        \n        # Export dashboard\n        export_config = ExportConfig(\n            format=ExportFormat.HTML,\n            quality=ExportQuality.HIGH,\n            filename="lineage_dashboard",\n            include_title=True,\n            include_metadata=True\n        )\n        \n        job_id = await self.export_manager.export_dashboard(\n            dashboard_html,\n            export_config,\n            metadata={\n                "title": "Data Lineage Analytics Dashboard",\n                "description": "Comprehensive dashboard for data pipeline monitoring",\n                "widgets": len(self.dashboard_builder.widgets),\n                "generated_at": datetime.utcnow().isoformat()\n            }\n        )\n        \n        # Wait for export to complete\n        job = await self.export_manager.wait_for_job(job_id)\n        logger.info(f"Dashboard exported to: {job.output_path}")\n        \n        return dashboard_html\n    \n    async def demo_mobile_ui(self):\n        """Demonstrate mobile UI capabilities."""\n        logger.info("Demonstrating mobile UI...")\n        \n        # Create mobile cards for nodes\n        mobile_cards = []\n        for node in self.sample_nodes:\n            card = MobileCard(\n                id=node.id,\n                title=node.name,\n                subtitle=node.node_type.value,\n                content=f"Owner: {node.metadata.get('owner', 'Unknown')}",\n                image_url=None,\n                action_url=f"/node/{node.id}",\n                metadata=node.metadata\n            )\n            mobile_cards.append(card)\n        \n        # Create mobile list items for edges\n        mobile_list_items = []\n        for edge in self.sample_edges:\n            item = MobileListItem(\n                id=f"{edge.source_id}-{edge.target_id}",\n                title=f"{edge.source_id} → {edge.target_id}",\n                subtitle=edge.edge_type.value,\n                description=f"Confidence: {edge.metadata.get('confidence', 'Unknown')}",\n                icon="arrow-right",\n                action_url=f"/edge/{edge.source_id}/{edge.target_id}",\n                metadata=edge.metadata\n            )\n            mobile_list_items.append(item)\n        \n        # Render mobile views\n        card_view_html = await self.mobile_renderer.render_card_view(\n            mobile_cards,\n            title="Data Sources",\n            enable_search=True,\n            enable_filter=True\n        )\n        \n        list_view_html = await self.mobile_renderer.render_list_view(\n            mobile_list_items,\n            title="Data Connections",\n            enable_search=True,\n            enable_pagination=True\n        )\n        \n        # Create simplified graph for mobile\n        graph_html = await self.mobile_renderer.render_graph_view(\n            self.sample_nodes,\n            self.sample_edges,\n            title="Lineage Graph",\n            simplified=True\n        )\n        \n        # Export mobile views\n        mobile_exports = [\n            ("mobile_card_view", card_view_html),\n            ("mobile_list_view", list_view_html),\n            ("mobile_graph_view", graph_html)\n        ]\n        \n        export_jobs = []\n        for filename, html_content in mobile_exports:\n            export_config = ExportConfig(\n                format=ExportFormat.HTML,\n                quality=ExportQuality.HIGH,\n                filename=filename,\n                include_title=True\n            )\n            \n            job_id = await self.export_manager.export_dashboard(\n                html_content,\n                export_config,\n                metadata={\n                    "title": f"Mobile {filename.replace('_', ' ').title()}",\n                    "description": "Mobile-optimized data lineage view",\n                    "generated_at": datetime.utcnow().isoformat()\n                }\n            )\n            export_jobs.append(job_id)\n        \n        # Wait for all exports to complete\n        for job_id in export_jobs:\n            job = await self.export_manager.wait_for_job(job_id)\n            logger.info(f"Mobile view exported to: {job.output_path}")\n        \n        return {\n            "card_view": card_view_html,\n            "list_view": list_view_html,\n            "graph_view": graph_html\n        }\n    \n    async def demo_batch_export(self):\n        """Demonstrate batch export capabilities."""\n        logger.info("Demonstrating batch export...")\n        \n        # Create interactive graph figure\n        graph_figure = await self.interactive_graph.create_figure(\n            self.sample_nodes,\n            self.sample_edges\n        )\n        \n        # Prepare batch export items\n        export_items = [\n            {\n                "figure": graph_figure,\n                "metadata": {\n                    "title": "Interactive Lineage Graph - PNG",\n                    "format": "PNG Image",\n                    "description": "High-resolution PNG export"\n                },\n                "config_overrides": {"format": ExportFormat.PNG}\n            },\n            {\n                "figure": graph_figure,\n                "metadata": {\n                    "title": "Interactive Lineage Graph - SVG",\n                    "format": "SVG Vector",\n                    "description": "Scalable vector graphics export"\n                },\n                "config_overrides": {"format": ExportFormat.SVG}\n            },\n            {\n                "figure": graph_figure,\n                "metadata": {\n                    "title": "Interactive Lineage Graph - PDF",\n                    "format": "PDF Document",\n                    "description": "PDF document with metadata"\n                },\n                "config_overrides": {"format": ExportFormat.PDF}\n            },\n            {\n                "data": [node.__dict__ for node in self.sample_nodes],\n                "metadata": {\n                    "title": "Lineage Nodes Data",\n                    "format": "JSON Data",\n                    "description": "Node data in JSON format"\n                },\n                "config_overrides": {"format": ExportFormat.JSON}\n            }\n        ]\n        \n        # Base configuration for batch export\n        base_config = ExportConfig(\n            format=ExportFormat.PNG,  # Will be overridden\n            quality=ExportQuality.HIGH,\n            size=ExportSize.LARGE,\n            filename="batch_export",\n            include_title=True,\n            include_metadata=True\n        )\n        \n        # Execute batch export\n        job_ids = await self.export_manager.batch_export(export_items, base_config)\n        \n        # Wait for all jobs to complete\n        completed_jobs = []\n        for job_id in job_ids:\n            job = await self.export_manager.wait_for_job(job_id)\n            completed_jobs.append(job)\n            logger.info(f"Batch export completed: {job.output_path}")\n        \n        return completed_jobs\n    \n    def _get_node_color(self, node_type: NodeType) -> str:\n        """Get color for node type."""\n        color_map = {\n            NodeType.SOURCE: "#4CAF50",      # Green\n            NodeType.TRANSFORMATION: "#2196F3",  # Blue\n            NodeType.PROCESS: "#FF9800",     # Orange\n            NodeType.MODEL: "#9C27B0",       # Purple\n            NodeType.OUTPUT: "#F44336",      # Red\n            NodeType.SINK: "#607D8B"         # Blue Grey\n        }\n        return color_map.get(node_type, "#757575")\n    \n    async def run_demo(self):\n        """Run the complete advanced visualization demo."""\n        logger.info("Starting advanced visualization demo...")\n        \n        try:\n            # Setup all components\n            await self.setup()\n            \n            # Demonstrate 3D visualization\n            three_d_figure = await self.demo_3d_visualization()\n            \n            # Demonstrate dashboard builder\n            dashboard_html = await self.demo_dashboard_builder()\n            \n            # Demonstrate mobile UI\n            mobile_views = await self.demo_mobile_ui()\n            \n            # Demonstrate batch export\n            batch_jobs = await self.demo_batch_export()\n            \n            # Print summary\n            stats = self.export_manager.get_stats()\n            logger.info("\\n" + "="*50)\n            logger.info("ADVANCED VISUALIZATION DEMO COMPLETE")\n            logger.info("="*50)\n            logger.info(f"Total exports: {stats['total_exports']}")\n            logger.info(f"Successful exports: {stats['successful_exports']}")\n            logger.info(f"Failed exports: {stats['failed_exports']}")\n            logger.info(f"Total file size: {stats['total_file_size']} bytes")\n            logger.info(f"Average export time: {stats['average_export_time']:.2f} seconds")\n            logger.info("\\nExport formats used:")\n            for format_name, count in stats['export_formats'].items():\n                logger.info(f"  {format_name}: {count}")\n            logger.info("\\nGenerated files:")\n            logger.info("- 3D visualization (HTML)")\n            logger.info("- Interactive dashboard (HTML)")\n            logger.info("- Mobile card view (HTML)")\n            logger.info("- Mobile list view (HTML)")\n            logger.info("- Mobile graph view (HTML)")\n            logger.info("- Batch exports (PNG, SVG, PDF, JSON)")\n            logger.info("\\nAll files saved to: demo_exports/")\n            \n            return {\n                "3d_visualization": three_d_figure,\n                "dashboard": dashboard_html,\n                "mobile_views": mobile_views,\n                "batch_exports": batch_jobs,\n                "export_stats": stats\n            }\n            \n        except Exception as e:\n            logger.error(f"Demo failed: {e}")\n            raise\n        \n        finally:\n            # Cleanup\n            await self.cleanup()\n    \n    async def cleanup(self):\n        """Clean up resources."""\n        logger.info("Cleaning up resources...")\n        \n        if self.export_manager:\n            await self.export_manager.stop()\n        \n        if self.three_d_visualizer:\n            await self.three_d_visualizer.stop()\n        \n        logger.info("Cleanup complete")\n\n\nasync def main():\n    """Main function to run the advanced visualization demo."""\n    demo = AdvancedVisualizationDemo()\n    \n    try:\n        results = await demo.run_demo()\n        print("\\nDemo completed successfully!")\n        print("Check the 'demo_exports' directory for generated files.")\n        return results\n    \n    except Exception as e:\n        logger.error(f"Demo failed: {e}")\n        raise\n\n\nif __name__ == "__main__":\n    # Run the demo\n    asyncio.run(main())\n
