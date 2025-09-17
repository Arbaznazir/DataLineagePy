"""
Advanced Visualization Test Suite for DataLineagePy
Tests for 3D visualization, dashboard builder, mobile UI, and export manager
"""

import asyncio
import pytest
import tempfile
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Import visualization components
try:
    from datalineagepy.visualization import (
        create_3d_visualizer,
        create_dashboard_builder,
        create_mobile_renderer,
        create_export_manager,
        Node3D,
        Edge3D,
        WidgetConfig,
        MobileCard,
        ExportConfig,
        ExportFormat,
        ExportQuality,
        WidgetType,
        ThreeDConfig,
        DashboardConfig,
        MobileConfig
    )
except ImportError as e:
    pytest.skip(f"Visualization dependencies not available: {e}", allow_module_level=True)


class TestThreeDVisualizer:
    """Test suite for 3D visualization functionality."""
    
    @pytest.fixture
    async def visualizer(self):
        """Create a 3D visualizer instance for testing."""
        config = ThreeDConfig(
            width=800,
            height=600,
            physics_enabled=True,
            clustering_enabled=True
        )
        visualizer = create_3d_visualizer(config)
        await visualizer.start()
        yield visualizer
        await visualizer.stop()
    
    @pytest.mark.asyncio
    async def test_node_operations(self, visualizer):
        """Test adding, updating, and removing nodes."""
        # Add node
        node = Node3D(
            id="test_node",
            label="Test Node",
            node_type="source",
            size=10.0,
            color="#FF0000"
        )
        
        await visualizer.add_node(node)
        assert await visualizer.get_node_count() == 1
        
        # Update node
        updated_node = Node3D(
            id="test_node",
            label="Updated Node",
            node_type="source",
            size=15.0,
            color="#00FF00"
        )
        
        await visualizer.update_node(updated_node)
        retrieved_node = await visualizer.get_node("test_node")
        assert retrieved_node.label == "Updated Node"
        
        # Remove node
        await visualizer.remove_node("test_node")
        assert await visualizer.get_node_count() == 0
    
    @pytest.mark.asyncio
    async def test_edge_operations(self, visualizer):
        """Test adding, updating, and removing edges."""
        # Add nodes first
        node1 = Node3D("node1", "Node 1", "source")
        node2 = Node3D("node2", "Node 2", "target")
        
        await visualizer.add_node(node1)
        await visualizer.add_node(node2)
        
        # Add edge
        edge = Edge3D(
            source_id="node1",
            target_id="node2",
            edge_type="data_flow",
            width=2.0,
            color="#0000FF"
        )
        
        await visualizer.add_edge(edge)
        assert await visualizer.get_edge_count() == 1
        
        # Remove edge
        await visualizer.remove_edge("node1", "node2")
        assert await visualizer.get_edge_count() == 0
    
    @pytest.mark.asyncio
    async def test_physics_simulation(self, visualizer):
        """Test physics simulation functionality."""
        # Add nodes
        for i in range(5):
            node = Node3D(f"node_{i}", f"Node {i}", "source")
            await visualizer.add_node(node)
        
        # Start physics
        await visualizer.start_physics()
        assert visualizer.is_physics_running()
        
        # Stop physics
        await visualizer.stop_physics()
        assert not visualizer.is_physics_running()
    
    @pytest.mark.asyncio
    async def test_clustering(self, visualizer):
        """Test node clustering functionality."""
        # Add nodes of different types
        for i in range(3):
            await visualizer.add_node(Node3D(f"source_{i}", f"Source {i}", "source"))
            await visualizer.add_node(Node3D(f"transform_{i}", f"Transform {i}", "transform"))
        
        # Cluster by type
        await visualizer.cluster_nodes_by_type()
        clusters = await visualizer.get_clusters()
        
        assert len(clusters) == 2  # source and transform clusters
        assert "source" in clusters
        assert "transform" in clusters
    
    @pytest.mark.asyncio
    async def test_render(self, visualizer):
        """Test visualization rendering."""
        # Add sample data
        node = Node3D("test", "Test", "source")
        await visualizer.add_node(node)
        
        # Render
        figure = await visualizer.render()
        
        assert figure is not None
        assert hasattr(figure, 'data')
        assert hasattr(figure, 'layout')


class TestDashboardBuilder:
    """Test suite for dashboard builder functionality."""
    
    @pytest.fixture
    async def dashboard(self):
        """Create a dashboard builder instance for testing."""
        config = DashboardConfig(
            title="Test Dashboard",
            theme="dark",
            auto_refresh=False,
            real_time_updates=False
        )
        dashboard = create_dashboard_builder(config)
        yield dashboard
    
    @pytest.mark.asyncio
    async def test_widget_operations(self, dashboard):
        """Test adding, updating, and removing widgets."""
        # Add widget
        widget = WidgetConfig(
            id="test_widget",
            title="Test Widget",
            widget_type=WidgetType.CHART,
            position=(0, 0),
            size=(6, 4)
        )
        
        await dashboard.add_widget(widget)
        assert await dashboard.get_widget_count() == 1
        
        # Update widget
        updated_widget = WidgetConfig(
            id="test_widget",
            title="Updated Widget",
            widget_type=WidgetType.CHART,
            position=(0, 0),
            size=(8, 6)
        )
        
        await dashboard.update_widget(updated_widget)
        retrieved_widget = await dashboard.get_widget("test_widget")
        assert retrieved_widget.title == "Updated Widget"
        
        # Remove widget
        await dashboard.remove_widget("test_widget")
        assert await dashboard.get_widget_count() == 0
    
    @pytest.mark.asyncio
    async def test_dashboard_render(self, dashboard):
        """Test dashboard rendering."""
        # Add sample widget
        widget = WidgetConfig(
            id="sample",
            title="Sample Widget",
            widget_type=WidgetType.KPI_CARD,
            position=(0, 0),
            size=(4, 2)
        )
        
        await dashboard.add_widget(widget)
        
        # Render dashboard
        html = await dashboard.render()
        
        assert html is not None
        assert isinstance(html, str)
        assert "Sample Widget" in html
    
    @pytest.mark.asyncio
    async def test_real_time_updates(self, dashboard):
        """Test real-time update functionality."""
        # Enable real-time updates
        await dashboard.enable_real_time_updates()
        
        # Add widget
        widget = WidgetConfig(
            id="realtime_widget",
            title="Real-time Widget",
            widget_type=WidgetType.CHART,
            position=(0, 0),
            size=(6, 4)
        )
        
        await dashboard.add_widget(widget)
        
        # Update widget data
        await dashboard.update_widget_data(
            "realtime_widget",
            {"value": 42, "timestamp": datetime.now().isoformat()}
        )
        
        # Verify update
        widget_data = await dashboard.get_widget_data("realtime_widget")
        assert widget_data["value"] == 42


class TestMobileRenderer:
    """Test suite for mobile UI renderer functionality."""
    
    @pytest.fixture
    def mobile_renderer(self):
        """Create a mobile renderer instance for testing."""
        config = MobileConfig(
            touch_enabled=True,
            offline_support=True,
            performance_mode=True
        )
        return create_mobile_renderer(config)
    
    @pytest.mark.asyncio
    async def test_card_view_render(self, mobile_renderer):
        """Test mobile card view rendering."""
        cards = [
            MobileCard(
                id="card1",
                title="Test Card 1",
                subtitle="Test Subtitle",
                content="Test content for card 1",
                action_url="/test1"
            ),
            MobileCard(
                id="card2",
                title="Test Card 2",
                subtitle="Another Subtitle",
                content="Test content for card 2",
                action_url="/test2"
            )
        ]
        
        html = await mobile_renderer.render_card_view(
            cards,
            title="Test Cards",
            enable_search=True,
            enable_pagination=True
        )
        
        assert html is not None
        assert "Test Card 1" in html
        assert "Test Card 2" in html
        assert "Test Cards" in html
    
    @pytest.mark.asyncio
    async def test_list_view_render(self, mobile_renderer):
        """Test mobile list view rendering."""
        from datalineagepy.visualization import MobileListItem
        
        items = [
            MobileListItem(
                id="item1",
                title="List Item 1",
                subtitle="Subtitle 1",
                description="Description for item 1",
                icon="arrow-right"
            ),
            MobileListItem(
                id="item2",
                title="List Item 2",
                subtitle="Subtitle 2",
                description="Description for item 2",
                icon="cpu"
            )
        ]
        
        html = await mobile_renderer.render_list_view(
            items,
            title="Test List",
            enable_search=True,
            enable_grouping=False
        )
        
        assert html is not None
        assert "List Item 1" in html
        assert "List Item 2" in html
    
    @pytest.mark.asyncio
    async def test_graph_view_render(self, mobile_renderer):
        """Test mobile graph view rendering."""
        # Mock nodes and edges
        nodes = [
            {"id": "node1", "label": "Node 1", "type": "source"},
            {"id": "node2", "label": "Node 2", "type": "transform"}
        ]
        
        edges = [
            {"source": "node1", "target": "node2", "type": "data_flow"}
        ]
        
        html = await mobile_renderer.render_graph_view(
            nodes=nodes,
            edges=edges,
            title="Mobile Graph",
            simplified=True,
            max_nodes=50
        )
        
        assert html is not None
        assert "Mobile Graph" in html


class TestExportManager:
    """Test suite for export manager functionality."""
    
    @pytest.fixture
    async def export_manager(self):
        """Create an export manager instance for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = create_export_manager(temp_dir)
            await exporter.start()
            yield exporter
            await exporter.stop()
    
    @pytest.mark.asyncio
    async def test_export_formats(self, export_manager):
        """Test different export formats."""
        # Mock figure data
        mock_figure = Mock()
        mock_figure.to_dict.return_value = {"data": [], "layout": {}}
        
        # Test PNG export
        config = ExportConfig(
            format=ExportFormat.PNG,
            quality=ExportQuality.MEDIUM,
            filename="test_export"
        )
        
        with patch('plotly.io.write_image') as mock_write:
            job_id = await export_manager.export_visualization(mock_figure, config)
            job = await export_manager.wait_for_job(job_id, timeout=10)
            
            assert job.status == "completed"
            mock_write.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_batch_export(self, export_manager):
        """Test batch export functionality."""
        # Mock data
        mock_figure = Mock()
        mock_figure.to_dict.return_value = {"data": [], "layout": {}}
        
        export_items = [
            {
                "figure": mock_figure,
                "metadata": {"title": "Export 1"},
                "config_overrides": {"format": ExportFormat.PNG}
            },
            {
                "figure": mock_figure,
                "metadata": {"title": "Export 2"},
                "config_overrides": {"format": ExportFormat.SVG}
            }
        ]
        
        base_config = ExportConfig(
            quality=ExportQuality.HIGH,
            filename="batch_export"
        )
        
        with patch('plotly.io.write_image'), patch('plotly.io.write_html'):
            job_ids = await export_manager.batch_export(export_items, base_config)
            
            assert len(job_ids) == 2
            
            # Wait for all jobs
            for job_id in job_ids:
                job = await export_manager.wait_for_job(job_id, timeout=10)
                assert job.status == "completed"
    
    @pytest.mark.asyncio
    async def test_export_statistics(self, export_manager):
        """Test export statistics tracking."""
        # Get initial stats
        initial_stats = export_manager.get_stats()
        
        # Mock export
        mock_figure = Mock()
        mock_figure.to_dict.return_value = {"data": [], "layout": {}}
        
        config = ExportConfig(
            format=ExportFormat.PNG,
            filename="stats_test"
        )
        
        with patch('plotly.io.write_image'):
            job_id = await export_manager.export_visualization(mock_figure, config)
            await export_manager.wait_for_job(job_id, timeout=10)
        
        # Check updated stats
        final_stats = export_manager.get_stats()
        assert final_stats["total_exports"] == initial_stats["total_exports"] + 1
        assert final_stats["successful_exports"] == initial_stats["successful_exports"] + 1


class TestIntegration:
    """Integration tests for advanced visualization components."""
    
    @pytest.mark.asyncio
    async def test_complete_workflow(self):
        """Test complete visualization workflow integration."""
        # Initialize components
        visualizer_3d = create_3d_visualizer()
        dashboard = create_dashboard_builder()
        mobile_ui = create_mobile_renderer()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = create_export_manager(temp_dir)
            
            try:
                # Start services
                await visualizer_3d.start()
                await exporter.start()
                
                # Add data to 3D visualizer
                node1 = Node3D("node1", "Source", "source")
                node2 = Node3D("node2", "Transform", "transform")
                edge = Edge3D("node1", "node2", "data_flow")
                
                await visualizer_3d.add_node(node1)
                await visualizer_3d.add_node(node2)
                await visualizer_3d.add_edge(edge)
                
                # Render 3D visualization
                figure_3d = await visualizer_3d.render()
                assert figure_3d is not None
                
                # Create dashboard widget
                widget = WidgetConfig(
                    id="3d_widget",
                    title="3D Visualization",
                    widget_type=WidgetType.LINEAGE_GRAPH,
                    position=(0, 0),
                    size=(12, 8)
                )
                
                await dashboard.add_widget(widget)
                dashboard_html = await dashboard.render()
                assert dashboard_html is not None
                
                # Create mobile view
                cards = [
                    MobileCard(
                        id="mobile_card",
                        title="Data Pipeline",
                        subtitle="Active",
                        content="Processing data..."
                    )
                ]
                
                mobile_html = await mobile_ui.render_card_view(cards, "Pipeline")
                assert mobile_html is not None
                
                # Export visualization
                config = ExportConfig(
                    format=ExportFormat.PNG,
                    filename="integration_test"
                )
                
                with patch('plotly.io.write_image'):
                    job_id = await exporter.export_visualization(figure_3d, config)
                    job = await exporter.wait_for_job(job_id, timeout=10)
                    assert job.status == "completed"
                
            finally:
                # Cleanup
                await visualizer_3d.stop()
                await exporter.stop()


# Performance and stress tests
class TestPerformance:
    """Performance tests for visualization components."""
    
    @pytest.mark.asyncio
    async def test_large_graph_performance(self):
        """Test performance with large graphs."""
        config = ThreeDConfig(
            physics_enabled=False,  # Disable for performance
            clustering_enabled=True,
            lod_enabled=True
        )
        
        visualizer = create_3d_visualizer(config)
        await visualizer.start()
        
        try:
            # Add many nodes
            node_count = 1000
            for i in range(node_count):
                node = Node3D(f"node_{i}", f"Node {i}", "source")
                await visualizer.add_node(node)
            
            # Add edges
            edge_count = 500
            for i in range(edge_count):
                source = f"node_{i}"
                target = f"node_{(i + 1) % node_count}"
                edge = Edge3D(source, target, "data_flow")
                await visualizer.add_edge(edge)
            
            # Render (should complete within reasonable time)
            import time
            start_time = time.time()
            figure = await visualizer.render()
            render_time = time.time() - start_time
            
            assert figure is not None
            assert render_time < 30  # Should render within 30 seconds
            
        finally:
            await visualizer.stop()
    
    @pytest.mark.asyncio
    async def test_export_performance(self):
        """Test export performance with multiple concurrent exports."""
        with tempfile.TemporaryDirectory() as temp_dir:
            exporter = create_export_manager(temp_dir)
            await exporter.start()
            
            try:
                # Mock figure
                mock_figure = Mock()
                mock_figure.to_dict.return_value = {"data": [], "layout": {}}
                
                # Start multiple exports concurrently
                job_ids = []
                export_count = 10
                
                with patch('plotly.io.write_image'):
                    for i in range(export_count):
                        config = ExportConfig(
                            format=ExportFormat.PNG,
                            filename=f"perf_test_{i}"
                        )
                        job_id = await exporter.export_visualization(mock_figure, config)
                        job_ids.append(job_id)
                    
                    # Wait for all exports to complete
                    start_time = time.time()
                    for job_id in job_ids:
                        job = await exporter.wait_for_job(job_id, timeout=30)
                        assert job.status == "completed"
                    
                    total_time = time.time() - start_time
                    assert total_time < 60  # All exports should complete within 60 seconds
                
            finally:
                await exporter.stop()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
