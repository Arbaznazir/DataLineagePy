"""
Data flow mapper for enterprise integrations - handles lineage mapping functionality.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Set, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import json
from abc import ABC, abstractmethod
import networkx as nx

logger = logging.getLogger(__name__)


class FlowType(Enum):
    """Types of data flows."""
    READ = "read"
    WRITE = "write"
    TRANSFORM = "transform"
    COPY = "copy"
    MOVE = "move"
    DELETE = "delete"
    CREATE = "create"
    UPDATE = "update"
    MERGE = "merge"
    JOIN = "join"
    AGGREGATE = "aggregate"
    FILTER = "filter"
    SORT = "sort"
    UNION = "union"
    SPLIT = "split"
    PIVOT = "pivot"
    UNPIVOT = "unpivot"


class FlowDirection(Enum):
    """Direction of data flow."""
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class DataEntity:
    """Represents a data entity in the flow."""
    entity_id: str
    name: str
    entity_type: str
    system: str
    location: Optional[str] = None
    schema: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'entity_id': self.entity_id,
            'name': self.name,
            'entity_type': self.entity_type,
            'system': self.system,
            'location': self.location,
            'schema': self.schema,
            'properties': self.properties,
            'tags': self.tags
        }


@dataclass
class DataFlow:
    """Represents a data flow between entities."""
    flow_id: str
    source_entity: DataEntity
    target_entity: DataEntity
    flow_type: FlowType
    direction: FlowDirection = FlowDirection.DOWNSTREAM
    timestamp: datetime = field(default_factory=datetime.utcnow)
    process_name: Optional[str] = None
    process_id: Optional[str] = None
    transformation_logic: Optional[str] = None
    columns_mapping: Dict[str, str] = field(default_factory=dict)
    properties: Dict[str, Any] = field(default_factory=dict)
    confidence_score: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'flow_id': self.flow_id,
            'source_entity': self.source_entity.to_dict(),
            'target_entity': self.target_entity.to_dict(),
            'flow_type': self.flow_type.value,
            'direction': self.direction.value,
            'timestamp': self.timestamp.isoformat(),
            'process_name': self.process_name,
            'process_id': self.process_id,
            'transformation_logic': self.transformation_logic,
            'columns_mapping': self.columns_mapping,
            'properties': self.properties,
            'confidence_score': self.confidence_score
        }
    
    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), default=str)


@dataclass
class FlowPath:
    """Represents a path through multiple data flows."""
    path_id: str
    flows: List[DataFlow]
    total_hops: int = 0
    path_length: float = 0.0
    confidence_score: float = 1.0
    
    def __post_init__(self):
        self.total_hops = len(self.flows)
        self.path_length = sum(1.0 / flow.confidence_score for flow in self.flows)
        if self.flows:
            self.confidence_score = min(flow.confidence_score for flow in self.flows)
    
    def get_entities(self) -> List[DataEntity]:
        """Get all entities in the path."""
        entities = []
        for flow in self.flows:
            entities.append(flow.source_entity)
            entities.append(flow.target_entity)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_entities = []
        for entity in entities:
            if entity.entity_id not in seen:
                seen.add(entity.entity_id)
                unique_entities.append(entity)
        
        return unique_entities
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'path_id': self.path_id,
            'flows': [flow.to_dict() for flow in self.flows],
            'total_hops': self.total_hops,
            'path_length': self.path_length,
            'confidence_score': self.confidence_score
        }


class BaseFlowMapper(ABC):
    """Base class for data flow mappers."""
    
    def __init__(self, system_name: str):
        self.system_name = system_name
        self.discovered_flows: Dict[str, DataFlow] = {}
        self.mapping_stats = {
            'total_flows': 0,
            'successful_mappings': 0,
            'failed_mappings': 0,
            'mapping_time': 0.0,
            'last_mapping': None
        }
    
    @abstractmethod
    async def discover_flows(self, entity_id: Optional[str] = None) -> List[DataFlow]:
        """Discover data flows from the system."""
        pass
    
    @abstractmethod
    async def trace_upstream(self, entity_id: str, max_depth: int = 10) -> List[FlowPath]:
        """Trace upstream data flows."""
        pass
    
    @abstractmethod
    async def trace_downstream(self, entity_id: str, max_depth: int = 10) -> List[FlowPath]:
        """Trace downstream data flows."""
        pass
    
    async def get_cached_flows(self, entity_id: str) -> List[DataFlow]:
        """Get cached flows for an entity."""
        return [flow for flow in self.discovered_flows.values() 
                if flow.source_entity.entity_id == entity_id or 
                   flow.target_entity.entity_id == entity_id]
    
    async def cache_flow(self, flow: DataFlow):
        """Cache a data flow."""
        self.discovered_flows[flow.flow_id] = flow
    
    async def clear_cache(self):
        """Clear flow cache."""
        self.discovered_flows.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mapping statistics."""
        return self.mapping_stats.copy()


class DataFlowMapper:
    """Main data flow mapper that coordinates different mappers."""
    
    def __init__(self):
        self.mappers: Dict[str, BaseFlowMapper] = {}
        self.flow_graph = nx.DiGraph()
        self.flow_cache: Dict[str, DataFlow] = {}
        self.entity_cache: Dict[str, DataEntity] = {}
        self.mapping_history: List[Dict[str, Any]] = []
        self.stats = {
            'total_mappings': 0,
            'successful_mappings': 0,
            'failed_mappings': 0,
            'systems_count': 0,
            'flows_count': 0,
            'entities_count': 0
        }
    
    def register_mapper(self, system_name: str, mapper: BaseFlowMapper):
        """Register a flow mapper for a system."""
        self.mappers[system_name] = mapper
        self.stats['systems_count'] = len(self.mappers)
        logger.info(f"Registered flow mapper for {system_name}")
    
    def unregister_mapper(self, system_name: str):
        """Unregister a flow mapper."""
        if system_name in self.mappers:
            del self.mappers[system_name]
            self.stats['systems_count'] = len(self.mappers)
            logger.info(f"Unregistered flow mapper for {system_name}")
    
    async def discover_all_flows(self) -> Dict[str, List[DataFlow]]:
        """Discover flows from all registered systems."""
        results = {}
        
        for system_name, mapper in self.mappers.items():
            try:
                start_time = datetime.utcnow()
                flows = await mapper.discover_flows()
                end_time = datetime.utcnow()
                
                results[system_name] = flows
                
                # Cache flows and build graph
                for flow in flows:
                    await self.cache_flow(flow)
                    await self.add_flow_to_graph(flow)
                
                # Update stats
                self.stats['total_mappings'] += 1
                self.stats['successful_mappings'] += 1
                self.stats['flows_count'] += len(flows)
                
                # Record mapping history
                self.mapping_history.append({
                    'system': system_name,
                    'timestamp': start_time,
                    'duration': (end_time - start_time).total_seconds(),
                    'flows_discovered': len(flows),
                    'success': True
                })
                
                logger.info(f"Discovered {len(flows)} flows from {system_name}")
                
            except Exception as e:
                self.stats['total_mappings'] += 1
                self.stats['failed_mappings'] += 1
                
                self.mapping_history.append({
                    'system': system_name,
                    'timestamp': datetime.utcnow(),
                    'duration': 0,
                    'flows_discovered': 0,
                    'success': False,
                    'error': str(e)
                })
                
                logger.error(f"Failed to discover flows from {system_name}: {e}")
                results[system_name] = []
        
        return results
    
    async def cache_flow(self, flow: DataFlow):
        """Cache a data flow."""
        self.flow_cache[flow.flow_id] = flow
        
        # Cache entities
        self.entity_cache[flow.source_entity.entity_id] = flow.source_entity
        self.entity_cache[flow.target_entity.entity_id] = flow.target_entity
        
        self.stats['entities_count'] = len(self.entity_cache)
    
    async def add_flow_to_graph(self, flow: DataFlow):
        """Add flow to the graph."""
        source_id = flow.source_entity.entity_id
        target_id = flow.target_entity.entity_id
        
        # Add nodes
        self.flow_graph.add_node(source_id, entity=flow.source_entity)
        self.flow_graph.add_node(target_id, entity=flow.target_entity)
        
        # Add edge
        self.flow_graph.add_edge(
            source_id, target_id,
            flow=flow,
            weight=1.0 / flow.confidence_score
        )
    
    async def trace_upstream_flows(self, entity_id: str, max_depth: int = 10) -> List[FlowPath]:
        """Trace upstream data flows."""
        paths = []
        
        try:
            # Use NetworkX to find paths
            for source_id in self.flow_graph.nodes():
                if source_id != entity_id:
                    try:
                        # Find shortest paths
                        path_nodes = nx.shortest_path(
                            self.flow_graph, source_id, entity_id
                        )
                        
                        if len(path_nodes) <= max_depth + 1:
                            # Convert node path to flow path
                            flows = []
                            for i in range(len(path_nodes) - 1):
                                edge_data = self.flow_graph.get_edge_data(
                                    path_nodes[i], path_nodes[i + 1]
                                )
                                if edge_data and 'flow' in edge_data:
                                    flows.append(edge_data['flow'])
                            
                            if flows:
                                path = FlowPath(
                                    path_id=f"upstream_{entity_id}_{len(paths)}",
                                    flows=flows
                                )
                                paths.append(path)
                    
                    except nx.NetworkXNoPath:
                        continue
        
        except Exception as e:
            logger.error(f"Error tracing upstream flows for {entity_id}: {e}")
        
        return paths
    
    async def trace_downstream_flows(self, entity_id: str, max_depth: int = 10) -> List[FlowPath]:
        """Trace downstream data flows."""
        paths = []
        
        try:
            # Use NetworkX to find paths
            for target_id in self.flow_graph.nodes():
                if target_id != entity_id:
                    try:
                        # Find shortest paths
                        path_nodes = nx.shortest_path(
                            self.flow_graph, entity_id, target_id
                        )
                        
                        if len(path_nodes) <= max_depth + 1:
                            # Convert node path to flow path
                            flows = []
                            for i in range(len(path_nodes) - 1):
                                edge_data = self.flow_graph.get_edge_data(
                                    path_nodes[i], path_nodes[i + 1]
                                )
                                if edge_data and 'flow' in edge_data:
                                    flows.append(edge_data['flow'])
                            
                            if flows:
                                path = FlowPath(
                                    path_id=f"downstream_{entity_id}_{len(paths)}",
                                    flows=flows
                                )
                                paths.append(path)
                    
                    except nx.NetworkXNoPath:
                        continue
        
        except Exception as e:
            logger.error(f"Error tracing downstream flows for {entity_id}: {e}")
        
        return paths
    
    async def find_flow_paths(self, source_id: str, target_id: str, max_paths: int = 10) -> List[FlowPath]:
        """Find all paths between two entities."""
        paths = []
        
        try:
            # Find all simple paths
            all_paths = nx.all_simple_paths(
                self.flow_graph, source_id, target_id, cutoff=10
            )
            
            path_count = 0
            for path_nodes in all_paths:
                if path_count >= max_paths:
                    break
                
                # Convert node path to flow path
                flows = []
                for i in range(len(path_nodes) - 1):
                    edge_data = self.flow_graph.get_edge_data(
                        path_nodes[i], path_nodes[i + 1]
                    )
                    if edge_data and 'flow' in edge_data:
                        flows.append(edge_data['flow'])
                
                if flows:
                    path = FlowPath(
                        path_id=f"path_{source_id}_{target_id}_{path_count}",
                        flows=flows
                    )
                    paths.append(path)
                    path_count += 1
        
        except Exception as e:
            logger.error(f"Error finding paths from {source_id} to {target_id}: {e}")
        
        return paths
    
    async def get_entity_flows(self, entity_id: str) -> List[DataFlow]:
        """Get all flows for an entity."""
        flows = []
        
        for flow in self.flow_cache.values():
            if (flow.source_entity.entity_id == entity_id or 
                flow.target_entity.entity_id == entity_id):
                flows.append(flow)
        
        return flows
    
    async def get_flows_by_type(self, flow_type: FlowType) -> List[DataFlow]:
        """Get flows by type."""
        return [flow for flow in self.flow_cache.values() if flow.flow_type == flow_type]
    
    async def get_flows_by_system(self, system_name: str) -> List[DataFlow]:
        """Get flows by system."""
        return [flow for flow in self.flow_cache.values() 
                if (flow.source_entity.system == system_name or 
                    flow.target_entity.system == system_name)]
    
    async def search_flows(self, 
                          query: str,
                          flow_type: Optional[FlowType] = None,
                          system: Optional[str] = None) -> List[DataFlow]:
        """Search flows based on criteria."""
        results = []
        
        for flow in self.flow_cache.values():
            # Filter by flow type
            if flow_type and flow.flow_type != flow_type:
                continue
            
            # Filter by system
            if system and (flow.source_entity.system != system and 
                          flow.target_entity.system != system):
                continue
            
            # Search in entity names and process names
            if (query.lower() in flow.source_entity.name.lower() or
                query.lower() in flow.target_entity.name.lower() or
                (flow.process_name and query.lower() in flow.process_name.lower())):
                results.append(flow)
        
        return results
    
    async def get_flow_summary(self) -> Dict[str, Any]:
        """Get flow summary."""
        summary = {
            'total_flows': len(self.flow_cache),
            'total_entities': len(self.entity_cache),
            'systems': {},
            'flow_types': {},
            'entities_by_system': {},
            'graph_stats': {
                'nodes': self.flow_graph.number_of_nodes(),
                'edges': self.flow_graph.number_of_edges(),
                'is_connected': nx.is_connected(self.flow_graph.to_undirected())
            }
        }
        
        for flow in self.flow_cache.values():
            # Count by systems
            source_system = flow.source_entity.system
            target_system = flow.target_entity.system
            
            if source_system not in summary['systems']:
                summary['systems'][source_system] = 0
            summary['systems'][source_system] += 1
            
            if target_system != source_system:
                if target_system not in summary['systems']:
                    summary['systems'][target_system] = 0
                summary['systems'][target_system] += 1
            
            # Count by flow type
            flow_type = flow.flow_type.value
            if flow_type not in summary['flow_types']:
                summary['flow_types'][flow_type] = 0
            summary['flow_types'][flow_type] += 1
        
        # Count entities by system
        for entity in self.entity_cache.values():
            system = entity.system
            if system not in summary['entities_by_system']:
                summary['entities_by_system'][system] = 0
            summary['entities_by_system'][system] += 1
        
        return summary
    
    async def export_flows(self, format: str = 'json') -> str:
        """Export flows in specified format."""
        if format.lower() == 'json':
            flows_list = [flow.to_dict() for flow in self.flow_cache.values()]
            return json.dumps(flows_list, indent=2, default=str)
        
        elif format.lower() == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow([
                'flow_id', 'source_entity', 'target_entity', 'flow_type',
                'direction', 'process_name', 'confidence_score', 'timestamp'
            ])
            
            # Write data
            for flow in self.flow_cache.values():
                writer.writerow([
                    flow.flow_id,
                    flow.source_entity.name,
                    flow.target_entity.name,
                    flow.flow_type.value,
                    flow.direction.value,
                    flow.process_name or '',
                    flow.confidence_score,
                    flow.timestamp.isoformat()
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def visualize_flows(self, entity_id: Optional[str] = None) -> Dict[str, Any]:
        """Generate visualization data for flows."""
        nodes = []
        edges = []
        
        if entity_id:
            # Get subgraph around specific entity
            if entity_id in self.flow_graph:
                # Get neighbors within 2 hops
                subgraph_nodes = set([entity_id])
                for neighbor in self.flow_graph.neighbors(entity_id):
                    subgraph_nodes.add(neighbor)
                    for second_neighbor in self.flow_graph.neighbors(neighbor):
                        subgraph_nodes.add(second_neighbor)
                
                subgraph = self.flow_graph.subgraph(subgraph_nodes)
            else:
                subgraph = nx.DiGraph()
        else:
            subgraph = self.flow_graph
        
        # Generate nodes
        for node_id in subgraph.nodes():
            entity = self.entity_cache.get(node_id)
            if entity:
                nodes.append({
                    'id': node_id,
                    'label': entity.name,
                    'type': entity.entity_type,
                    'system': entity.system,
                    'size': subgraph.degree(node_id)
                })
        
        # Generate edges
        for source, target in subgraph.edges():
            edge_data = subgraph.get_edge_data(source, target)
            flow = edge_data.get('flow') if edge_data else None
            
            if flow:
                edges.append({
                    'source': source,
                    'target': target,
                    'type': flow.flow_type.value,
                    'weight': flow.confidence_score,
                    'label': flow.process_name or flow.flow_type.value
                })
        
        return {
            'nodes': nodes,
            'edges': edges,
            'stats': {
                'node_count': len(nodes),
                'edge_count': len(edges)
            }
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get mapping statistics."""
        return {
            **self.stats,
            'cached_flows': len(self.flow_cache),
            'cached_entities': len(self.entity_cache),
            'graph_nodes': self.flow_graph.number_of_nodes(),
            'graph_edges': self.flow_graph.number_of_edges(),
            'mapping_history_count': len(self.mapping_history)
        }
    
    def get_mapping_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get mapping history."""
        history = sorted(self.mapping_history, key=lambda x: x['timestamp'], reverse=True)
        
        if limit:
            history = history[:limit]
        
        return history
    
    async def clear_cache(self):
        """Clear all caches."""
        self.flow_cache.clear()
        self.entity_cache.clear()
        self.flow_graph.clear()
        logger.info("Flow mapper cache cleared")
    
    async def refresh_flows(self, system_name: Optional[str] = None):
        """Refresh flows from systems."""
        if system_name:
            if system_name in self.mappers:
                mapper = self.mappers[system_name]
                flows = await mapper.discover_flows()
                
                # Remove old flows from this system
                flows_to_remove = [
                    flow_id for flow_id, flow in self.flow_cache.items()
                    if (flow.source_entity.system == system_name or 
                        flow.target_entity.system == system_name)
                ]
                
                for flow_id in flows_to_remove:
                    del self.flow_cache[flow_id]
                
                # Add new flows
                for flow in flows:
                    await self.cache_flow(flow)
                    await self.add_flow_to_graph(flow)
            else:
                raise ValueError(f"No mapper registered for system: {system_name}")
        else:
            await self.discover_all_flows()
        
        logger.info("Flows refreshed")


def create_data_flow_mapper() -> DataFlowMapper:
    """Factory function to create data flow mapper."""
    return DataFlowMapper()


def create_data_entity(entity_id: str, name: str, entity_type: str, system: str, **kwargs) -> DataEntity:
    """Factory function to create data entity."""
    return DataEntity(
        entity_id=entity_id,
        name=name,
        entity_type=entity_type,
        system=system,
        **kwargs
    )


def create_data_flow(flow_id: str,
                    source_entity: DataEntity,
                    target_entity: DataEntity,
                    flow_type: Union[FlowType, str],
                    **kwargs) -> DataFlow:
    """Factory function to create data flow."""
    if isinstance(flow_type, str):
        flow_type = FlowType(flow_type.lower())
    
    return DataFlow(
        flow_id=flow_id,
        source_entity=source_entity,
        target_entity=target_entity,
        flow_type=flow_type,
        **kwargs
    )
