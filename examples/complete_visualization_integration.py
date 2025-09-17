"""
Complete Advanced Visualization Integration Example
Demonstrates all visualization components working together in a real-world scenario
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import visualization components
from datalineagepy.visualization import (
    create_3d_visualizer,
    create_dashboard_builder,
    create_mobile_renderer,
    create_export_manager,
    Node3D,
    Edge3D,
    WidgetConfig,
    MobileCard,
    MobileListItem,
    ExportConfig,
    ExportFormat,
    ExportQuality,
    ExportSize,
    WidgetType,
    ChartType,
    ThreeDConfig,
    DashboardConfig,
    MobileConfig,
    Camera3DMode,
    Physics3DMode,
    LayoutType,
    MobileViewType
)


class CompleteVisualizationDemo:
    """Comprehensive demo of all advanced visualization features."""
    
    def __init__(self):
        self.components = {}
        self.sample_data = self._generate_sample_data()
        self.export_dir = Path("demo_exports")
        self.export_dir.mkdir(exist_ok=True)
    
    def _generate_sample_data(self):
        """Generate realistic sample lineage data."""
        return {
            "nodes": [
                {"id": "raw_data", "label": "Raw Customer Data", "type": "source", "size": 25},
                {"id": "cleaner", "label": "Data Cleaner", "type": "transform", "size": 20},
                {"id": "validator", "label": "Data Validator", "type": "transform", "size": 18},
                {"id": "enricher", "label": "ML Enricher", "type": "transform", "size": 22},
                {"id": "analytics_db", "label": "Analytics DB", "type": "sink", "size": 30},
                {"id": "dashboard", "label": "Executive Dashboard", "type": "sink", "size": 25},
                {"id": "ml_model", "label": "Prediction Model", "type": "model", "size": 28},
                {"id": "api_service", "label": "API Service", "type": "service", "size": 20}
            ],
            "edges": [
                {"source": "raw_data", "target": "cleaner", "type": "data_flow"},
                {"source": "cleaner", "target": "validator", "type": "data_flow"},
                {"source": "validator", "target": "enricher", "type": "data_flow"},
                {"source": "enricher", "target": "analytics_db", "type": "data_flow"},
                {"source": "analytics_db", "target": "dashboard", "type": "data_flow"},
                {"source": "enricher", "target": "ml_model", "type": "training"},
                {"source": "ml_model", "target": "api_service", "type": "inference"}
            ]
        }
    
    async def initialize_components(self):
        """Initialize all visualization components."""
        logger.info("Initializing visualization components...")
        
        # 3D Visualizer
        self.components['3d'] = create_3d_visualizer(ThreeDConfig(
            width=1200,
            height=800,
            camera_mode=Camera3DMode.ORBIT,
            physics_enabled=True,
            physics_mode=Physics3DMode.FORCE_DIRECTED,
            clustering_enabled=True,
            animation_enabled=True
        ))
        
        # Dashboard Builder
        self.components['dashboard'] = create_dashboard_builder(DashboardConfig(
            title="Data Lineage Analytics Dashboard",
            theme="dark",
            layout_type=LayoutType.GRID,
            grid_columns=12,
            auto_refresh=True,
            refresh_interval=30,
            real_time_updates=True
        ))
        
        # Mobile UI Renderer
        self.components['mobile'] = create_mobile_renderer(MobileConfig(
            touch_enabled=True,
            navigation_type="bottom_tabs",
            theme="dark",
            performance_mode=True,
            offline_support=True
        ))
        
        # Export Manager
        self.components['export'] = create_export_manager(str(self.export_dir))
        
        # Start async components
        await self.components['3d'].start()
        await self.components['export'].start()
        
        logger.info("All components initialized successfully")
    
    async def setup_3d_visualization(self):
        """Setup 3D visualization with sample data."""
        logger.info("Setting up 3D visualization...")
        
        visualizer = self.components['3d']
        
        # Add nodes with different colors by type
        type_colors = {
            "source": "#4CAF50",
            "transform": "#2196F3",
            "sink": "#FF9800",
            "model": "#9C27B0",
            "service": "#F44336"
        }
        
        for node_data in self.sample_data["nodes"]:
            node = Node3D(
                id=node_data["id"],
                label=node_data["label"],
                node_type=node_data["type"],
                size=node_data["size"],
                color=type_colors.get(node_data["type"], "#666666")
            )
            await visualizer.add_node(node)
        
        # Add edges
        for edge_data in self.sample_data["edges"]:
            edge = Edge3D(
                source_id=edge_data["source"],
                target_id=edge_data["target"],
                edge_type=edge_data["type"],
                width=2.0,
                color="#666666"
            )
            await visualizer.add_edge(edge)
        
        # Start physics simulation
        await visualizer.start_physics()
        
        # Create layers for better organization
        await visualizer.create_layer("sources", z_position=0)
        await visualizer.create_layer("transforms", z_position=150)
        await visualizer.create_layer("sinks", z_position=300)
        
        logger.info("3D visualization setup complete")
    
    async def build_dashboard(self):
        """Build comprehensive dashboard with multiple widgets."""
        logger.info("Building dashboard...")
        
        dashboard = self.components['dashboard']
        
        # Main lineage graph widget
        lineage_widget = WidgetConfig(
            id="main_lineage",
            title="Data Lineage Graph",
            widget_type=WidgetType.LINEAGE_GRAPH,
            position=(0, 0),
            size=(8, 6),
            interactive=True,
            refresh_interval=60
        )
        
        # KPI metrics widget
        kpi_widget = WidgetConfig(
            id="kpi_metrics",
            title="Pipeline Metrics",
            widget_type=WidgetType.KPI_CARD,
            position=(8, 0),
            size=(4, 3),
            chart_config={
                "metrics": [
                    {"name": "Total Nodes", "value": len(self.sample_data["nodes"]), "trend": "+2"},
                    {"name": "Active Pipelines", "value": 3, "trend": "+1"},
                    {"name": "Data Quality", "value": "98.7%", "trend": "+0.2%"},
                    {"name": "Avg Processing", "value": "1.8s", "trend": "-0.3s"}
                ]
            }
        )
        
        # Performance chart widget
        performance_widget = WidgetConfig(
            id="performance_chart",
            title="Throughput Trends",
            widget_type=WidgetType.CHART,
            chart_type=ChartType.LINE,
            position=(0, 6),
            size=(6, 4),
            chart_config={
                "data": {
                    "x": ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00"],
                    "y": [1200, 1100, 1500, 1800, 1600, 1300]
                },
                "title": "Records/Hour",
                "xaxis_title": "Time",
                "yaxis_title": "Records"
            }
        )
        
        # Data quality heatmap
        heatmap_widget = WidgetConfig(
            id="quality_heatmap",
            title="Data Quality Heatmap",
            widget_type=WidgetType.HEATMAP,
            position=(6, 6),
            size=(6, 4),
            chart_config={
                "data": {
                    "z": [[95, 98, 92], [97, 99, 94], [93, 96, 98]],
                    "x": ["Completeness", "Accuracy", "Consistency"],
                    "y": ["Raw Data", "Cleaned", "Enriched"]
                }
            }
        )
        
        # Timeline widget
        timeline_widget = WidgetConfig(
            id="pipeline_timeline",
            title="Pipeline Timeline",
            widget_type=WidgetType.TIMELINE,
            position=(8, 3),
            size=(4, 3),
            chart_config={
                "events": [
                    {"time": "09:00", "event": "Data ingestion started"},
                    {"time": "09:15", "event": "Cleaning completed"},
                    {"time": "09:30", "event": "Validation passed"},
                    {"time": "09:45", "event": "ML enrichment done"}
                ]
            }
        )
        
        # Add all widgets
        widgets = [lineage_widget, kpi_widget, performance_widget, heatmap_widget, timeline_widget]
        for widget in widgets:
            await dashboard.add_widget(widget)
        
        logger.info("Dashboard built successfully")
    
    async def create_mobile_views(self):
        """Create mobile-optimized views."""
        logger.info("Creating mobile views...")
        
        mobile = self.components['mobile']
        
        # Card view for pipelines
        pipeline_cards = [
            MobileCard(
                id="customer_pipeline",
                title="Customer Data Pipeline",
                subtitle="Active • 1.2M records/day",
                content="Real-time customer data processing with ML enrichment",
                action_url="/pipeline/customer",
                metadata={"status": "active", "success_rate": 99.8}
            ),
            MobileCard(
                id="analytics_pipeline",
                title="Analytics Pipeline",
                subtitle="Scheduled • Daily at 2 AM",
                content="Batch analytics processing for executive dashboards",
                action_url="/pipeline/analytics",
                metadata={"status": "scheduled", "last_run": "success"}
            ),
            MobileCard(
                id="ml_pipeline",
                title="ML Training Pipeline",
                subtitle="Running • 45% complete",
                content="Model training and validation pipeline",
                action_url="/pipeline/ml",
                metadata={"status": "running", "progress": 0.45}
            )
        ]
        
        self.mobile_card_html = await mobile.render_card_view(
            pipeline_cards,
            title="Data Pipelines",
            enable_search=True,
            enable_filter=True,
            enable_pagination=True
        )
        
        # List view for lineage items
        lineage_items = [
            MobileListItem(
                id="raw_to_clean",
                title="Raw Data → Cleaning",
                subtitle="Data Flow • 99.5% success",
                description="Customer data ingestion and cleaning pipeline",
                icon="arrow-right",
                action_url="/lineage/raw-clean"
            ),
            MobileListItem(
                id="clean_to_validate",
                title="Cleaning → Validation",
                subtitle="Data Flow • 98.9% success",
                description="Data validation and quality checks",
                icon="check-circle",
                action_url="/lineage/clean-validate"
            ),
            MobileListItem(
                id="validate_to_enrich",
                title="Validation → Enrichment",
                subtitle="ML Pipeline • Active",
                description="Machine learning data enrichment",
                icon="cpu",
                action_url="/lineage/validate-enrich"
            )
        ]
        
        self.mobile_list_html = await mobile.render_list_view(
            lineage_items,
            title="Data Lineage",
            enable_search=True,
            enable_grouping=True,
            group_by="subtitle"
        )
        
        # Simplified graph view for mobile
        self.mobile_graph_html = await mobile.render_graph_view(
            nodes=self.sample_data["nodes"],
            edges=self.sample_data["edges"],
            title="Lineage Graph",
            simplified=True,
            max_nodes=50,
            enable_clustering=True,
            touch_interactions=True
        )
        
        logger.info("Mobile views created successfully")
    
    async def export_all_visualizations(self):
        """Export all visualizations in multiple formats."""
        logger.info("Starting comprehensive export process...")
        
        exporter = self.components['export']
        
        # Render 3D visualization
        figure_3d = await self.components['3d'].render()
        
        # Render dashboard
        dashboard_html = await self.components['dashboard'].render()
        
        # Export configurations for different use cases
        export_configs = [
            # High-quality PNG for presentations
            ExportConfig(
                format=ExportFormat.PNG,
                quality=ExportQuality.HIGH,
                size=ExportSize.LARGE,
                filename="lineage_3d_presentation",
                include_title=True,
                include_metadata=True
            ),
            # PDF for reports
            ExportConfig(
                format=ExportFormat.PDF,
                quality=ExportQuality.HIGH,
                size=ExportSize.PRINT_LETTER,
                filename="lineage_report",
                include_title=True,
                include_metadata=True
            ),
            # SVG for web
            ExportConfig(
                format=ExportFormat.SVG,
                quality=ExportQuality.MEDIUM,
                filename="lineage_web",
                include_title=False
            ),
            # JSON for data exchange
            ExportConfig(
                format=ExportFormat.JSON,
                filename="lineage_data",
                include_metadata=True
            )
        ]
        
        # Export 3D visualization in multiple formats
        export_jobs = []
        for config in export_configs:
            if config.format in [ExportFormat.PNG, ExportFormat.PDF, ExportFormat.SVG]:
                job_id = await exporter.export_visualization(
                    figure_3d,
                    config,
                    metadata={
                        "title": "Data Lineage 3D Visualization",
                        "description": "Interactive 3D view of data pipeline",
                        "generated_at": datetime.now().isoformat(),
                        "node_count": len(self.sample_data["nodes"]),
                        "edge_count": len(self.sample_data["edges"])
                    }
                )
                export_jobs.append(job_id)
        
        # Export dashboard as HTML
        dashboard_job = await exporter.export_dashboard(
            dashboard_html,
            ExportConfig(
                format=ExportFormat.HTML,
                filename="dashboard_interactive",
                include_metadata=True
            ),
            metadata={
                "title": "Data Lineage Dashboard",
                "description": "Interactive dashboard with metrics and charts",
                "generated_at": datetime.now().isoformat()
            }
        )
        export_jobs.append(dashboard_job)
        
        # Export mobile views
        mobile_exports = [
            (self.mobile_card_html, "mobile_cards"),
            (self.mobile_list_html, "mobile_list"),
            (self.mobile_graph_html, "mobile_graph")
        ]
        
        for html_content, filename in mobile_exports:
            job_id = await exporter.export_dashboard(
                html_content,
                ExportConfig(
                    format=ExportFormat.HTML,
                    filename=filename,
                    include_metadata=True
                )
            )
            export_jobs.append(job_id)
        
        # Wait for all exports to complete
        logger.info(f"Waiting for {len(export_jobs)} export jobs to complete...")
        completed_exports = []
        
        for job_id in export_jobs:
            job = await exporter.wait_for_job(job_id, timeout=120)
            if job.status == "completed":
                completed_exports.append(job.output_path)
                logger.info(f"Export completed: {job.output_path}")
            else:
                logger.error(f"Export failed: {job.error}")
        
        # Create batch export for archive
        batch_items = [
            {
                "figure": figure_3d,
                "metadata": {"title": "3D Visualization - Archive"},
                "config_overrides": {"format": ExportFormat.PNG, "quality": ExportQuality.MEDIUM}
            },
            {
                "data": self.sample_data,
                "metadata": {"title": "Lineage Data - Archive"},
                "config_overrides": {"format": ExportFormat.JSON}
            }
        ]
        
        batch_config = ExportConfig(
            format=ExportFormat.ZIP,
            filename="lineage_archive",
            include_metadata=True
        )
        
        batch_jobs = await exporter.batch_export(batch_items, batch_config)
        
        for job_id in batch_jobs:
            job = await exporter.wait_for_job(job_id, timeout=60)
            if job.status == "completed":
                completed_exports.append(job.output_path)
                logger.info(f"Batch export completed: {job.output_path}")
        
        logger.info(f"Export process complete. {len(completed_exports)} files exported.")
        return completed_exports
    
    async def demonstrate_real_time_updates(self):
        """Demonstrate real-time update capabilities."""
        logger.info("Demonstrating real-time updates...")
        
        dashboard = self.components['dashboard']
        visualizer_3d = self.components['3d']
        
        # Enable real-time updates
        await dashboard.enable_real_time_updates()
        
        # Simulate real-time data updates
        for i in range(5):
            # Update metrics
            await dashboard.update_widget_data(
                "kpi_metrics",
                {
                    "metrics": [
                        {"name": "Total Nodes", "value": len(self.sample_data["nodes"]) + i, "trend": f"+{i}"},
                        {"name": "Active Pipelines", "value": 3 + (i % 2), "trend": f"+{i % 2}"},
                        {"name": "Data Quality", "value": f"{98.7 + (i * 0.1):.1f}%", "trend": f"+{i * 0.1:.1f}%"}
                    ]
                }
            )
            
            # Add new node to 3D visualization
            new_node = Node3D(
                id=f"dynamic_node_{i}",
                label=f"Dynamic Node {i}",
                node_type="dynamic",
                size=15.0,
                color="#00FF00"
            )
            await visualizer_3d.add_node(new_node)
            
            # Broadcast update
            await dashboard.broadcast_update({
                "type": "node_added",
                "node_id": f"dynamic_node_{i}",
                "timestamp": datetime.now().isoformat()
            })
            
            logger.info(f"Real-time update {i+1}/5 completed")
            await asyncio.sleep(2)
        
        logger.info("Real-time updates demonstration complete")
    
    async def cleanup(self):
        """Cleanup all components."""
        logger.info("Cleaning up components...")
        
        # Stop async components
        if '3d' in self.components:
            await self.components['3d'].stop()
        
        if 'export' in self.components:
            await self.components['export'].stop()
        
        logger.info("Cleanup complete")
    
    async def run_complete_demo(self):
        """Run the complete visualization demonstration."""
        try:
            logger.info("Starting Complete Advanced Visualization Demo")
            
            # Initialize all components
            await self.initialize_components()
            
            # Setup visualizations
            await self.setup_3d_visualization()
            await self.build_dashboard()
            await self.create_mobile_views()
            
            # Demonstrate real-time updates
            await self.demonstrate_real_time_updates()
            
            # Export everything
            exported_files = await self.export_all_visualizations()
            
            # Display results
            logger.info("=== DEMO COMPLETE ===")
            logger.info(f"Exported files: {len(exported_files)}")
            for file_path in exported_files:
                logger.info(f"  - {file_path}")
            
            # Get final statistics
            export_stats = self.components['export'].get_stats()
            logger.info(f"Export Statistics: {export_stats}")
            
            performance_stats = await self.components['3d'].get_performance_stats()
            logger.info(f"3D Performance: {performance_stats}")
            
            logger.info("Demo completed successfully!")
            
        except Exception as e:
            logger.error(f"Demo failed: {e}")
            raise
        
        finally:
            await self.cleanup()


async def main():
    """Main entry point for the demo."""
    demo = CompleteVisualizationDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    asyncio.run(main())
