"""
Dashboard builder for creating custom data lineage dashboards.
Provides drag-and-drop dashboard creation with multiple widget types.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Set, Union
from datetime import datetime
from enum import Enum
import threading
import uuid

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import pandas as pd
except ImportError:
    go = None
    px = None
    make_subplots = None
    pd = None

logger = logging.getLogger(__name__)


class WidgetType(Enum):
    """Dashboard widget types."""
    LINEAGE_GRAPH = "lineage_graph"
    METRICS_CHART = "metrics_chart"
    TABLE = "table"
    KPI_CARD = "kpi_card"
    TIMELINE = "timeline"
    HEATMAP = "heatmap"
    TREE_MAP = "tree_map"
    SANKEY = "sankey"
    GAUGE = "gauge"
    TEXT = "text"
    IMAGE = "image"
    IFRAME = "iframe"


class ChartType(Enum):
    """Chart types for metrics widgets."""
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    SCATTER = "scatter"
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    AREA = "area"
    FUNNEL = "funnel"
    WATERFALL = "waterfall"


class LayoutType(Enum):
    """Dashboard layout types."""
    GRID = "grid"
    FLEX = "flex"
    MASONRY = "masonry"
    TABS = "tabs"
    ACCORDION = "accordion"


@dataclass
class WidgetConfig:
    """Configuration for a dashboard widget."""
    id: str
    widget_type: WidgetType
    title: str
    description: str = ""
    
    # Position and size
    x: int = 0
    y: int = 0
    width: int = 4
    height: int = 3
    min_width: int = 2
    min_height: int = 2
    max_width: int = 12
    max_height: int = 12
    
    # Styling
    background_color: str = "#ffffff"
    border_color: str = "#e0e0e0"
    border_width: int = 1
    border_radius: int = 4
    padding: int = 16
    margin: int = 8
    
    # Data source
    data_source: Optional[str] = None
    query: Optional[str] = None
    refresh_interval: int = 60  # seconds
    
    # Widget-specific config
    config: Dict[str, Any] = field(default_factory=dict)
    
    # Visibility and permissions
    visible: bool = True
    permissions: List[str] = field(default_factory=list)
    
    # Interactivity
    clickable: bool = False
    drilldown_enabled: bool = False
    filters_enabled: bool = True
    
    # Caching
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds


@dataclass
class DashboardConfig:
    """Configuration for a dashboard."""
    id: str
    name: str
    description: str = ""
    
    # Layout
    layout_type: LayoutType = LayoutType.GRID
    grid_columns: int = 12
    grid_row_height: int = 100
    
    # Styling
    theme: str = "light"
    background_color: str = "#f5f5f5"
    header_color: str = "#ffffff"
    sidebar_color: str = "#ffffff"
    
    # Behavior
    auto_refresh: bool = True
    refresh_interval: int = 300  # seconds
    real_time_updates: bool = False
    
    # Permissions
    public: bool = False
    owner: str = ""
    shared_with: List[str] = field(default_factory=list)
    
    # Export settings
    export_enabled: bool = True
    export_formats: List[str] = field(default_factory=lambda: ["pdf", "png", "html"])
    
    # Mobile settings
    mobile_responsive: bool = True
    mobile_breakpoint: int = 768
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    tags: List[str] = field(default_factory=list)


class DashboardWidget:
    """Individual dashboard widget."""
    
    def __init__(self, config: WidgetConfig):
        self.config = config
        self.data: Optional[Any] = None
        self.figure: Optional[go.Figure] = None
        self.last_updated: Optional[datetime] = None
        self.error: Optional[str] = None
        
        # Event handlers
        self.click_handlers: List[Callable] = []
        self.hover_handlers: List[Callable] = []
        self.filter_handlers: List[Callable] = []
        
        # Cache
        self._cache: Dict[str, Any] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    async def load_data(self, data_source: Any = None):
        """Load data for the widget."""
        try:
            if self.config.data_source and data_source:
                # Load data from configured source
                if self.config.query:
                    self.data = await data_source.query(self.config.query)
                else:
                    self.data = await data_source.get_data()
            
            await self.render()
            self.last_updated = datetime.utcnow()
            self.error = None
            
        except Exception as e:
            self.error = str(e)
            logger.error(f"Error loading data for widget {self.config.id}: {e}")
    
    async def render(self):
        """Render the widget."""
        if not self.data:
            return
        
        try:
            if self.config.widget_type == WidgetType.LINEAGE_GRAPH:
                await self._render_lineage_graph()
            elif self.config.widget_type == WidgetType.METRICS_CHART:
                await self._render_metrics_chart()
            elif self.config.widget_type == WidgetType.TABLE:
                await self._render_table()
            elif self.config.widget_type == WidgetType.KPI_CARD:
                await self._render_kpi_card()
            elif self.config.widget_type == WidgetType.TIMELINE:
                await self._render_timeline()
            elif self.config.widget_type == WidgetType.HEATMAP:
                await self._render_heatmap()
            elif self.config.widget_type == WidgetType.TREE_MAP:
                await self._render_tree_map()
            elif self.config.widget_type == WidgetType.SANKEY:
                await self._render_sankey()
            elif self.config.widget_type == WidgetType.GAUGE:
                await self._render_gauge()
            elif self.config.widget_type == WidgetType.TEXT:
                await self._render_text()
            
        except Exception as e:
            self.error = str(e)
            logger.error(f"Error rendering widget {self.config.id}: {e}")
    
    async def _render_lineage_graph(self):
        """Render lineage graph widget."""
        # Implementation would integrate with interactive_graph.py
        pass
    
    async def _render_metrics_chart(self):
        """Render metrics chart widget."""
        if not pd or not go:
            return
        
        chart_type = self.config.config.get('chart_type', ChartType.LINE.value)
        
        if isinstance(self.data, dict) and 'x' in self.data and 'y' in self.data:
            x_data = self.data['x']
            y_data = self.data['y']
            
            if chart_type == ChartType.LINE.value:
                self.figure = go.Figure(data=go.Scatter(x=x_data, y=y_data, mode='lines'))
            elif chart_type == ChartType.BAR.value:
                self.figure = go.Figure(data=go.Bar(x=x_data, y=y_data))
            elif chart_type == ChartType.PIE.value:
                self.figure = go.Figure(data=go.Pie(labels=x_data, values=y_data))
            elif chart_type == ChartType.SCATTER.value:
                self.figure = go.Figure(data=go.Scatter(x=x_data, y=y_data, mode='markers'))
            
            if self.figure:
                self.figure.update_layout(
                    title=self.config.title,
                    showlegend=True,
                    margin=dict(l=40, r=40, t=40, b=40)
                )
    
    async def _render_table(self):
        """Render table widget."""
        if not go or not isinstance(self.data, (list, dict)):
            return
        
        if isinstance(self.data, list) and self.data:
            # Convert list of dicts to table
            if isinstance(self.data[0], dict):
                headers = list(self.data[0].keys())
                values = [[row.get(header, '') for header in headers] for row in self.data]
            else:
                headers = ['Value']
                values = [[str(item)] for item in self.data]
        elif isinstance(self.data, dict):
            headers = list(self.data.keys())
            values = [list(self.data.values())]
        else:
            return
        
        self.figure = go.Figure(data=[go.Table(
            header=dict(values=headers),
            cells=dict(values=list(zip(*values)))
        )])
        
        self.figure.update_layout(
            title=self.config.title,
            margin=dict(l=0, r=0, t=30, b=0)
        )
    
    async def _render_kpi_card(self):
        """Render KPI card widget."""
        if not go:
            return
        
        value = self.data.get('value', 0) if isinstance(self.data, dict) else self.data
        target = self.config.config.get('target')
        unit = self.config.config.get('unit', '')
        
        # Create indicator
        self.figure = go.Figure(go.Indicator(
            mode="number+delta+gauge",
            value=value,
            delta={'reference': target} if target else None,
            title={'text': self.config.title},
            gauge={'axis': {'range': [None, target * 1.2]} if target else None}
        ))
        
        self.figure.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=200
        )
    
    async def _render_timeline(self):
        """Render timeline widget."""
        if not go or not isinstance(self.data, list):
            return
        
        # Expect data format: [{'date': datetime, 'event': str, 'value': float}]
        dates = [item.get('date') for item in self.data]
        events = [item.get('event', '') for item in self.data]
        values = [item.get('value', 0) for item in self.data]
        
        self.figure = go.Figure(data=go.Scatter(
            x=dates,
            y=values,
            mode='lines+markers',
            text=events,
            hovertemplate='<b>%{text}</b><br>Date: %{x}<br>Value: %{y}<extra></extra>'
        ))
        
        self.figure.update_layout(
            title=self.config.title,
            xaxis_title='Date',
            yaxis_title='Value',
            margin=dict(l=40, r=40, t=40, b=40)
        )
    
    async def _render_heatmap(self):
        """Render heatmap widget."""
        if not go:
            return
        
        if isinstance(self.data, dict) and 'z' in self.data:
            z_data = self.data['z']
            x_labels = self.data.get('x', None)
            y_labels = self.data.get('y', None)
            
            self.figure = go.Figure(data=go.Heatmap(
                z=z_data,
                x=x_labels,
                y=y_labels,
                colorscale='Viridis'
            ))
            
            self.figure.update_layout(
                title=self.config.title,
                margin=dict(l=40, r=40, t=40, b=40)
            )
    
    async def _render_tree_map(self):
        """Render tree map widget."""
        if not go:
            return
        
        if isinstance(self.data, list):
            labels = [item.get('label', '') for item in self.data]
            values = [item.get('value', 0) for item in self.data]
            parents = [item.get('parent', '') for item in self.data]
            
            self.figure = go.Figure(go.Treemap(
                labels=labels,
                values=values,
                parents=parents
            ))
            
            self.figure.update_layout(
                title=self.config.title,
                margin=dict(l=0, r=0, t=30, b=0)
            )
    
    async def _render_sankey(self):
        """Render Sankey diagram widget."""
        if not go:
            return
        
        if isinstance(self.data, dict) and 'nodes' in self.data and 'links' in self.data:
            nodes = self.data['nodes']
            links = self.data['links']
            
            self.figure = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=15,
                    thickness=20,
                    line=dict(color="black", width=0.5),
                    label=[node.get('label', '') for node in nodes],
                    color=[node.get('color', 'blue') for node in nodes]
                ),
                link=dict(
                    source=[link.get('source', 0) for link in links],
                    target=[link.get('target', 0) for link in links],
                    value=[link.get('value', 1) for link in links]
                )
            )])
            
            self.figure.update_layout(
                title=self.config.title,
                margin=dict(l=0, r=0, t=30, b=0)
            )
    
    async def _render_gauge(self):
        """Render gauge widget."""
        if not go:
            return
        
        value = self.data.get('value', 0) if isinstance(self.data, dict) else self.data
        min_val = self.config.config.get('min', 0)
        max_val = self.config.config.get('max', 100)
        
        self.figure = go.Figure(go.Indicator(
            mode="gauge+number",
            value=value,
            title={'text': self.config.title},
            gauge={'axis': {'range': [min_val, max_val]},
                   'bar': {'color': "darkblue"},
                   'steps': [
                       {'range': [min_val, max_val * 0.5], 'color': "lightgray"},
                       {'range': [max_val * 0.5, max_val * 0.8], 'color': "gray"}
                   ],
                   'threshold': {'line': {'color': "red", 'width': 4},
                                'thickness': 0.75, 'value': max_val * 0.9}}
        ))
        
        self.figure.update_layout(margin=dict(l=20, r=20, t=20, b=20))
    
    async def _render_text(self):
        """Render text widget."""
        # Text widgets don't use Plotly figures
        pass
    
    def get_html(self) -> str:
        """Get HTML representation of the widget."""
        if self.figure:
            return self.figure.to_html(include_plotlyjs='cdn')
        elif self.config.widget_type == WidgetType.TEXT:
            content = self.data if isinstance(self.data, str) else str(self.data)
            return f"""
            <div style="padding: {self.config.padding}px; 
                        background-color: {self.config.background_color};
                        border: {self.config.border_width}px solid {self.config.border_color};
                        border-radius: {self.config.border_radius}px;">
                <h3>{self.config.title}</h3>
                <div>{content}</div>
            </div>
            """
        else:
            return f"<div>Widget {self.config.id} - No content</div>"


class DashboardBuilder:
    """Dashboard builder for creating custom dashboards."""
    
    def __init__(self, config: DashboardConfig):
        self.config = config
        self.widgets: Dict[str, DashboardWidget] = {}
        self.layout: List[List[str]] = []  # Grid layout
        
        # Data sources
        self.data_sources: Dict[str, Any] = {}
        
        # Real-time updates
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.update_task: Optional[asyncio.Task] = None
        
        # Event handlers
        self.widget_click_handlers: List[Callable] = []
        self.dashboard_change_handlers: List[Callable] = []
        
        # Statistics
        self.stats = {
            'widgets': 0,
            'data_sources': 0,
            'last_refresh': None,
            'refresh_count': 0,
            'error_count': 0,
        }
        
        self._lock = threading.Lock()
        
        if go is None:
            raise ImportError("plotly is required for dashboard building")
    
    async def start(self):
        """Start the dashboard builder."""
        if self.config.real_time_updates:
            self.update_task = asyncio.create_task(self._process_updates())
        
        logger.info(f"Dashboard builder started for '{self.config.name}'")
    
    async def stop(self):
        """Stop the dashboard builder."""
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"Dashboard builder stopped for '{self.config.name}'")
    
    def add_widget(self, widget_config: WidgetConfig):
        """Add a widget to the dashboard."""
        widget = DashboardWidget(widget_config)
        
        with self._lock:
            self.widgets[widget_config.id] = widget
            self.stats['widgets'] = len(self.widgets)
        
        # Update layout if using grid
        if self.config.layout_type == LayoutType.GRID:
            self._update_grid_layout()
    
    def remove_widget(self, widget_id: str):
        """Remove a widget from the dashboard."""
        with self._lock:
            if widget_id in self.widgets:
                del self.widgets[widget_id]
                self.stats['widgets'] = len(self.widgets)
        
        self._update_grid_layout()
    
    def add_data_source(self, name: str, data_source: Any):
        """Add a data source to the dashboard."""
        with self._lock:
            self.data_sources[name] = data_source
            self.stats['data_sources'] = len(self.data_sources)
    
    async def refresh_all_widgets(self):
        """Refresh all widgets."""
        try:
            tasks = []
            for widget in self.widgets.values():
                if widget.config.data_source and widget.config.data_source in self.data_sources:
                    data_source = self.data_sources[widget.config.data_source]
                    tasks.append(widget.load_data(data_source))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            with self._lock:
                self.stats['last_refresh'] = datetime.utcnow()
                self.stats['refresh_count'] += 1
            
        except Exception as e:
            with self._lock:
                self.stats['error_count'] += 1
            logger.error(f"Error refreshing widgets: {e}")
    
    async def refresh_widget(self, widget_id: str):
        """Refresh a specific widget."""
        if widget_id not in self.widgets:
            return
        
        widget = self.widgets[widget_id]
        if widget.config.data_source and widget.config.data_source in self.data_sources:
            data_source = self.data_sources[widget.config.data_source]
            await widget.load_data(data_source)
    
    def _update_grid_layout(self):
        """Update grid layout based on widget positions."""
        if not self.widgets:
            self.layout = []
            return
        
        # Calculate grid dimensions
        max_x = max(w.config.x + w.config.width for w in self.widgets.values())
        max_y = max(w.config.y + w.config.height for w in self.widgets.values())
        
        # Initialize grid
        grid = [[None for _ in range(max_x)] for _ in range(max_y)]
        
        # Place widgets in grid
        for widget in self.widgets.values():
            for y in range(widget.config.y, widget.config.y + widget.config.height):
                for x in range(widget.config.x, widget.config.x + widget.config.width):
                    if y < len(grid) and x < len(grid[0]):
                        grid[y][x] = widget.config.id
        
        self.layout = grid
    
    def generate_html(self) -> str:
        """Generate HTML for the entire dashboard."""
        html_parts = [
            f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{self.config.name}</title>
                <meta charset="utf-8">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 0;
                        padding: 20px;
                        background-color: {self.config.background_color};
                    }}
                    .dashboard-header {{
                        background-color: {self.config.header_color};
                        padding: 20px;
                        margin-bottom: 20px;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    }}
                    .dashboard-grid {{
                        display: grid;
                        grid-template-columns: repeat({self.config.grid_columns}, 1fr);
                        gap: 16px;
                        auto-rows: {self.config.grid_row_height}px;
                    }}
                    .widget {{
                        background-color: white;
                        border-radius: 8px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }}
                    @media (max-width: {self.config.mobile_breakpoint}px) {{
                        .dashboard-grid {{
                            grid-template-columns: 1fr;
                        }}
                    }}
                </style>
            </head>
            <body>
                <div class="dashboard-header">
                    <h1>{self.config.name}</h1>
                    <p>{self.config.description}</p>
                </div>
                <div class="dashboard-grid">
            """
        ]
        
        # Add widgets
        for widget in self.widgets.values():
            if widget.config.visible:
                widget_html = f"""
                <div class="widget" style="
                    grid-column: span {widget.config.width};
                    grid-row: span {widget.config.height};
                ">
                    {widget.get_html()}
                </div>
                """
                html_parts.append(widget_html)
        
        html_parts.append("""
                </div>
            </body>
            </html>
        """)
        
        return "".join(html_parts)
    
    async def _process_updates(self):
        """Process real-time updates."""
        while True:
            try:
                update = await self.update_queue.get()
                await self._handle_update(update)
                self.update_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing update: {e}")
    
    async def _handle_update(self, update: Dict[str, Any]):
        """Handle a single update."""
        widget_id = update.get('widget_id')
        if widget_id and widget_id in self.widgets:
            await self.refresh_widget(widget_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics."""
        with self._lock:
            return self.stats.copy()


def create_dashboard_builder(
    name: str,
    description: str = "",
    layout_type: LayoutType = LayoutType.GRID,
    **kwargs
) -> DashboardBuilder:
    """Factory function to create dashboard builder."""
    config = DashboardConfig(
        id=str(uuid.uuid4()),
        name=name,
        description=description,
        layout_type=layout_type,
        **kwargs
    )
    return DashboardBuilder(config)


def create_widget_config(
    widget_type: WidgetType,
    title: str,
    x: int = 0,
    y: int = 0,
    width: int = 4,
    height: int = 3,
    **kwargs
) -> WidgetConfig:
    """Factory function to create widget configuration."""
    return WidgetConfig(
        id=str(uuid.uuid4()),
        widget_type=widget_type,
        title=title,
        x=x,
        y=y,
        width=width,
        height=height,
        **kwargs
    )
