"""
Documentation Generator for DataLineagePy

Automatically generates documentation for data lineage graphs, nodes, and operations.
"""

import uuid
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


@dataclass
class DocSection:
    """Represents a section in generated documentation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    content: str = ""
    section_type: str = "text"  # text, code, table, diagram
    metadata: Dict[str, Any] = field(default_factory=dict)
    order: int = 0


@dataclass
class DocTemplate:
    """Template for generating documentation."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    sections: List[DocSection] = field(default_factory=list)
    variables: Dict[str, str] = field(default_factory=dict)
    format: str = "markdown"  # markdown, html, pdf


class DocumentationGenerator:
    """Generates documentation for data lineage components."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.templates: Dict[str, DocTemplate] = {}
        self._lock = threading.RLock()
        
        # Initialize default templates
        self._create_default_templates()
        
        logger.info("DocumentationGenerator initialized")
    
    def _create_default_templates(self) -> None:
        """Create default documentation templates."""
        # Node documentation template
        node_template = DocTemplate(
            name="node_documentation",
            description="Template for documenting data nodes",
            sections=[
                DocSection(
                    title="Overview",
                    content="# {node_name}\n\n{node_description}\n\n**Type:** {node_type}\n**Created:** {created_at}",
                    section_type="text",
                    order=1
                ),
                DocSection(
                    title="Properties",
                    content="## Properties\n\n{properties_table}",
                    section_type="table",
                    order=2
                ),
                DocSection(
                    title="Lineage",
                    content="## Data Lineage\n\n### Upstream Dependencies\n{upstream_nodes}\n\n### Downstream Consumers\n{downstream_nodes}",
                    section_type="text",
                    order=3
                )
            ]
        )
        self.templates["node"] = node_template
        
        # Operation documentation template
        operation_template = DocTemplate(
            name="operation_documentation",
            description="Template for documenting operations",
            sections=[
                DocSection(
                    title="Operation Overview",
                    content="# {operation_name}\n\n{operation_description}\n\n**Type:** {operation_type}\n**Executed:** {execution_time}",
                    section_type="text",
                    order=1
                ),
                DocSection(
                    title="Input/Output",
                    content="## Input Data\n{input_nodes}\n\n## Output Data\n{output_nodes}",
                    section_type="text",
                    order=2
                ),
                DocSection(
                    title="Transformation Logic",
                    content="## Transformation Details\n\n```python\n{transformation_code}\n```",
                    section_type="code",
                    order=3
                )
            ]
        )
        self.templates["operation"] = operation_template
        
        # Lineage graph template
        graph_template = DocTemplate(
            name="graph_documentation",
            description="Template for documenting lineage graphs",
            sections=[
                DocSection(
                    title="Graph Overview",
                    content="# Data Lineage Graph: {graph_name}\n\n{graph_description}\n\n**Nodes:** {node_count}\n**Edges:** {edge_count}",
                    section_type="text",
                    order=1
                ),
                DocSection(
                    title="Node Summary",
                    content="## Node Summary\n\n{node_summary_table}",
                    section_type="table",
                    order=2
                ),
                DocSection(
                    title="Data Flow",
                    content="## Data Flow Diagram\n\n{flow_diagram}",
                    section_type="diagram",
                    order=3
                )
            ]
        )
        self.templates["graph"] = graph_template
    
    def generate_node_documentation(self, node_data: Dict[str, Any]) -> str:
        """Generate documentation for a data node."""
        with self._lock:
            template = self.templates.get("node")
            if not template:
                return self._generate_basic_node_doc(node_data)
            
            variables = {
                "node_name": node_data.get("name", "Unknown Node"),
                "node_description": node_data.get("description", "No description available"),
                "node_type": node_data.get("type", "unknown"),
                "created_at": node_data.get("created_at", "Unknown"),
                "properties_table": self._generate_properties_table(node_data.get("metadata", {})),
                "upstream_nodes": self._format_node_list(node_data.get("upstream", [])),
                "downstream_nodes": self._format_node_list(node_data.get("downstream", []))
            }
            
            return self._render_template(template, variables)
    
    def generate_operation_documentation(self, operation_data: Dict[str, Any]) -> str:
        """Generate documentation for an operation."""
        with self._lock:
            template = self.templates.get("operation")
            if not template:
                return self._generate_basic_operation_doc(operation_data)
            
            variables = {
                "operation_name": operation_data.get("name", "Unknown Operation"),
                "operation_description": operation_data.get("description", "No description available"),
                "operation_type": operation_data.get("type", "unknown"),
                "execution_time": operation_data.get("timestamp", "Unknown"),
                "input_nodes": self._format_node_list(operation_data.get("input_nodes", [])),
                "output_nodes": self._format_node_list(operation_data.get("output_nodes", [])),
                "transformation_code": operation_data.get("code", "# No code available")
            }
            
            return self._render_template(template, variables)
    
    def generate_graph_documentation(self, graph_data: Dict[str, Any]) -> str:
        """Generate documentation for a lineage graph."""
        with self._lock:
            template = self.templates.get("graph")
            if not template:
                return self._generate_basic_graph_doc(graph_data)
            
            nodes = graph_data.get("nodes", [])
            edges = graph_data.get("edges", [])
            
            variables = {
                "graph_name": graph_data.get("name", "Data Lineage Graph"),
                "graph_description": graph_data.get("description", "No description available"),
                "node_count": str(len(nodes)),
                "edge_count": str(len(edges)),
                "node_summary_table": self._generate_node_summary_table(nodes),
                "flow_diagram": self._generate_flow_diagram_placeholder(nodes, edges)
            }
            
            return self._render_template(template, variables)
    
    def _render_template(self, template: DocTemplate, variables: Dict[str, str]) -> str:
        """Render a template with variables."""
        sections = sorted(template.sections, key=lambda s: s.order)
        rendered_content = []
        
        for section in sections:
            content = section.content
            
            # Replace variables
            for var_name, var_value in variables.items():
                content = content.replace(f"{{{var_name}}}", str(var_value))
            
            rendered_content.append(content)
        
        return "\n\n".join(rendered_content)
    
    def _generate_properties_table(self, metadata: Dict[str, Any]) -> str:
        """Generate a properties table from metadata."""
        if not metadata:
            return "No properties available."
        
        table_rows = []
        for key, value in metadata.items():
            table_rows.append(f"| {key} | {value} |")
        
        if not table_rows:
            return "No properties available."
        
        table = "| Property | Value |\n|----------|-------|\n" + "\n".join(table_rows)
        return table
    
    def _format_node_list(self, nodes: List[Dict[str, Any]]) -> str:
        """Format a list of nodes for documentation."""
        if not nodes:
            return "None"
        
        formatted_nodes = []
        for node in nodes:
            name = node.get("name", "Unknown")
            node_type = node.get("type", "unknown")
            formatted_nodes.append(f"- **{name}** ({node_type})")
        
        return "\n".join(formatted_nodes)
    
    def _generate_node_summary_table(self, nodes: List[Dict[str, Any]]) -> str:
        """Generate a summary table of nodes."""
        if not nodes:
            return "No nodes available."
        
        table_rows = []
        for node in nodes:
            name = node.get("name", "Unknown")
            node_type = node.get("type", "unknown")
            description = node.get("description", "No description")[:50] + "..."
            table_rows.append(f"| {name} | {node_type} | {description} |")
        
        table = "| Name | Type | Description |\n|------|------|-------------|\n" + "\n".join(table_rows)
        return table
    
    def _generate_flow_diagram_placeholder(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> str:
        """Generate a placeholder for flow diagram."""
        return f"```\n[Flow diagram with {len(nodes)} nodes and {len(edges)} edges]\n(Diagram generation requires visualization tools)\n```"
    
    def _generate_basic_node_doc(self, node_data: Dict[str, Any]) -> str:
        """Generate basic node documentation without template."""
        name = node_data.get("name", "Unknown Node")
        node_type = node_data.get("type", "unknown")
        description = node_data.get("description", "No description available")
        
        return f"# {name}\n\n**Type:** {node_type}\n\n{description}"
    
    def _generate_basic_operation_doc(self, operation_data: Dict[str, Any]) -> str:
        """Generate basic operation documentation without template."""
        name = operation_data.get("name", "Unknown Operation")
        op_type = operation_data.get("type", "unknown")
        description = operation_data.get("description", "No description available")
        
        return f"# {name}\n\n**Type:** {op_type}\n\n{description}"
    
    def _generate_basic_graph_doc(self, graph_data: Dict[str, Any]) -> str:
        """Generate basic graph documentation without template."""
        name = graph_data.get("name", "Data Lineage Graph")
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])
        
        return f"# {name}\n\n**Nodes:** {len(nodes)}\n**Edges:** {len(edges)}"
    
    def add_template(self, template: DocTemplate) -> None:
        """Add a custom documentation template."""
        with self._lock:
            self.templates[template.name] = template
            logger.info(f"Added documentation template: {template.name}")
    
    def get_template(self, template_name: str) -> Optional[DocTemplate]:
        """Get a documentation template by name."""
        with self._lock:
            return self.templates.get(template_name)
    
    def list_templates(self) -> List[str]:
        """List available template names."""
        with self._lock:
            return list(self.templates.keys())
    
    def generate_batch_documentation(self, items: List[Dict[str, Any]], doc_type: str = "node") -> Dict[str, str]:
        """Generate documentation for multiple items."""
        with self._lock:
            results = {}
            
            for item in items:
                item_id = item.get("id", str(uuid.uuid4()))
                
                if doc_type == "node":
                    doc = self.generate_node_documentation(item)
                elif doc_type == "operation":
                    doc = self.generate_operation_documentation(item)
                elif doc_type == "graph":
                    doc = self.generate_graph_documentation(item)
                else:
                    doc = f"# {item.get('name', 'Unknown')}\n\nUnsupported documentation type: {doc_type}"
                
                results[item_id] = doc
            
            logger.info(f"Generated batch documentation for {len(items)} {doc_type} items")
            return results
    
    def export_documentation(self, content: str, format: str = "markdown", filename: Optional[str] = None) -> bool:
        """Export documentation to file."""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"lineage_documentation_{timestamp}.{format}"
            
            with open(filename, 'w', encoding='utf-8') as f:
                if format == "markdown":
                    f.write(content)
                elif format == "html":
                    html_content = self._markdown_to_html(content)
                    f.write(html_content)
                else:
                    f.write(content)
            
            logger.info(f"Exported documentation to {filename}")
            return True
        
        except Exception as e:
            logger.error(f"Error exporting documentation: {e}")
            return False
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown to HTML (basic implementation)."""
        # Basic markdown to HTML conversion
        html = markdown_content
        
        # Headers
        html = html.replace("# ", "<h1>").replace("\n", "</h1>\n", 1)
        html = html.replace("## ", "<h2>").replace("\n", "</h2>\n", 1)
        html = html.replace("### ", "<h3>").replace("\n", "</h3>\n", 1)
        
        # Bold text
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Code blocks
        html = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', html, flags=re.DOTALL)
        
        # Lists
        html = re.sub(r'^- (.*?)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        
        # Wrap in HTML structure
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Data Lineage Documentation</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        pre {{ background-color: #f4f4f4; padding: 10px; border-radius: 4px; }}
    </style>
</head>
<body>
{html}
</body>
</html>"""
        
        return html


def create_doc_generator(config: Optional[Dict[str, Any]] = None) -> DocumentationGenerator:
    """Factory function to create a documentation generator."""
    return DocumentationGenerator(config)
