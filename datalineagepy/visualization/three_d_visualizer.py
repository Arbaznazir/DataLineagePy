"""
3D visualization for complex data lineage relationships.
Provides immersive 3D visualization of data lineage graphs with physics simulation.
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
import math

try:
    import plotly.graph_objects as go
    import plotly.express as px
    import numpy as np
    import networkx as nx
except ImportError:
    go = None
    px = None
    np = None
    nx = None

from .interactive_graph import GraphNode, GraphEdge, NodeType, EdgeType

logger = logging.getLogger(__name__)


class Camera3DMode(Enum):
    """3D camera modes."""
    ORBIT = "orbit"
    FLY = "fly"
    FIRST_PERSON = "first_person"
    TOP_DOWN = "top_down"
    SIDE_VIEW = "side_view"


class Physics3DMode(Enum):
    """3D physics simulation modes."""
    FORCE_DIRECTED = "force_directed"
    HIERARCHICAL = "hierarchical"
    LAYERED = "layered"
    CLUSTERED = "clustered"
    SPRING = "spring"


@dataclass
class Node3D(GraphNode):
    """3D node with additional properties."""
    z: float = 0.0
    velocity_x: float = 0.0
    velocity_y: float = 0.0
    velocity_z: float = 0.0
    mass: float = 1.0
    fixed: bool = False
    layer: int = 0
    cluster_id: Optional[str] = None
    
    def distance_to(self, other: 'Node3D') -> float:
        """Calculate 3D distance to another node."""
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2 +
            (self.z - other.z) ** 2
        )


@dataclass
class Edge3D(GraphEdge):
    """3D edge with additional properties."""
    spring_length: float = 100.0
    spring_strength: float = 0.1
    damping: float = 0.01
    
    def length(self, nodes: Dict[str, Node3D]) -> float:
        """Calculate current edge length."""
        if self.source in nodes and self.target in nodes:
            return nodes[self.source].distance_to(nodes[self.target])
        return 0.0


@dataclass
class ThreeDConfig:
    """Configuration for 3D visualization."""
    width: int = 1200
    height: int = 800
    background_color: str = "#000000"
    
    # Camera settings
    camera_distance: float = 1000.0
    camera_mode: Camera3DMode = Camera3DMode.ORBIT
    auto_rotate: bool = False
    rotation_speed: float = 0.5
    
    # Node settings
    node_size_range: Tuple[float, float] = (5.0, 30.0)
    node_opacity: float = 0.8
    node_hover_size_multiplier: float = 1.5
    
    # Edge settings
    edge_width_range: Tuple[float, float] = (1.0, 10.0)
    edge_opacity: float = 0.6
    show_edge_labels: bool = False
    
    # Physics settings
    physics_enabled: bool = True
    physics_mode: Physics3DMode = Physics3DMode.FORCE_DIRECTED
    gravity: float = -30.0
    spring_length: float = 100.0
    spring_strength: float = 0.08
    damping: float = 0.09
    repulsion_strength: float = 1000.0
    max_velocity: float = 50.0
    simulation_steps: int = 100
    
    # Clustering settings
    clustering_enabled: bool = True
    cluster_separation: float = 200.0
    cluster_gravity: float = 0.1
    
    # Layering settings
    layer_separation: float = 150.0
    layer_auto_arrange: bool = True
    
    # Animation settings
    animation_enabled: bool = True
    animation_duration: int = 1000
    smooth_transitions: bool = True
    
    # Interaction settings
    enable_controls: bool = True
    enable_zoom: bool = True
    enable_pan: bool = True
    enable_rotate: bool = True
    
    # Performance settings
    max_nodes_3d: int = 5000
    max_edges_3d: int = 25000
    level_of_detail: bool = True
    frustum_culling: bool = True


class ThreeDVisualizer:
    """3D visualizer for data lineage graphs."""
    
    def __init__(self, config: ThreeDConfig):
        self.config = config
        self.nodes: Dict[str, Node3D] = {}
        self.edges: Dict[str, Edge3D] = {}
        self.graph: Optional[nx.Graph] = None
        self.figure: Optional[go.Figure] = None
        
        # Physics simulation
        self.physics_running = False
        self.physics_task: Optional[asyncio.Task] = None
        self.simulation_time = 0.0
        
        # Clustering
        self.clusters: Dict[str, Set[str]] = {}
        self.cluster_centers: Dict[str, Tuple[float, float, float]] = {}
        
        # Layers
        self.layers: Dict[int, Set[str]] = {}
        self.layer_positions: Dict[int, float] = {}
        
        # Camera and view
        self.camera_position = [0, 0, config.camera_distance]
        self.camera_target = [0, 0, 0]
        self.camera_up = [0, 1, 0]
        
        # Animation
        self.animation_queue: asyncio.Queue = asyncio.Queue()
        self.animation_task: Optional[asyncio.Task] = None
        
        # Event handlers
        self.node_hover_handlers: List[Callable] = []
        self.camera_change_handlers: List[Callable] = []
        
        # Statistics
        self.stats = {
            'nodes_3d': 0,
            'edges_3d': 0,
            'clusters': 0,
            'layers': 0,
            'physics_fps': 0.0,
            'render_time': 0.0,
            'last_update': None,
        }
        
        self._lock = threading.Lock()
        
        if go is None:
            raise ImportError("plotly is required for 3D visualization")
        if np is None:
            raise ImportError("numpy is required for 3D calculations")
        if nx is None:
            raise ImportError("networkx is required for graph operations")
    
    async def start(self):
        """Start the 3D visualizer."""
        # Initialize NetworkX graph
        self.graph = nx.Graph()
        
        # Start physics simulation if enabled
        if self.config.physics_enabled:
            self.physics_running = True
            self.physics_task = asyncio.create_task(self._physics_simulation())
        
        # Start animation processing
        if self.config.animation_enabled:
            self.animation_task = asyncio.create_task(self._process_animations())
        
        logger.info("3D visualizer started")
    
    async def stop(self):
        """Stop the 3D visualizer."""
        # Stop physics simulation
        self.physics_running = False
        if self.physics_task:
            self.physics_task.cancel()
            try:
                await self.physics_task
            except asyncio.CancelledError:
                pass
        
        # Stop animation processing
        if self.animation_task:
            self.animation_task.cancel()
            try:
                await self.animation_task
            except asyncio.CancelledError:
                pass
        
        logger.info("3D visualizer stopped")
    
    def add_node_3d(self, node: Node3D):
        """Add a 3D node to the visualization."""
        with self._lock:
            self.nodes[node.id] = node
            
            if self.graph:
                self.graph.add_node(
                    node.id,
                    x=node.x,
                    y=node.y,
                    z=node.z,
                    layer=node.layer,
                    cluster_id=node.cluster_id,
                    **node.metadata
                )
            
            # Update layer tracking
            if node.layer not in self.layers:
                self.layers[node.layer] = set()
            self.layers[node.layer].add(node.id)
            
            # Update cluster tracking
            if node.cluster_id:
                if node.cluster_id not in self.clusters:
                    self.clusters[node.cluster_id] = set()
                self.clusters[node.cluster_id].add(node.id)
            
            self.stats['nodes_3d'] = len(self.nodes)
            self.stats['layers'] = len(self.layers)
            self.stats['clusters'] = len(self.clusters)
    
    def add_edge_3d(self, edge: Edge3D):
        """Add a 3D edge to the visualization."""
        with self._lock:
            self.edges[edge.id] = edge
            
            if self.graph and edge.source in self.nodes and edge.target in self.nodes:
                self.graph.add_edge(
                    edge.source,
                    edge.target,
                    edge_id=edge.id,
                    spring_length=edge.spring_length,
                    spring_strength=edge.spring_strength,
                    **edge.metadata
                )
            
            self.stats['edges_3d'] = len(self.edges)
    
    def create_node_3d_from_2d(self, node_2d: GraphNode, z: float = 0.0, layer: int = 0) -> Node3D:
        """Create a 3D node from a 2D node."""
        return Node3D(
            id=node_2d.id,
            label=node_2d.label,
            node_type=node_2d.node_type,
            x=node_2d.x,
            y=node_2d.y,
            z=z,
            size=node_2d.size,
            color=node_2d.color,
            metadata=node_2d.metadata,
            tooltip=node_2d.tooltip,
            layer=layer,
        )
    
    def create_edge_3d_from_2d(self, edge_2d: GraphEdge) -> Edge3D:
        """Create a 3D edge from a 2D edge."""
        return Edge3D(
            id=edge_2d.id,
            source=edge_2d.source,
            target=edge_2d.target,
            edge_type=edge_2d.edge_type,
            weight=edge_2d.weight,
            color=edge_2d.color,
            width=edge_2d.width,
            metadata=edge_2d.metadata,
            tooltip=edge_2d.tooltip,
            spring_length=self.config.spring_length,
            spring_strength=self.config.spring_strength,
        )
    
    def arrange_by_layers(self):
        """Arrange nodes by layers along the Z-axis."""
        if not self.layers:
            return
        
        layer_count = len(self.layers)
        layer_keys = sorted(self.layers.keys())
        
        for i, layer_id in enumerate(layer_keys):
            z_position = (i - layer_count / 2) * self.config.layer_separation
            self.layer_positions[layer_id] = z_position
            
            # Update node positions
            for node_id in self.layers[layer_id]:
                if node_id in self.nodes:
                    self.nodes[node_id].z = z_position
    
    def arrange_by_clusters(self):
        """Arrange nodes by clusters in 3D space."""
        if not self.clusters:
            return
        
        cluster_count = len(self.clusters)
        cluster_keys = list(self.clusters.keys())
        
        # Arrange clusters in a 3D grid
        grid_size = math.ceil(cluster_count ** (1/3))
        
        for i, cluster_id in enumerate(cluster_keys):
            # Calculate cluster center position
            x = (i % grid_size - grid_size / 2) * self.config.cluster_separation
            y = ((i // grid_size) % grid_size - grid_size / 2) * self.config.cluster_separation
            z = (i // (grid_size * grid_size) - grid_size / 2) * self.config.cluster_separation
            
            self.cluster_centers[cluster_id] = (x, y, z)
            
            # Arrange nodes within cluster
            cluster_nodes = list(self.clusters[cluster_id])
            cluster_size = len(cluster_nodes)
            
            for j, node_id in enumerate(cluster_nodes):
                if node_id in self.nodes:
                    # Position nodes in a sphere around cluster center
                    angle1 = (j / cluster_size) * 2 * math.pi
                    angle2 = math.acos(1 - 2 * (j / cluster_size))
                    radius = 50  # Cluster radius
                    
                    node_x = x + radius * math.sin(angle2) * math.cos(angle1)
                    node_y = y + radius * math.sin(angle2) * math.sin(angle1)
                    node_z = z + radius * math.cos(angle2)
                    
                    self.nodes[node_id].x = node_x
                    self.nodes[node_id].y = node_y
                    self.nodes[node_id].z = node_z
    
    def render_3d(self) -> go.Figure:
        """Render the 3D visualization."""
        start_time = time.time()
        
        try:
            # Create 3D figure
            fig = go.Figure()
            
            # Add 3D edges
            self._add_3d_edges(fig)
            
            # Add 3D nodes
            self._add_3d_nodes(fig)
            
            # Configure 3D layout
            fig.update_layout(
                title="3D Data Lineage Visualization",
                scene=dict(
                    xaxis=dict(
                        showgrid=False,
                        showticklabels=False,
                        showline=False,
                        zeroline=False,
                        title=""
                    ),
                    yaxis=dict(
                        showgrid=False,
                        showticklabels=False,
                        showline=False,
                        zeroline=False,
                        title=""
                    ),
                    zaxis=dict(
                        showgrid=False,
                        showticklabels=False,
                        showline=False,
                        zeroline=False,
                        title=""
                    ),
                    bgcolor=self.config.background_color,
                    camera=dict(
                        eye=dict(
                            x=self.camera_position[0] / 1000,
                            y=self.camera_position[1] / 1000,
                            z=self.camera_position[2] / 1000
                        ),
                        center=dict(
                            x=self.camera_target[0] / 1000,
                            y=self.camera_target[1] / 1000,
                            z=self.camera_target[2] / 1000
                        ),
                        up=dict(
                            x=self.camera_up[0],
                            y=self.camera_up[1],
                            z=self.camera_up[2]
                        )
                    )
                ),
                width=self.config.width,
                height=self.config.height,
                showlegend=True,
                margin=dict(l=0, r=0, b=0, t=30),
            )
            
            self.figure = fig
            
            # Update stats
            render_time = time.time() - start_time
            with self._lock:
                self.stats['render_time'] = render_time
                self.stats['last_update'] = datetime.utcnow()
            
            return fig
            
        except Exception as e:
            logger.error(f"Error rendering 3D visualization: {e}")
            raise
    
    def _add_3d_nodes(self, fig: go.Figure):
        """Add 3D nodes to the figure."""
        visible_nodes = [node for node in self.nodes.values() if node.visible]
        
        if not visible_nodes:
            return
        
        # Group nodes by type
        node_groups = {}
        for node in visible_nodes:
            node_type = node.node_type.value
            if node_type not in node_groups:
                node_groups[node_type] = []
            node_groups[node_type].append(node)
        
        # Add 3D scatter trace for each node type
        for node_type, nodes in node_groups.items():
            x_coords = [node.x for node in nodes]
            y_coords = [node.y for node in nodes]
            z_coords = [node.z for node in nodes]
            sizes = [node.size for node in nodes]
            colors = [node.color for node in nodes]
            texts = [node.label for node in nodes]
            hovertexts = [node.tooltip or f"{node.label} ({node.node_type.value})" for node in nodes]
            
            fig.add_trace(go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='markers+text',
                marker=dict(
                    size=sizes,
                    color=colors,
                    opacity=self.config.node_opacity,
                    line=dict(width=2, color='white'),
                ),
                text=texts,
                textposition="middle center",
                hovertext=hovertexts,
                hoverinfo='text',
                name=node_type.title(),
                showlegend=True
            ))
    
    def _add_3d_edges(self, fig: go.Figure):
        """Add 3D edges to the figure."""
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
        
        # Add 3D line trace for each edge type
        for edge_type, edges in edge_groups.items():
            x_coords = []
            y_coords = []
            z_coords = []
            
            for edge in edges:
                if edge.source in self.nodes and edge.target in self.nodes:
                    source_node = self.nodes[edge.source]
                    target_node = self.nodes[edge.target]
                    
                    x_coords.extend([source_node.x, target_node.x, None])
                    y_coords.extend([source_node.y, target_node.y, None])
                    z_coords.extend([source_node.z, target_node.z, None])
            
            if x_coords:
                fig.add_trace(go.Scatter3d(
                    x=x_coords,
                    y=y_coords,
                    z=z_coords,
                    mode='lines',
                    line=dict(
                        width=4,
                        color=edges[0].color if edges else '#666666'
                    ),
                    opacity=self.config.edge_opacity,
                    hoverinfo='none',
                    name=f"{edge_type.title()} Edges",
                    showlegend=True
                ))
    
    async def _physics_simulation(self):
        """Run physics simulation for 3D layout."""
        last_time = time.time()
        
        while self.physics_running:
            try:
                current_time = time.time()
                dt = current_time - last_time
                last_time = current_time
                
                if dt > 0:
                    # Run physics step
                    self._physics_step(dt)
                    
                    # Update FPS
                    fps = 1.0 / dt if dt > 0 else 0
                    with self._lock:
                        self.stats['physics_fps'] = fps
                
                # Control simulation speed
                await asyncio.sleep(0.016)  # ~60 FPS
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in physics simulation: {e}")
                await asyncio.sleep(0.1)
    
    def _physics_step(self, dt: float):
        """Execute one physics simulation step."""
        if not self.nodes:
            return
        
        # Apply forces
        for node in self.nodes.values():
            if node.fixed:
                continue
            
            # Reset forces
            force_x = force_y = force_z = 0.0
            
            # Gravity
            force_z += self.config.gravity * node.mass
            
            # Repulsion from other nodes
            for other_node in self.nodes.values():
                if other_node.id != node.id:
                    distance = node.distance_to(other_node)
                    if distance > 0:
                        repulsion = self.config.repulsion_strength / (distance ** 2)
                        direction_x = (node.x - other_node.x) / distance
                        direction_y = (node.y - other_node.y) / distance
                        direction_z = (node.z - other_node.z) / distance
                        
                        force_x += repulsion * direction_x
                        force_y += repulsion * direction_y
                        force_z += repulsion * direction_z
            
            # Spring forces from edges
            for edge in self.edges.values():
                if edge.source == node.id:
                    other_id = edge.target
                elif edge.target == node.id:
                    other_id = edge.source
                else:
                    continue
                
                if other_id in self.nodes:
                    other_node = self.nodes[other_id]
                    distance = node.distance_to(other_node)
                    
                    if distance > 0:
                        spring_force = edge.spring_strength * (distance - edge.spring_length)
                        direction_x = (other_node.x - node.x) / distance
                        direction_y = (other_node.y - node.y) / distance
                        direction_z = (other_node.z - node.z) / distance
                        
                        force_x += spring_force * direction_x
                        force_y += spring_force * direction_y
                        force_z += spring_force * direction_z
            
            # Cluster gravity
            if node.cluster_id and node.cluster_id in self.cluster_centers:
                center_x, center_y, center_z = self.cluster_centers[node.cluster_id]
                distance_to_center = math.sqrt(
                    (node.x - center_x) ** 2 +
                    (node.y - center_y) ** 2 +
                    (node.z - center_z) ** 2
                )
                
                if distance_to_center > 0:
                    cluster_force = self.config.cluster_gravity * distance_to_center
                    force_x += cluster_force * (center_x - node.x) / distance_to_center
                    force_y += cluster_force * (center_y - node.y) / distance_to_center
                    force_z += cluster_force * (center_z - node.z) / distance_to_center
            
            # Update velocity
            node.velocity_x += force_x / node.mass * dt
            node.velocity_y += force_y / node.mass * dt
            node.velocity_z += force_z / node.mass * dt
            
            # Apply damping
            node.velocity_x *= (1 - self.config.damping)
            node.velocity_y *= (1 - self.config.damping)
            node.velocity_z *= (1 - self.config.damping)
            
            # Limit velocity
            velocity_magnitude = math.sqrt(
                node.velocity_x ** 2 + node.velocity_y ** 2 + node.velocity_z ** 2
            )
            if velocity_magnitude > self.config.max_velocity:
                scale = self.config.max_velocity / velocity_magnitude
                node.velocity_x *= scale
                node.velocity_y *= scale
                node.velocity_z *= scale
            
            # Update position
            node.x += node.velocity_x * dt
            node.y += node.velocity_y * dt
            node.z += node.velocity_z * dt
    
    async def _process_animations(self):
        """Process animation queue."""
        while True:
            try:
                animation = await self.animation_queue.get()
                await self._execute_animation(animation)
                self.animation_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing animation: {e}")
    
    async def _execute_animation(self, animation: Dict[str, Any]):
        """Execute a single animation."""
        # Animation implementation would go here
        pass
    
    def set_camera_position(self, x: float, y: float, z: float):
        """Set camera position."""
        self.camera_position = [x, y, z]
    
    def set_camera_target(self, x: float, y: float, z: float):
        """Set camera target."""
        self.camera_target = [x, y, z]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get 3D visualization statistics."""
        with self._lock:
            return self.stats.copy()


def create_3d_visualizer(
    width: int = 1200,
    height: int = 800,
    physics_enabled: bool = True,
    **kwargs
) -> ThreeDVisualizer:
    """Factory function to create 3D visualizer."""
    config = ThreeDConfig(
        width=width,
        height=height,
        physics_enabled=physics_enabled,
        **kwargs
    )
    return ThreeDVisualizer(config)
