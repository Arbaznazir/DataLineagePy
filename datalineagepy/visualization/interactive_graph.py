"""
Interactive graph visualizer for real-time data lineage visualization.
Provides interactive, zoomable, and searchable lineage graphs with real-time updates.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable, Set, Tuple
from datetime import datetime
from enum import Enum
import threading
import time

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import networkx as nx
    import pandas as pd
except ImportError:
    go = None
    px = None
    make_subplots = None
    nx = None
    pd = None

logger = logging.getLogger(__name__)


class InteractionMode(Enum):
    """Interaction modes for the graph."""
    VIEW = "view"
    SELECT = "select"
    EDIT = "edit"
    FILTER = "filter"
    SEARCH = "search"


class NodeType(Enum):
    """Types of nodes in the lineage graph."""
    TABLE = "table"
    VIEW = "view"
    COLUMN = "column"
    TRANSFORMATION = "transformation"
    PIPELINE = "pipeline"
    SYSTEM = "system"
    USER = "user"
    PROCESS = "process"


class EdgeType(Enum):
    """Types of edges in the lineage graph."""
    DATA_FLOW = "data_flow"
    TRANSFORMATION = "transformation"
    DEPENDENCY = "dependency"
    INHERITANCE = "inheritance"
    REFERENCE = "reference"
    TRIGGER = "trigger"


@dataclass
class GraphNode:
    """Represents a node in the interactive graph."""
    id: str
    label: str
    node_type: NodeType
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0
    size: float = 10.0
    color: str = "#1f77b4"
    metadata: Dict[str, Any] = field(default_factory=dict)
    tooltip: str = ""
    selected: bool = False
    highlighted: bool = False
    visible: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'label': self.label,
            'node_type': self.node_type.value,
            'x': self.x,
            'y': self.y,
            'z': self.z,
            'size': self.size,
            'color': self.color,
            'metadata': self.metadata,
            'tooltip': self.tooltip,
            'selected': self.selected,
            'highlighted': self.highlighted,
            'visible': self.visible,
        }


@dataclass
class GraphEdge:
    """Represents an edge in the interactive graph."""
    id: str
    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    color: str = "#666666"
    width: float = 2.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    tooltip: str = ""
    selected: bool = False
    highlighted: bool = False
    visible: bool = True
    animated: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'id': self.id,
            'source': self.source,
            'target': self.target,
            'edge_type': self.edge_type.value,
            'weight': self.weight,
            'color': self.color,
            'width': self.width,
            'metadata': self.metadata,
            'tooltip': self.tooltip,
            'selected': self.selected,
            'highlighted': self.highlighted,
            'visible': self.visible,
            'animated': self.animated,
        }


@dataclass
class GraphConfig:
    """Configuration for interactive graph visualization."""
    width: int = 1200
    height: int = 800
    background_color: str = "#ffffff"
    node_size_range: Tuple[float, float] = (5.0, 30.0)
    edge_width_range: Tuple[float, float] = (1.0, 10.0)
    font_size: int = 12
    font_family: str = "Arial, sans-serif"
    animation_duration: int = 500
    zoom_enabled: bool = True
    pan_enabled: bool = True
    selection_enabled: bool = True
    multi_selection_enabled: bool = True
    tooltip_enabled: bool = True
    search_enabled: bool = True
    filter_enabled: bool = True
    layout_algorithm: str = "force_directed"
    physics_enabled: bool = True
    clustering_enabled: bool = True
    real_time_updates: bool = True
    auto_refresh_interval: float = 5.0
    max_nodes: int = 10000
    max_edges: int = 50000
    
    # Color schemes
    node_colors: Dict[str, str] = field(default_factory=lambda: {
        'table': '#1f77b4',
        'view': '#ff7f0e',
        'column': '#2ca02c',
        'transformation': '#d62728',
        'pipeline': '#9467bd',
        'system': '#8c564b',
        'user': '#e377c2',
        'process': '#7f7f7f',
    })
    
    edge_colors: Dict[str, str] = field(default_factory=lambda: {
        'data_flow': '#1f77b4',
        'transformation': '#ff7f0e',
        'dependency': '#2ca02c',
        'inheritance': '#d62728',
        'reference': '#9467bd',
        'trigger': '#8c564b',
    })


class InteractiveGraphVisualizer:
    """Interactive graph visualizer for data lineage."""
    
    def __init__(self, config: GraphConfig):
        self.config = config
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: Dict[str, GraphEdge] = {}
        self.graph: Optional[nx.Graph] = None
        self.figure: Optional[go.Figure] = None
        
        # State management
        self.selected_nodes: Set[str] = set()
        self.selected_edges: Set[str] = set()
        self.highlighted_nodes: Set[str] = set()
        self.highlighted_edges: Set[str] = set()
        self.filtered_nodes: Set[str] = set()
        self.filtered_edges: Set[str] = set()
        self.search_results: Set[str] = set()
        
        # Interaction state
        self.interaction_mode = InteractionMode.VIEW
        self.zoom_level = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        
        # Event handlers
        self.node_click_handlers: List[Callable] = []
        self.edge_click_handlers: List[Callable] = []
        self.selection_change_handlers: List[Callable] = []
        self.zoom_change_handlers: List[Callable] = []
        
        # Real-time updates
        self.real_time_enabled = config.real_time_updates
        self.update_queue: asyncio.Queue = asyncio.Queue()
        self.update_task: Optional[asyncio.Task] = None
        
        # Statistics
        self.stats = {
            'nodes_count': 0,
            'edges_count': 0,
            'visible_nodes': 0,
            'visible_edges': 0,
            'selected_nodes': 0,
            'selected_edges': 0,
            'last_update': None,
            'render_time': 0.0,
        }
        
        self._lock = threading.Lock()
        
        if go is None:
            raise ImportError("plotly is required for interactive graph visualization")
        if nx is None:
            raise ImportError("networkx is required for graph operations")
    
    async def start(self):
        """Start the interactive graph visualizer."""
        if self.real_time_enabled:
            self.update_task = asyncio.create_task(self._process_updates())
        
        # Initialize NetworkX graph
        self.graph = nx.Graph()
        
        logger.info("Interactive graph visualizer started")
    
    async def stop(self):
        """Stop the interactive graph visualizer."""
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Interactive graph visualizer stopped")
    
    def add_node(self, node: GraphNode):
        """Add a node to the graph."""
        with self._lock:
            self.nodes[node.id] = node
            
            if self.graph:
                self.graph.add_node(
                    node.id,
                    label=node.label,
                    node_type=node.node_type.value,
                    size=node.size,
                    color=node.color,
                    **node.metadata
                )
            
            self.stats['nodes_count'] = len(self.nodes)
            if node.visible:
                self.stats['visible_nodes'] = sum(1 for n in self.nodes.values() if n.visible)
    
    def add_edge(self, edge: GraphEdge):
        """Add an edge to the graph."""
        with self._lock:
            self.edges[edge.id] = edge
            
            if self.graph and edge.source in self.nodes and edge.target in self.nodes:
                self.graph.add_edge(
                    edge.source,
                    edge.target,
                    edge_id=edge.id,
                    edge_type=edge.edge_type.value,
                    weight=edge.weight,
                    color=edge.color,
                    width=edge.width,
                    **edge.metadata
                )
            
            self.stats['edges_count'] = len(self.edges)
            if edge.visible:
                self.stats['visible_edges'] = sum(1 for e in self.edges.values() if e.visible)
    
    def remove_node(self, node_id: str):
        """Remove a node from the graph."""
        with self._lock:
            if node_id in self.nodes:
                del self.nodes[node_id]
                
                if self.graph and self.graph.has_node(node_id):
                    self.graph.remove_node(node_id)
                
                # Remove from selections
                self.selected_nodes.discard(node_id)
                self.highlighted_nodes.discard(node_id)
                self.filtered_nodes.discard(node_id)
                self.search_results.discard(node_id)
                
                self.stats['nodes_count'] = len(self.nodes)
                self.stats['visible_nodes'] = sum(1 for n in self.nodes.values() if n.visible)
    
    def remove_edge(self, edge_id: str):
        """Remove an edge from the graph."""
        with self._lock:
            if edge_id in self.edges:
                edge = self.edges[edge_id]
                del self.edges[edge_id]
                
                if self.graph and self.graph.has_edge(edge.source, edge.target):
                    self.graph.remove_edge(edge.source, edge.target)
                
                # Remove from selections
                self.selected_edges.discard(edge_id)
                self.highlighted_edges.discard(edge_id)
                self.filtered_edges.discard(edge_id)
                
                self.stats['edges_count'] = len(self.edges)
                self.stats['visible_edges'] = sum(1 for e in self.edges.values() if e.visible)
    
    def select_node(self, node_id: str, multi_select: bool = False):
        """Select a node."""
        with self._lock:
            if not multi_select:
                self.selected_nodes.clear()
                for node in self.nodes.values():
                    node.selected = False
            
            if node_id in self.nodes:
                self.selected_nodes.add(node_id)
                self.nodes[node_id].selected = True
                self.stats['selected_nodes'] = len(self.selected_nodes)
                
                # Trigger selection change handlers
                for handler in self.selection_change_handlers:
                    try:
                        handler(self.selected_nodes, self.selected_edges)
                    except Exception as e:
                        logger.error(f"Error in selection change handler: {e}")
    
    def select_edge(self, edge_id: str, multi_select: bool = False):
        """Select an edge."""
        with self._lock:
            if not multi_select:
                self.selected_edges.clear()
                for edge in self.edges.values():
                    edge.selected = False
            
            if edge_id in self.edges:
                self.selected_edges.add(edge_id)
                self.edges[edge_id].selected = True
                self.stats['selected_edges'] = len(self.selected_edges)
                
                # Trigger selection change handlers
                for handler in self.selection_change_handlers:
                    try:
                        handler(self.selected_nodes, self.selected_edges)
                    except Exception as e:
                        logger.error(f"Error in selection change handler: {e}")
    
    def highlight_path(self, start_node: str, end_node: str):
        """Highlight the shortest path between two nodes."""
        if not self.graph or start_node not in self.graph or end_node not in self.graph:
            return
        
        try:
            path = nx.shortest_path(self.graph, start_node, end_node)
            
            # Clear previous highlights
            self.clear_highlights()
            
            # Highlight nodes in path
            for node_id in path:
                if node_id in self.nodes:
                    self.nodes[node_id].highlighted = True
                    self.highlighted_nodes.add(node_id)
            
            # Highlight edges in path
            for i in range(len(path) - 1):
                source, target = path[i], path[i + 1]
                for edge in self.edges.values():
                    if (edge.source == source and edge.target == target) or \
                       (edge.source == target and edge.target == source):
                        edge.highlighted = True
                        self.highlighted_edges.add(edge.id)
                        break
            
        except nx.NetworkXNoPath:
            logger.warning(f"No path found between {start_node} and {end_node}")
        except Exception as e:
            logger.error(f"Error highlighting path: {e}")
    
    def clear_highlights(self):
        """Clear all highlights."""
        with self._lock:
            for node_id in self.highlighted_nodes:
                if node_id in self.nodes:
                    self.nodes[node_id].highlighted = False
            
            for edge_id in self.highlighted_edges:
                if edge_id in self.edges:
                    self.edges[edge_id].highlighted = False
            
            self.highlighted_nodes.clear()
            self.highlighted_edges.clear()
    
    def search_nodes(self, query: str, search_fields: List[str] = None) -> Set[str]:
        """Search for nodes matching the query."""
        if search_fields is None:
            search_fields = ['label', 'id']
        
        results = set()
        query_lower = query.lower()
        
        for node in self.nodes.values():
            for field in search_fields:
                if field == 'label' and query_lower in node.label.lower():
                    results.add(node.id)
                elif field == 'id' and query_lower in node.id.lower():
                    results.add(node.id)
                elif field == 'node_type' and query_lower in node.node_type.value.lower():
                    results.add(node.id)
                elif field in node.metadata and query_lower in str(node.metadata[field]).lower():
                    results.add(node.id)
        
        self.search_results = results
        return results
    
    def filter_by_node_type(self, node_types: List[NodeType]):
        """Filter nodes by type."""
        with self._lock:
            self.filtered_nodes.clear()
            
            for node in self.nodes.values():
                if node.node_type in node_types:
                    node.visible = True
                    self.filtered_nodes.add(node.id)
                else:
                    node.visible = False
            
            self.stats['visible_nodes'] = len(self.filtered_nodes)
    
    def filter_by_edge_type(self, edge_types: List[EdgeType]):
        """Filter edges by type."""
        with self._lock:
            self.filtered_edges.clear()
            
            for edge in self.edges.values():
                if edge.edge_type in edge_types:
                    edge.visible = True
                    self.filtered_edges.add(edge.id)
                else:
                    edge.visible = False
            
            self.stats['visible_edges'] = len(self.filtered_edges)
    
    def get_neighbors(self, node_id: str, depth: int = 1) -> Set[str]:
        """Get neighbors of a node up to specified depth."""
        if not self.graph or node_id not in self.graph:
            return set()
        
        neighbors = set()
        current_level = {node_id}
        
        for _ in range(depth):
            next_level = set()
            for node in current_level:
                node_neighbors = set(self.graph.neighbors(node))
                next_level.update(node_neighbors)
                neighbors.update(node_neighbors)
            current_level = next_level
        
        return neighbors
    
    def render(self) -> go.Figure:
        """Render the interactive graph."""
        start_time = time.time()
        
        try:
            # Create figure
            fig = go.Figure()
            
            # Calculate layout if needed
            if self.graph and self.nodes:
                self._calculate_layout()
            
            # Add edges
            self._add_edges_to_figure(fig)
            
            # Add nodes
            self._add_nodes_to_figure(fig)
            
            # Configure layout
            fig.update_layout(
                title="Interactive Data Lineage Graph",
                showlegend=True,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                annotations=[
                    dict(
                        text="Data Lineage Visualization",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        xanchor='left', yanchor='bottom',
                        font=dict(size=12)
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                plot_bgcolor=self.config.background_color,
                width=self.config.width,
                height=self.config.height,
            )
            
            self.figure = fig
            
            # Update stats
            render_time = time.time() - start_time
            with self._lock:
                self.stats['render_time'] = render_time
                self.stats['last_update'] = datetime.utcnow()
            
            return fig
            
        except Exception as e:
            logger.error(f"Error rendering graph: {e}")
            raise
    
    def _calculate_layout(self):
        """Calculate node positions using the specified layout algorithm."""
        if not self.graph:
            return
        
        try:
            if self.config.layout_algorithm == "force_directed":
                pos = nx.spring_layout(self.graph, k=1, iterations=50)
            elif self.config.layout_algorithm == "circular":
                pos = nx.circular_layout(self.graph)
            elif self.config.layout_algorithm == "hierarchical":
                pos = nx.nx_agraph.graphviz_layout(self.graph, prog='dot')
            else:
                pos = nx.spring_layout(self.graph)
            
            # Update node positions
            for node_id, (x, y) in pos.items():
                if node_id in self.nodes:
                    self.nodes[node_id].x = x * 1000  # Scale for better visualization
                    self.nodes[node_id].y = y * 1000
                    
        except Exception as e:
            logger.error(f"Error calculating layout: {e}")
            # Fallback to random positions
            import random
            for node in self.nodes.values():
                node.x = random.uniform(-500, 500)
                node.y = random.uniform(-500, 500)
    
    def _add_nodes_to_figure(self, fig: go.Figure):
        """Add nodes to the figure."""
        visible_nodes = [node for node in self.nodes.values() if node.visible]
        
        if not visible_nodes:
            return
        
        # Group nodes by type for better legend
        node_groups = {}
        for node in visible_nodes:
            node_type = node.node_type.value
            if node_type not in node_groups:
                node_groups[node_type] = []
            node_groups[node_type].append(node)
        
        # Add trace for each node type
        for node_type, nodes in node_groups.items():
            x_coords = [node.x for node in nodes]
            y_coords = [node.y for node in nodes]
            sizes = [node.size for node in nodes]
            colors = [node.color for node in nodes]
            texts = [node.label for node in nodes]
            hovertexts = [node.tooltip or f"{node.label} ({node.node_type.value})" for node in nodes]
            
            fig.add_trace(go.Scatter(
                x=x_coords,
                y=y_coords,
                mode='markers+text',
                marker=dict(
                    size=sizes,
                    color=colors,
                    line=dict(width=2, color='white'),
                    opacity=0.8
                ),
                text=texts,
                textposition="middle center",
                textfont=dict(size=self.config.font_size, family=self.config.font_family),
                hovertext=hovertexts,
                hoverinfo='text',
                name=node_type.title(),
                showlegend=True
            ))
    
    def _add_edges_to_figure(self, fig: go.Figure):
        """Add edges to the figure."""
        visible_edges = [edge for edge in self.edges.values() if edge.visible]
        
        if not visible_edges:
            return
        
        # Group edges by type
        edge_groups = {}
        for edge in visible_edges:
            edge_type = edge.edge_type.value
            if edge_type not in edge_groups:
                edge_groups[edge_type] = []
            edge_groups[edge_type].append(edge)
        
        # Add trace for each edge type
        for edge_type, edges in edge_groups.items():
            x_coords = []
            y_coords = []
            
            for edge in edges:
                if edge.source in self.nodes and edge.target in self.nodes:
                    source_node = self.nodes[edge.source]
                    target_node = self.nodes[edge.target]
                    
                    x_coords.extend([source_node.x, target_node.x, None])
                    y_coords.extend([source_node.y, target_node.y, None])
            
            if x_coords:
                fig.add_trace(go.Scatter(
                    x=x_coords,
                    y=y_coords,
                    mode='lines',
                    line=dict(
                        width=2,
                        color=self.config.edge_colors.get(edge_type, '#666666')
                    ),
                    hoverinfo='none',
                    name=f"{edge_type.title()} Edges",
                    showlegend=True
                ))
    
    async def _process_updates(self):
        """Process real-time updates."""
        while True:
            try:
                # Wait for update
                update = await self.update_queue.get()
                
                # Process update
                await self._handle_update(update)
                
                # Mark task as done
                self.update_queue.task_done()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing update: {e}")
    
    async def _handle_update(self, update: Dict[str, Any]):
        """Handle a single update."""
        try:
            update_type = update.get('type')
            
            if update_type == 'add_node':
                node_data = update['data']
                node = GraphNode(**node_data)
                self.add_node(node)
            elif update_type == 'add_edge':
                edge_data = update['data']
                edge = GraphEdge(**edge_data)
                self.add_edge(edge)
            elif update_type == 'remove_node':
                node_id = update['node_id']
                self.remove_node(node_id)
            elif update_type == 'remove_edge':
                edge_id = update['edge_id']
                self.remove_edge(edge_id)
            elif update_type == 'update_node':
                node_id = update['node_id']
                changes = update['changes']
                if node_id in self.nodes:
                    for key, value in changes.items():
                        setattr(self.nodes[node_id], key, value)
            elif update_type == 'update_edge':
                edge_id = update['edge_id']
                changes = update['changes']
                if edge_id in self.edges:
                    for key, value in changes.items():
                        setattr(self.edges[edge_id], key, value)
            
        except Exception as e:
            logger.error(f"Error handling update: {e}")
    
    def add_node_click_handler(self, handler: Callable):
        """Add node click handler."""
        self.node_click_handlers.append(handler)
    
    def add_edge_click_handler(self, handler: Callable):
        """Add edge click handler."""
        self.edge_click_handlers.append(handler)
    
    def add_selection_change_handler(self, handler: Callable):
        """Add selection change handler."""
        self.selection_change_handlers.append(handler)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get visualization statistics."""
        with self._lock:
            return self.stats.copy()
    
    def export_data(self) -> Dict[str, Any]:
        """Export graph data."""
        return {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges.values()],
            'config': {
                'width': self.config.width,
                'height': self.config.height,
                'layout_algorithm': self.config.layout_algorithm,
            },
            'stats': self.get_stats(),
        }


def create_interactive_graph(
    width: int = 1200,
    height: int = 800,
    layout_algorithm: str = "force_directed",
    **kwargs
) -> InteractiveGraphVisualizer:
    """Factory function to create interactive graph visualizer."""
    config = GraphConfig(
        width=width,
        height=height,
        layout_algorithm=layout_algorithm,
        **kwargs
    )
    return InteractiveGraphVisualizer(config)
