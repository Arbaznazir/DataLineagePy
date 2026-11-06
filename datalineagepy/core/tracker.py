"""
LineageTracker - Core class for tracking data lineage in pandas and PySpark workflows.
"""

import uuid
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import pandas as pd

from .nodes import DataNode, FileNode, DatabaseNode
from .edges import LineageEdge
from .operations import Operation


class LineageTracker:
    """
    Main class for tracking data lineage across pandas and PySpark operations.

    This tracker maintains a graph of data transformations, capturing:
    - Data sources (files, databases, APIs)
    - Transformations (operations, functions)
    - Data sinks (output files, databases)
    - Column-level lineage
    """

    def __init__(self, name: str = "default"):
        """
        Initialize a new LineageTracker.

        Args:
            name: Name identifier for this tracker instance
        """
        self.name = name
        self.id = str(uuid.uuid4())
        self.created_at = datetime.now()

        # Graph storage
        self.nodes: Dict[str, DataNode] = {}
        self.edges: List[LineageEdge] = []
        self.operations: List[Operation] = []

        # Tracking state
        self.active = True
        self._current_operation = None

    def create_node(self,
                    node_type: str,
                    name: str,
                    metadata: Optional[Dict] = None) -> DataNode:
        """
        Create a new data node in the lineage graph.

        Args:
            node_type: Type of node ('data', 'file', 'database')
            name: Unique name for the node
            metadata: Additional metadata about the node

        Returns:
            Created DataNode instance
        """
        if node_type == 'file':
            node = FileNode(name, metadata or {})
        elif node_type == 'database':
            node = DatabaseNode(name, metadata or {})
        else:
            node = DataNode(name, metadata or {})

        self.nodes[node.id] = node
        return node

    def add_edge(self,
                 source_node: DataNode,
                 target_node: DataNode,
                 operation: Optional[Operation] = None,
                 metadata: Optional[Dict] = None) -> LineageEdge:
        """
        Add a lineage edge between two nodes.

        Args:
            source_node: Source data node
            target_node: Target data node  
            operation: Operation that created this edge
            metadata: Additional edge metadata

        Returns:
            Created LineageEdge instance
        """
        edge = LineageEdge(
            source_id=source_node.id,
            target_id=target_node.id,
            operation=operation,
            metadata=metadata or {}
        )

        self.edges.append(edge)
        return edge

    def track_operation(self,
                        operation_type: str,
                        inputs: List[DataNode],
                        outputs: List[DataNode],
                        metadata: Optional[Dict] = None,
                        column_lineage: Optional[Dict[str, List[str]]] = None) -> Operation:
        """
        Track a data operation with its inputs and outputs.

        Args:
            operation_type: Type of operation (e.g., 'merge', 'filter', 'aggregate')
            inputs: List of input data nodes
            outputs: List of output data nodes
            metadata: Additional operation metadata
            column_lineage: Mapping of output columns to input columns that created them

        Returns:
            Created Operation instance
        """
        operation = Operation(
            operation_type=operation_type,
            inputs=[node.id for node in inputs],
            outputs=[node.id for node in outputs],
            metadata=metadata or {}
        )

        # Add column lineage information
        if column_lineage:
            operation.add_parameter('column_lineage', column_lineage)

        self.operations.append(operation)

        # Create edges for this operation
        for input_node in inputs:
            for output_node in outputs:
                edge_metadata = {}
                if column_lineage:
                    edge_metadata['column_lineage'] = column_lineage
                self.add_edge(input_node, output_node,
                              operation, edge_metadata)

        return operation

    def enhance_operation_metadata(self,
                                   operation: Operation,
                                   additional_metadata: Optional[Dict] = None) -> None:
        """
        Enhance operation metadata with detailed logging information.

        Args:
            operation: Operation to enhance
            additional_metadata: Additional metadata to include
        """
        # Capture execution context
        execution_metadata = {
            'execution_timestamp': datetime.now().isoformat(),
            'operation_sequence': len(self.operations),
            'input_count': len(operation.inputs),
            'output_count': len(operation.outputs)
        }

        # Add data size information if available
        for input_id in operation.inputs:
            if input_id in self.nodes:
                node = self.nodes[input_id]
                if hasattr(node, 'shape'):
                    execution_metadata[f'input_{input_id}_shape'] = getattr(
                        node, 'shape', 'unknown')
                if hasattr(node, 'columns'):
                    execution_metadata[f'input_{input_id}_columns'] = len(
                        getattr(node, 'columns', []))

        for output_id in operation.outputs:
            if output_id in self.nodes:
                node = self.nodes[output_id]
                if hasattr(node, 'shape'):
                    execution_metadata[f'output_{output_id}_shape'] = getattr(
                        node, 'shape', 'unknown')
                if hasattr(node, 'columns'):
                    execution_metadata[f'output_{output_id}_columns'] = len(
                        getattr(node, 'columns', []))

        # Add performance metadata placeholder (can be enhanced with actual timing)
        performance_metadata = {
            # Can be calculated based on operation type and data size
            'estimated_complexity': 'medium',
            'memory_impact': 'moderate',       # Can be measured in practice
            'io_operations': operation.operation_type in ['read_csv', 'to_csv', 'read_json', 'to_json']
        }

        # Merge all metadata
        enhanced_metadata = {
            **operation.metadata,
            'execution_context': execution_metadata,
            'performance_info': performance_metadata
        }

        if additional_metadata:
            enhanced_metadata.update(additional_metadata)

        operation.metadata = enhanced_metadata

    def log_operation_details(self,
                              operation_type: str,
                              inputs: List[DataNode],
                              outputs: List[DataNode],
                              parameters: Optional[Dict] = None,
                              timing_info: Optional[Dict] = None) -> Operation:
        """
        Log detailed operation information with comprehensive metadata.

        Args:
            operation_type: Type of operation
            inputs: Input nodes
            outputs: Output nodes
            parameters: Operation parameters
            timing_info: Optional timing information

        Returns:
            Enhanced Operation with detailed metadata
        """
        # Create the operation with enhanced metadata
        metadata = {
            'operation_details': {
                'type': operation_type,
                'input_nodes': [{'id': node.id, 'name': node.name} for node in inputs],
                'output_nodes': [{'id': node.id, 'name': node.name} for node in outputs],
                'parameters': parameters or {},
                'logged_at': datetime.now().isoformat()
            }
        }

        if timing_info:
            metadata['performance'] = timing_info

        operation = self.track_operation(
            operation_type=operation_type,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata
        )

        # Enhance with additional context
        self.enhance_operation_metadata(operation)

        return operation

    def get_lineage(self, node_id: str, direction: str = 'both') -> Dict:
        """
        Get lineage information for a specific node.

        Args:
            node_id: ID of the node to trace
            direction: Direction to trace ('upstream', 'downstream', 'both')

        Returns:
            Dictionary containing lineage information
        """
        if node_id not in self.nodes:
            raise ValueError(f"Node {node_id} not found in tracker")

        result = {
            'node': self.nodes[node_id].to_dict(),
            'upstream': [],
            'downstream': []
        }

        if direction in ['upstream', 'both']:
            result['upstream'] = self._get_upstream_nodes(node_id)

        if direction in ['downstream', 'both']:
            result['downstream'] = self._get_downstream_nodes(node_id)

        return result

    def _get_upstream_nodes(self, node_id: str) -> List[Dict]:
        """Get all upstream nodes for a given node."""
        upstream = []
        visited = set()

        def traverse_upstream(current_id):
            if current_id in visited:
                return
            visited.add(current_id)

            for edge in self.edges:
                if edge.target_id == current_id:
                    source_node = self.nodes[edge.source_id]
                    upstream.append({
                        'node': source_node.to_dict(),
                        'edge': edge.to_dict()
                    })
                    traverse_upstream(edge.source_id)

        traverse_upstream(node_id)
        return upstream

    def _get_downstream_nodes(self, node_id: str) -> List[Dict]:
        """Get all downstream nodes for a given node."""
        downstream = []
        visited = set()

        def traverse_downstream(current_id):
            if current_id in visited:
                return
            visited.add(current_id)

            for edge in self.edges:
                if edge.source_id == current_id:
                    target_node = self.nodes[edge.target_id]
                    downstream.append({
                        'node': target_node.to_dict(),
                        'edge': edge.to_dict()
                    })
                    traverse_downstream(edge.target_id)

        traverse_downstream(node_id)
        return downstream

    def track_column_lineage(self,
                             source_node: DataNode,
                             target_node: DataNode,
                             column_mapping: Dict[str, List[str]],
                             operation_type: str = "column_transform") -> None:
        """
        Track column-level lineage between nodes.

        Args:
            source_node: Source data node
            target_node: Target data node  
            column_mapping: Dict mapping target columns to source columns
            operation_type: Type of operation that created this mapping
        """
        for target_col, source_cols in column_mapping.items():
            metadata = {
                'target_column': target_col,
                'source_columns': source_cols,
                'operation_type': operation_type
            }
            edge = self.add_edge(source_node, target_node, None, metadata)

    def search_lineage(self,
                       query: str,
                       search_type: str = "node_name") -> List[Dict]:
        """
        Search for lineage elements based on various criteria.

        Args:
            query: Search query string
            search_type: Type of search ('node_name', 'column_name', 'operation_type')

        Returns:
            List of matching elements
        """
        results = []
        query_lower = query.lower()

        if search_type == "node_name":
            for node_id, node in self.nodes.items():
                if query_lower in node.name.lower():
                    lineage = self.get_lineage(node_id, 'both')
                    results.append({
                        'type': 'node',
                        'node': node.to_dict(),
                        'lineage': lineage
                    })

        elif search_type == "column_name":
            for node_id, node in self.nodes.items():
                if hasattr(node, 'columns'):
                    matching_cols = [
                        col for col in node.columns if query_lower in col.lower()]
                    if matching_cols:
                        results.append({
                            'type': 'column',
                            'node': node.to_dict(),
                            'matching_columns': matching_cols,
                            'lineage': self.get_lineage(node_id, 'both')
                        })

        elif search_type == "operation_type":
            for operation in self.operations:
                if query_lower in operation.operation_type.lower():
                    results.append({
                        'type': 'operation',
                        'operation': operation.to_dict(),
                        'input_nodes': [self.nodes[nid].to_dict() for nid in operation.inputs if nid in self.nodes],
                        'output_nodes': [self.nodes[nid].to_dict() for nid in operation.outputs if nid in self.nodes]
                    })

        return results

    def track_error(self,
                    node_id: str,
                    error_message: str,
                    error_type: str = "unknown",
                    operation_id: Optional[str] = None) -> None:
        """
        Track an error that occurred during data processing.

        Args:
            node_id: ID of the node where error occurred
            error_message: Description of the error
            error_type: Type of error (e.g., 'validation', 'processing', 'connection')
            operation_id: ID of the operation that caused the error
        """
        if node_id in self.nodes:
            node = self.nodes[node_id]
            if 'errors' not in node.metadata:
                node.metadata['errors'] = []

            error_info = {
                'timestamp': datetime.now().isoformat(),
                'message': error_message,
                'type': error_type,
                'operation_id': operation_id
            }
            node.metadata['errors'].append(error_info)

    def propagate_error_analysis(self, node_id: str) -> Dict[str, Any]:
        """
        Analyze error propagation from a node through the lineage graph.

        Args:
            node_id: Starting node for error analysis

        Returns:
            Error propagation analysis results
        """
        if node_id not in self.nodes:
            return {'error': f'Node {node_id} not found'}

        # Get all downstream nodes
        downstream = self._get_downstream_nodes(node_id)

        analysis = {
            'source_node': self.nodes[node_id].to_dict(),
            'potential_impact': [],
            'error_chain': []
        }

        # Check for existing errors in the source node
        source_errors = self.nodes[node_id].metadata.get('errors', [])
        if source_errors:
            analysis['source_errors'] = source_errors

        # Analyze downstream impact
        for item in downstream:
            node_data = item['node']
            if 'errors' in node_data.get('metadata', {}):
                analysis['error_chain'].append({
                    'node': node_data,
                    'errors': node_data['metadata']['errors']
                })
            else:
                analysis['potential_impact'].append(node_data)

        return analysis

    def auto_generate_step_names(self) -> None:
        """
        Automatically generate meaningful names for operations based on their context and parameters.
        Enhanced with intelligent naming based on operation details.
        """
        for operation in self.operations:
            if not operation.metadata.get('auto_named', False):
                # Generate name based on operation type and context
                op_type = operation.operation_type
                input_count = len(operation.inputs)
                output_count = len(operation.outputs)

                # Get input and output node names for context
                input_names = []
                output_names = []

                for input_id in operation.inputs:
                    if input_id in self.nodes:
                        input_names.append(self.nodes[input_id].name)

                for output_id in operation.outputs:
                    if output_id in self.nodes:
                        output_names.append(self.nodes[output_id].name)

                # Enhanced naming logic
                if op_type == 'merge' or op_type == 'join':
                    if len(input_names) >= 2:
                        name = f"Join {input_names[0]} with {input_names[1]}"
                    else:
                        name = f"Merge {input_count} datasets"

                elif op_type == 'filter':
                    if input_names and 'filter_condition' in operation.metadata:
                        condition = operation.metadata['filter_condition']
                        name = f"Filter {input_names[0]} where {condition}"
                    else:
                        name = f"Filter {input_names[0] if input_names else 'data'}"

                elif op_type == 'aggregate' or op_type == 'groupby':
                    group_cols = operation.metadata.get('group_columns', [])
                    agg_cols = operation.metadata.get('agg_columns', [])
                    if group_cols and agg_cols:
                        name = f"Group {input_names[0] if input_names else 'data'} by {', '.join(group_cols[:2])}"
                    else:
                        name = f"Aggregate {input_names[0] if input_names else 'data'}"

                elif op_type == 'transform' or op_type == 'assign':
                    new_cols = operation.metadata.get('new_columns', [])
                    if new_cols:
                        name = f"Add columns {', '.join(new_cols[:2])} to {input_names[0] if input_names else 'data'}"
                    else:
                        name = f"Transform {input_names[0] if input_names else 'data'}"

                elif op_type == 'select':
                    selected_cols = operation.metadata.get(
                        'selected_columns', [])
                    if selected_cols:
                        name = f"Select {len(selected_cols)} columns from {input_names[0] if input_names else 'data'}"
                    else:
                        name = f"Select columns from {input_names[0] if input_names else 'data'}"

                elif op_type == 'sort' or op_type == 'sort_values':
                    sort_cols = operation.metadata.get('sort_columns', [])
                    if sort_cols:
                        name = f"Sort {input_names[0] if input_names else 'data'} by {', '.join(sort_cols[:2])}"
                    else:
                        name = f"Sort {input_names[0] if input_names else 'data'}"

                elif op_type in ['read_csv', 'read_json', 'read_parquet']:
                    file_path = operation.metadata.get('file_path', '')
                    if file_path:
                        filename = file_path.split('/')[-1]
                        name = f"Load {filename}"
                    else:
                        name = f"Load {op_type.split('_')[1].upper()} file"

                elif op_type in ['to_csv', 'to_json', 'to_parquet']:
                    file_path = operation.metadata.get('file_path', '')
                    if file_path:
                        filename = file_path.split('/')[-1]
                        name = f"Save {input_names[0] if input_names else 'data'} to {filename}"
                    else:
                        name = f"Export {input_names[0] if input_names else 'data'} to {op_type.split('_')[1].upper()}"

                elif op_type == 'dropna':
                    name = f"Remove nulls from {input_names[0] if input_names else 'data'}"

                elif op_type == 'drop_duplicates':
                    name = f"Remove duplicates from {input_names[0] if input_names else 'data'}"

                elif op_type == 'fillna':
                    fill_value = operation.metadata.get(
                        'fill_value', 'default')
                    name = f"Fill nulls in {input_names[0] if input_names else 'data'} with {fill_value}"

                else:
                    # Fallback naming
                    if input_names:
                        name = f"{op_type.title().replace('_', ' ')} on {input_names[0]}"
                    else:
                        name = f"{op_type.title().replace('_', ' ')} operation"

                operation.add_parameter('generated_name', name)
                operation.metadata['auto_named'] = True
                operation.metadata['naming_context'] = {
                    'input_names': input_names,
                    'output_names': output_names,
                    'operation_details': operation.metadata.copy()
                }

    def register_custom_hook(self,
                             hook_type: str,
                             hook_function: callable) -> None:
        """
        Register a custom hook function for lineage events.

        Args:
            hook_type: Type of hook ('pre_operation', 'post_operation', 'error')
            hook_function: Function to call when hook is triggered
        """
        if not hasattr(self, '_custom_hooks'):
            self._custom_hooks = {}

        if hook_type not in self._custom_hooks:
            self._custom_hooks[hook_type] = []

        self._custom_hooks[hook_type].append(hook_function)

    def trigger_hooks(self, hook_type: str, **kwargs) -> None:
        """
        Trigger registered hooks of a specific type.

        Args:
            hook_type: Type of hook to trigger
            **kwargs: Arguments to pass to hook functions
        """
        if hasattr(self, '_custom_hooks') and hook_type in self._custom_hooks:
            for hook_func in self._custom_hooks[hook_type]:
                try:
                    hook_func(self, **kwargs)
                except Exception as e:
                    # Log hook errors but don't break main flow
                    self.track_error(
                        kwargs.get('node_id', 'unknown'),
                        f"Hook error: {str(e)}",
                        'hook_execution'
                    )

    def mask_sensitive_data(self,
                            column_patterns: List[str],
                            mask_value: str = "***MASKED***") -> None:
        """
        Mask sensitive data in column names and schemas for PII protection.

        Args:
            column_patterns: List of regex patterns for sensitive columns
            mask_value: Value to replace sensitive data with
        """
        import re

        compiled_patterns = [re.compile(pattern, re.IGNORECASE)
                             for pattern in column_patterns]

        for node_id, node in self.nodes.items():
            if hasattr(node, 'schema'):
                new_schema = {}
                for col_name, col_type in node.schema.items():
                    # Check if column name matches any sensitive pattern
                    is_sensitive = any(pattern.search(col_name)
                                       for pattern in compiled_patterns)
                    if is_sensitive:
                        new_schema[mask_value] = col_type
                        # Track that masking was applied
                        if 'masked_columns' not in node.metadata:
                            node.metadata['masked_columns'] = []
                        node.metadata['masked_columns'].append(col_name)
                    else:
                        new_schema[col_name] = col_type

                node.set_schema(new_schema)

    def get_stats(self) -> Dict:
        """
        Get statistics about the current lineage graph.

        Returns:
            Dictionary with graph statistics
        """
        return {
            'tracker_id': self.id,
            'tracker_name': self.name,
            'created_at': self.created_at.isoformat(),
            'total_nodes': len(self.nodes),
            'total_edges': len(self.edges),
            'total_operations': len(self.operations),
            'node_types': self._count_node_types(),
            'operation_types': self._count_operation_types()
        }

    def _count_node_types(self) -> Dict[str, int]:
        """Count nodes by type."""
        counts = {}
        for node in self.nodes.values():
            node_type = type(node).__name__
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts

    def _count_operation_types(self) -> Dict[str, int]:
        """Count operations by type."""
        counts = {}
        for operation in self.operations:
            op_type = operation.operation_type
            counts[op_type] = counts.get(op_type, 0) + 1
        return counts

    def export_graph(self, format: str = 'dict', output_file: Optional[str] = None) -> Any:
        """
        Export the lineage graph in various formats.

        Args:
            format: Export format ('dict', 'json', 'dot', 'networkx')
            output_file: Optional file path to save the export

        Returns:
            Graph data in specified format
        """
        graph_data = {
            'metadata': self.get_stats(),
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [edge.to_dict() for edge in self.edges],
            'operations': [op.to_dict() for op in self.operations]
        }

        if format == 'dict':
            if output_file:
                import json
                with open(output_file, 'w') as f:
                    json.dump(graph_data, f, indent=2, default=str)
            return graph_data

        elif format == 'json':
            import json
            json_str = json.dumps(graph_data, indent=2, default=str)
            if output_file:
                with open(output_file, 'w') as f:
                    f.write(json_str)
            return json_str

        elif format == 'dot':
            dot_lines = ['digraph lineage {']
            dot_lines.append('  rankdir=TB;')
            dot_lines.append('  node [shape=box, style=filled];')

            # Add nodes
            for node in self.nodes.values():
                node_type = getattr(node, 'node_type', 'data')
                color = 'lightblue' if node_type == 'file' else 'lightgreen' if node_type == 'database' else 'lightcoral'
                dot_lines.append(
                    f'  "{node.id}" [label="{node.name}", fillcolor={color}];')

            # Add edges
            for edge in self.edges:
                operation = edge.operation.operation_type if edge.operation else 'unknown'
                dot_lines.append(
                    f'  "{edge.source_id}" -> "{edge.target_id}" [label="{operation}"];')

            dot_lines.append('}')
            dot_content = '\n'.join(dot_lines)

            if output_file:
                with open(output_file, 'w') as f:
                    f.write(dot_content)
            return dot_content

        elif format == 'networkx':
            import networkx as nx
            graph = nx.DiGraph()
            for node_id, node in self.nodes.items():
                graph.add_node(node_id, **node.to_dict())
            for edge in self.edges:
                graph.add_edge(edge.source_id, edge.target_id,
                               **edge.to_dict())
            return graph

        else:
            raise ValueError(f"Unsupported export format: {format}")

    def export_lineage(self, output_file: str, format: Optional[str] = None) -> str:
        """Write the lineage graph to disk.

        This is the documented quick-start entry point. ``export_graph`` remains
        available when callers need the graph returned in memory.

        Args:
            output_file: Destination path. ``.json`` and ``.dot`` suffixes
                select the format when ``format`` is omitted.
            format: Optional export format (``json``, ``dict``, ``dot``).

        Returns:
            The path that was written.
        """
        if format is None:
            lower = output_file.lower()
            if lower.endswith(".dot"):
                format = "dot"
            else:
                format = "json"
        self.export_graph(format=format, output_file=output_file)
        return output_file

    def visualize(self, output_file: str = "lineage.html") -> str:
        """Write an HTML view of the lineage graph.

        Uses the Plotly visualizer when that extra is installed. Otherwise
        writes a self-contained HTML page so the quick start still runs.

        Args:
            output_file: Destination HTML path.

        Returns:
            The path that was written.
        """
        try:
            from ..visualization.graph_visualizer import GraphVisualizer
        except ImportError:
            html = self._simple_lineage_html()
            with open(output_file, "w", encoding="utf-8") as handle:
                handle.write(html)
            return output_file

        GraphVisualizer(self).generate_html(output_file=output_file)
        return output_file

    def _simple_lineage_html(self) -> str:
        """Render lineage as HTML without optional visualization libraries."""
        import html as html_lib

        node_rows = []
        for node in self.nodes.values():
            columns = ", ".join(node.columns) if node.columns else "—"
            node_rows.append(
                "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
                    html_lib.escape(str(node.name)),
                    html_lib.escape(getattr(node, "node_type", "data")),
                    html_lib.escape(columns),
                )
            )

        edge_items = []
        id_to_name = {node.id: node.name for node in self.nodes.values()}
        for edge in self.edges:
            operation = edge.operation.operation_type if edge.operation else "unknown"
            source = id_to_name.get(edge.source_id, edge.source_id)
            target = id_to_name.get(edge.target_id, edge.target_id)
            edge_items.append(
                "<li>{} &rarr; {} <em>({})</em></li>".format(
                    html_lib.escape(str(source)),
                    html_lib.escape(str(target)),
                    html_lib.escape(str(operation)),
                )
            )

        if not node_rows:
            node_rows.append("<tr><td colspan='3'>No lineage nodes yet</td></tr>")
        if not edge_items:
            edge_items.append("<li>No transformations recorded</li>")

        return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{title} lineage</title>
  <style>
    body {{ font-family: sans-serif; margin: 2rem; color: #1f2933; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border: 1px solid #d9e2ec; padding: 0.5rem 0.75rem; text-align: left; }}
    th {{ background: #f0f4f8; }}
  </style>
</head>
<body>
  <h1>{title}</h1>
  <p>{stats}</p>
  <h2>Nodes</h2>
  <table>
    <thead><tr><th>Name</th><th>Type</th><th>Columns</th></tr></thead>
    <tbody>
      {nodes}
    </tbody>
  </table>
  <h2>Transformations</h2>
  <ul>
    {edges}
  </ul>
</body>
</html>
""".format(
            title=html_lib.escape(self.name),
            stats=html_lib.escape(
                "{} nodes, {} edges".format(len(self.nodes), len(self.edges))
            ),
            nodes="\n".join(node_rows),
            edges="\n".join(edge_items),
        )

    def get_lineage_graph(self, format: str = 'dict') -> Any:
        """
        Get the complete lineage graph structure.

        This method provides a simplified interface to access the lineage graph,
        building on the existing export_graph functionality.

        Args:
            format: Format to return the graph in ('dict', 'json', 'networkx', 'ai_ready')

        Returns:
            Graph data in the specified format
        """
        if format == 'ai_ready':
            return self.export_ai_ready_format()
        elif format in ['dict', 'json', 'networkx']:
            return self.export_graph(format=format)
        else:
            raise ValueError(
                f"Unsupported format: {format}. Use 'dict', 'json', 'networkx', or 'ai_ready'")

    def export_ai_ready_format(self) -> Dict:
        """
        Export lineage data in AI-ready format optimized for LLM consumption.

        This format includes structured examples, natural language descriptions,
        and training-friendly data representations.

        Returns:
            Dictionary with AI-ready lineage data
        """
        # Generate natural language descriptions
        nl_descriptions = self._generate_natural_language_descriptions()

        # Create structured examples
        examples = self._generate_structured_examples()

        # Create relationship patterns
        patterns = self._extract_lineage_patterns()

        # Create column-level mappings
        column_mappings = self._generate_column_mappings()

        ai_ready_data = {
            'metadata': {
                'format': 'ai_ready',
                'version': '1.0',
                'generated_at': datetime.now().isoformat(),
                'tracker_info': self.get_stats(),
                'description': f"AI-ready lineage data for '{self.name}' with {len(self.nodes)} nodes and {len(self.edges)} edges"
            },

            'natural_language': {
                'summary': nl_descriptions['summary'],
                'step_descriptions': nl_descriptions['steps'],
                'data_flow_narrative': nl_descriptions['narrative'],
                'transformation_descriptions': nl_descriptions['transformations']
            },

            'structured_examples': {
                'input_output_pairs': examples['io_pairs'],
                'transformation_examples': examples['transformations'],
                'column_transformation_examples': examples['column_transforms'],
                'error_examples': examples.get('errors', [])
            },

            'patterns': {
                'common_operations': patterns['operations'],
                'data_flow_patterns': patterns['flows'],
                'transformation_patterns': patterns['transformations'],
                'dependency_patterns': patterns['dependencies']
            },

            'column_lineage': {
                'mappings': column_mappings['mappings'],
                'transformations': column_mappings['transformations'],
                'derivations': column_mappings['derivations']
            },

            'training_data': {
                'question_answer_pairs': self._generate_qa_pairs(),
                'code_examples': self._generate_code_examples(),
                'explanation_templates': self._generate_explanation_templates()
            },

            'graph_structure': {
                'nodes': [self._node_to_ai_format(node) for node in self.nodes.values()],
                'edges': [self._edge_to_ai_format(edge) for edge in self.edges],
                'operations': [self._operation_to_ai_format(op) for op in self.operations]
            }
        }

        return ai_ready_data

    def _generate_natural_language_descriptions(self) -> Dict:
        """Generate natural language descriptions of the lineage."""
        descriptions = {
            'summary': f"This data lineage tracks {len(self.nodes)} data sources through {len(self.operations)} operations.",
            'steps': [],
            'narrative': "",
            'transformations': []
        }

        # Generate step descriptions
        for i, operation in enumerate(self.operations):
            input_names = [
                self.nodes[nid].name for nid in operation.inputs if nid in self.nodes]
            output_names = [
                self.nodes[nid].name for nid in operation.outputs if nid in self.nodes]

            step_desc = f"Step {i+1}: {operation.operation_type.replace('_', ' ').title()}"
            if input_names:
                step_desc += f" on {', '.join(input_names)}"
            if output_names:
                step_desc += f" producing {', '.join(output_names)}"

            descriptions['steps'].append({
                'step_number': i+1,
                'operation_type': operation.operation_type,
                'description': step_desc,
                'inputs': input_names,
                'outputs': output_names
            })

        # Generate narrative
        if descriptions['steps']:
            narrative_parts = []
            narrative_parts.append(
                f"The data pipeline begins with {len([op for op in self.operations if 'read' in op.operation_type])} data sources.")
            narrative_parts.append(
                f"Data flows through {len(self.operations)} transformation steps.")

            # Identify key transformation types
            transform_types = [op.operation_type for op in self.operations]
            unique_types = list(set(transform_types))
            if unique_types:
                narrative_parts.append(
                    f"Key operations include: {', '.join(unique_types[:5])}.")

            descriptions['narrative'] = ' '.join(narrative_parts)

        return descriptions

    def _generate_structured_examples(self) -> Dict:
        """Generate structured examples for training."""
        examples = {
            'io_pairs': [],
            'transformations': [],
            'column_transforms': [],
            'errors': []
        }

        # Input-output pairs
        for operation in self.operations:
            input_nodes = [self.nodes[nid]
                           for nid in operation.inputs if nid in self.nodes]
            output_nodes = [self.nodes[nid]
                            for nid in operation.outputs if nid in self.nodes]

            io_example = {
                'operation': operation.operation_type,
                'inputs': [{'name': node.name, 'type': getattr(node, 'node_type', 'data')} for node in input_nodes],
                'outputs': [{'name': node.name, 'type': getattr(node, 'node_type', 'data')} for node in output_nodes],
                'description': f"Operation '{operation.operation_type}' transforms {len(input_nodes)} input(s) into {len(output_nodes)} output(s)"
            }
            examples['io_pairs'].append(io_example)

        return examples

    def _extract_lineage_patterns(self) -> Dict:
        """Extract common patterns from the lineage graph."""
        patterns = {
            'operations': {},
            'flows': [],
            'transformations': [],
            'dependencies': []
        }

        # Count operation types
        for operation in self.operations:
            op_type = operation.operation_type
            patterns['operations'][op_type] = patterns['operations'].get(
                op_type, 0) + 1

        # Extract flow patterns
        for edge in self.edges:
            source_node = self.nodes.get(edge.source_id)
            target_node = self.nodes.get(edge.target_id)

            if source_node and target_node:
                flow_pattern = {
                    'source_type': getattr(source_node, 'node_type', 'data'),
                    'target_type': getattr(target_node, 'node_type', 'data'),
                    'operation': edge.operation.operation_type if edge.operation else 'unknown'
                }
                patterns['flows'].append(flow_pattern)

        return patterns

    def _generate_column_mappings(self) -> Dict:
        """Generate column-level lineage mappings."""
        mappings = {
            'mappings': [],
            'transformations': [],
            'derivations': []
        }

        # Extract column lineage from edges
        for edge in self.edges:
            if 'column_lineage' in edge.metadata:
                col_lineage = edge.metadata['column_lineage']
                for target_col, source_cols in col_lineage.items():
                    mapping = {
                        'target_column': target_col,
                        'source_columns': source_cols,
                        'operation': edge.operation.operation_type if edge.operation else 'unknown',
                        'transformation_type': 'direct' if len(source_cols) == 1 else 'derived'
                    }
                    mappings['mappings'].append(mapping)

        return mappings

    def _generate_qa_pairs(self) -> List[Dict]:
        """Generate question-answer pairs for training."""
        qa_pairs = []

        # Basic lineage questions
        for node_id, node in self.nodes.items():
            qa_pairs.extend([
                {
                    'question': f"What is the source of {node.name}?",
                    'answer': f"The data source for {node.name} is tracked in the lineage graph.",
                    'context': 'source_identification'
                },
                {
                    'question': f"How was {node.name} created?",
                    'answer': f"{node.name} was created through the tracked operations in the pipeline.",
                    'context': 'creation_process'
                }
            ])

        # Operation questions
        for operation in self.operations:
            qa_pairs.append({
                'question': f"What does the {operation.operation_type} operation do?",
                'answer': f"The {operation.operation_type} operation processes {len(operation.inputs)} input(s) to produce {len(operation.outputs)} output(s).",
                'context': 'operation_explanation'
            })

        return qa_pairs[:20]  # Limit to avoid excessive data

    def _generate_code_examples(self) -> List[Dict]:
        """Generate code examples for training."""
        code_examples = []

        # Generate examples based on operations
        for operation in self.operations:
            if operation.operation_type == 'filter':
                code_examples.append({
                    'operation': 'filter',
                    'example': "df_filtered = df[df['column'] > threshold]",
                    'description': "Filter operation to select rows based on condition"
                })
            elif operation.operation_type == 'merge':
                code_examples.append({
                    'operation': 'merge',
                    'example': "df_merged = pd.merge(df1, df2, on='key')",
                    'description': "Merge operation to combine two datasets"
                })
            elif operation.operation_type == 'groupby':
                code_examples.append({
                    'operation': 'groupby',
                    'example': "df_grouped = df.groupby('category').agg({'value': 'sum'})",
                    'description': "Group by operation to aggregate data"
                })

        return code_examples

    def _generate_explanation_templates(self) -> List[Dict]:
        """Generate explanation templates for AI systems."""
        templates = [
            {
                'pattern': 'data_source',
                'template': "The data originates from {source_name} and contains {column_count} columns including {key_columns}.",
                'variables': ['source_name', 'column_count', 'key_columns']
            },
            {
                'pattern': 'transformation',
                'template': "This {operation_type} operation transforms {input_datasets} by {operation_description} to produce {output_dataset}.",
                'variables': ['operation_type', 'input_datasets', 'operation_description', 'output_dataset']
            },
            {
                'pattern': 'column_derivation',
                'template': "Column {target_column} is derived from {source_columns} using {transformation_method}.",
                'variables': ['target_column', 'source_columns', 'transformation_method']
            }
        ]

        return templates

    def _node_to_ai_format(self, node) -> Dict:
        """Convert node to AI-friendly format."""
        return {
            'id': node.id,
            'name': node.name,
            'type': getattr(node, 'node_type', 'data'),
            'description': f"Data node '{node.name}' of type {getattr(node, 'node_type', 'data')}",
            'metadata': node.metadata,
            'columns': getattr(node, 'columns', []),
            'schema': getattr(node, 'schema', {})
        }

    def _edge_to_ai_format(self, edge) -> Dict:
        """Convert edge to AI-friendly format."""
        return {
            'id': edge.id,
            'source': edge.source_id,
            'target': edge.target_id,
            'operation': edge.operation.operation_type if edge.operation else 'unknown',
            'description': f"Data flows from {edge.source_id} to {edge.target_id} via {edge.operation.operation_type if edge.operation else 'unknown'}",
            'metadata': edge.metadata
        }

    def _operation_to_ai_format(self, operation) -> Dict:
        """Convert operation to AI-friendly format."""
        return {
            'id': operation.id,
            'type': operation.operation_type,
            'description': f"Operation of type '{operation.operation_type}' with {len(operation.inputs)} inputs and {len(operation.outputs)} outputs",
            'inputs': operation.inputs,
            'outputs': operation.outputs,
            'metadata': operation.metadata,
            'parameters': getattr(operation, 'parameters', {})
        }

    def clear(self):
        """Clear all tracked lineage data."""
        self.nodes.clear()
        self.edges.clear()
        self.operations.clear()

    def clear_cache(self):
        """Alias for clear() method for memory optimization."""
        self.clear()

    def __str__(self) -> str:
        return f"LineageTracker(name='{self.name}', nodes={len(self.nodes)}, edges={len(self.edges)})"

    def __repr__(self) -> str:
        return self.__str__()


# Global default tracker instance
default_tracker = LineageTracker("global_default")
