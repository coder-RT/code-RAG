"""
Graph Generator - Generate dependency and integration graphs
"""

import os
import re
from typing import Dict, List, Optional
from pathlib import Path
import json

import networkx as nx
from langchain_openai import ChatOpenAI
from app.core.config import settings


class GraphGenerator:
    """
    Generates dependency and integration graphs for codebases.
    Supports multiple output formats: JSON, SVG, Mermaid.
    """
    
    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
    
    async def generate(
        self,
        path: str,
        graph_type: str = "full",
        output_format: str = "json"
    ) -> Dict:
        """
        Generate a graph based on the specified type.
        """
        if graph_type == "dependencies":
            graph_data = await self.generate_dependency_graph(path)
        elif graph_type == "integration":
            graph_data = await self.generate_integration_graph(path)
        elif graph_type == "terraform":
            graph_data = await self._generate_terraform_graph(path)
        else:
            # Full graph combines all types
            deps = await self.generate_dependency_graph(path)
            integration = await self.generate_integration_graph(path)
            graph_data = self._merge_graphs(deps, integration)
        
        if output_format == "mermaid":
            graph_data["mermaid"] = self._to_mermaid(graph_data)
        
        return graph_data
    
    async def generate_dependency_graph(self, path: str) -> Dict:
        """
        Generate a dependency graph showing module/package dependencies.
        """
        nodes = []
        edges = []
        
        # Track files and their imports
        file_imports = {}
        
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d not in [
                'node_modules', '__pycache__', 'venv', '.git', 'dist', 'build'
            ]]
            
            for f in files:
                file_path = os.path.join(root, f)
                ext = os.path.splitext(f)[1]
                
                if ext not in settings.SUPPORTED_EXTENSIONS:
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as fp:
                        content = fp.read()
                    
                    relative_path = os.path.relpath(file_path, path)
                    imports = self._extract_imports(content, ext)
                    
                    file_imports[relative_path] = imports
                    
                    # Add node for this file
                    nodes.append({
                        "id": relative_path,
                        "label": f,
                        "type": self._get_node_type(ext),
                        "metadata": {"extension": ext}
                    })
                    
                except Exception:
                    continue
        
        # Create edges based on imports
        for file_path, imports in file_imports.items():
            for imp in imports:
                # Try to resolve import to a file
                resolved = self._resolve_import(imp, file_path, list(file_imports.keys()))
                
                if resolved:
                    edges.append({
                        "source": file_path,
                        "target": resolved,
                        "relationship": "imports",
                        "metadata": {"import_name": imp}
                    })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "graph_type": "dependency",
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }
    
    async def generate_integration_graph(self, path: str) -> Dict:
        """
        Generate an integration graph showing:
        Terraform → Cloud Resources → Services → APIs → Frontend
        """
        nodes = []
        edges = []
        
        # Analyze directory structure to identify components
        components = self._identify_components(path)
        
        for comp in components:
            nodes.append({
                "id": comp["id"],
                "label": comp["name"],
                "type": comp["type"],
                "metadata": {"path": comp.get("path", "")}
            })
        
        # Infer connections based on common patterns
        edges = self._infer_integration_edges(components)
        
        # Add layer information
        layers = {
            "infrastructure": [],
            "backend": [],
            "api": [],
            "frontend": []
        }
        
        for node in nodes:
            if node["type"] in ["terraform", "infrastructure"]:
                layers["infrastructure"].append(node["id"])
            elif node["type"] in ["service", "server", "backend"]:
                layers["backend"].append(node["id"])
            elif node["type"] in ["api", "route", "controller"]:
                layers["api"].append(node["id"])
            elif node["type"] in ["frontend", "client", "ui"]:
                layers["frontend"].append(node["id"])
        
        return {
            "nodes": nodes,
            "edges": edges,
            "layers": layers,
            "graph_type": "integration",
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }
    
    async def _generate_terraform_graph(self, path: str) -> Dict:
        """Generate a graph specifically for Terraform resources."""
        nodes = []
        edges = []
        
        # Find all .tf files
        for root, dirs, files in os.walk(path):
            dirs[:] = [d for d in dirs if d != '.terraform']
            
            for f in files:
                if not f.endswith('.tf'):
                    continue
                
                file_path = os.path.join(root, f)
                
                try:
                    with open(file_path, 'r') as fp:
                        content = fp.read()
                    
                    # Extract resources
                    resources = re.findall(
                        r'resource\s+"([^"]+)"\s+"([^"]+)"',
                        content
                    )
                    
                    for res_type, res_name in resources:
                        node_id = f"{res_type}.{res_name}"
                        nodes.append({
                            "id": node_id,
                            "label": res_name,
                            "type": res_type,
                            "metadata": {"file": os.path.relpath(file_path, path)}
                        })
                        
                        # Find references to other resources
                        refs = re.findall(
                            r'(\w+\.\w+)\.(\w+)',
                            content
                        )
                        
                        for ref_type_name, ref_attr in refs:
                            if ref_type_name != node_id:
                                edges.append({
                                    "source": node_id,
                                    "target": ref_type_name,
                                    "relationship": "references",
                                    "metadata": {"attribute": ref_attr}
                                })
                                
                except Exception:
                    continue
        
        # Deduplicate edges
        seen_edges = set()
        unique_edges = []
        for edge in edges:
            key = (edge["source"], edge["target"])
            if key not in seen_edges:
                seen_edges.add(key)
                unique_edges.append(edge)
        
        return {
            "nodes": nodes,
            "edges": unique_edges,
            "graph_type": "terraform",
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(unique_edges)
            }
        }
    
    async def summarize(self, path: str, graph_type: str = "full") -> str:
        """
        Get a readable summary of the graph relationships.
        """
        graph_data = await self.generate(path, graph_type, "json")
        
        prompt = f"""Analyze this dependency/integration graph and provide a human-readable summary.

Graph Statistics:
- Nodes: {graph_data['stats']['total_nodes']}
- Edges: {graph_data['stats']['total_edges']}
- Type: {graph_data['graph_type']}

Sample Nodes (first 20):
{json.dumps(graph_data['nodes'][:20], indent=2)}

Sample Edges (first 30):
{json.dumps(graph_data['edges'][:30], indent=2)}

Provide:
1. **Overview**: What does this graph represent?
2. **Key Components**: What are the main nodes/modules?
3. **Relationships**: How do components depend on each other?
4. **Architecture Flow**: Describe the data/control flow
5. **Notable Patterns**: Any circular dependencies, isolated components, or central hubs?

Write a clear, concise summary suitable for developers."""

        response = await self.llm.ainvoke(prompt)
        return response.content
    
    async def export_svg(self, path: str, graph_type: str = "full") -> str:
        """
        Export the graph as an SVG image.
        Uses matplotlib and networkx for rendering.
        """
        import matplotlib
        matplotlib.use('Agg')  # Non-interactive backend
        import matplotlib.pyplot as plt
        import io
        
        graph_data = await self.generate(path, graph_type, "json")
        
        # Create NetworkX graph
        G = nx.DiGraph()
        
        for node in graph_data["nodes"]:
            G.add_node(node["id"], label=node["label"], type=node["type"])
        
        for edge in graph_data["edges"]:
            if edge["source"] in G.nodes and edge["target"] in G.nodes:
                G.add_edge(edge["source"], edge["target"])
        
        # Create figure
        fig, ax = plt.subplots(1, 1, figsize=(16, 12))
        
        # Layout
        try:
            pos = nx.spring_layout(G, k=2, iterations=50)
        except:
            pos = nx.circular_layout(G)
        
        # Draw
        nx.draw(
            G, pos, ax=ax,
            with_labels=True,
            node_color='lightblue',
            node_size=1500,
            font_size=8,
            font_weight='bold',
            arrows=True,
            edge_color='gray',
            alpha=0.8
        )
        
        plt.title(f"{graph_type.title()} Dependency Graph")
        
        # Save to SVG
        svg_buffer = io.BytesIO()
        plt.savefig(svg_buffer, format='svg', bbox_inches='tight')
        plt.close()
        
        svg_buffer.seek(0)
        return svg_buffer.read().decode('utf-8')
    
    async def export_mermaid(self, path: str, graph_type: str = "full") -> str:
        """
        Export the graph as Mermaid diagram syntax.
        """
        graph_data = await self.generate(path, graph_type, "json")
        return self._to_mermaid(graph_data)
    
    def _to_mermaid(self, graph_data: Dict) -> str:
        """Convert graph data to Mermaid syntax."""
        lines = ["graph LR"]
        
        # Add nodes with styling
        node_ids = {}
        for i, node in enumerate(graph_data["nodes"][:50]):  # Limit nodes
            safe_id = f"N{i}"
            node_ids[node["id"]] = safe_id
            label = node["label"].replace('"', "'")
            lines.append(f'    {safe_id}["{label}"]')
        
        # Add edges
        for edge in graph_data["edges"][:100]:  # Limit edges
            if edge["source"] in node_ids and edge["target"] in node_ids:
                src = node_ids[edge["source"]]
                tgt = node_ids[edge["target"]]
                rel = edge.get("relationship", "")[:10]
                lines.append(f'    {src} -->|{rel}| {tgt}')
        
        return "\n".join(lines)
    
    def _extract_imports(self, content: str, ext: str) -> List[str]:
        """Extract import statements from code."""
        imports = []
        
        if ext == '.py':
            # Python imports
            imports.extend(re.findall(r'^import\s+([\w\.]+)', content, re.MULTILINE))
            imports.extend(re.findall(r'^from\s+([\w\.]+)\s+import', content, re.MULTILINE))
        
        elif ext in ['.js', '.jsx', '.ts', '.tsx']:
            # JavaScript/TypeScript imports
            imports.extend(re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", content))
            imports.extend(re.findall(r"require\s*\(\s*['\"]([^'\"]+)['\"]", content))
        
        elif ext == '.go':
            # Go imports
            imports.extend(re.findall(r'"([^"]+)"', content))
        
        elif ext == '.rs':
            # Rust imports
            imports.extend(re.findall(r'use\s+([\w:]+)', content))
        
        return imports
    
    def _resolve_import(
        self,
        import_name: str,
        from_file: str,
        all_files: List[str]
    ) -> Optional[str]:
        """Try to resolve an import to a file in the codebase."""
        # Handle relative imports
        if import_name.startswith('.'):
            base_dir = os.path.dirname(from_file)
            relative_parts = import_name.split('/')
            
            for f in all_files:
                if f.startswith(base_dir) and any(
                    part in f for part in relative_parts if part != '.'
                ):
                    return f
        
        # Handle absolute imports
        import_parts = import_name.replace('.', '/').split('/')
        
        for f in all_files:
            if any(part in f for part in import_parts):
                return f
        
        return None
    
    def _get_node_type(self, ext: str) -> str:
        """Get node type based on file extension."""
        type_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'react',
            '.jsx': 'react',
            '.go': 'golang',
            '.rs': 'rust',
            '.tf': 'terraform',
            '.yaml': 'config',
            '.yml': 'config',
            '.json': 'config',
        }
        return type_map.get(ext, 'file')
    
    def _identify_components(self, path: str) -> List[Dict]:
        """Identify high-level components in the codebase."""
        components = []
        
        # Look for common component directories
        component_patterns = {
            'frontend': ['client', 'frontend', 'web', 'ui', 'app'],
            'backend': ['server', 'backend', 'api', 'service'],
            'infrastructure': ['terraform', 'infra', 'infrastructure', 'deploy'],
            'shared': ['shared', 'common', 'lib', 'packages'],
            'database': ['db', 'database', 'models', 'migrations']
        }
        
        for root, dirs, files in os.walk(path):
            if root == path:
                for d in dirs:
                    if d.startswith('.') or d in ['node_modules', '__pycache__', 'venv']:
                        continue
                    
                    comp_type = 'module'
                    for type_name, patterns in component_patterns.items():
                        if d.lower() in patterns:
                            comp_type = type_name
                            break
                    
                    components.append({
                        "id": d,
                        "name": d,
                        "type": comp_type,
                        "path": os.path.join(path, d)
                    })
                break
        
        return components
    
    def _infer_integration_edges(self, components: List[Dict]) -> List[Dict]:
        """Infer integration edges between components."""
        edges = []
        
        # Common integration patterns
        patterns = [
            ("infrastructure", "backend"),
            ("backend", "database"),
            ("backend", "api"),
            ("api", "frontend"),
            ("shared", "backend"),
            ("shared", "frontend"),
        ]
        
        comp_by_type = {}
        for comp in components:
            comp_type = comp["type"]
            if comp_type not in comp_by_type:
                comp_by_type[comp_type] = []
            comp_by_type[comp_type].append(comp)
        
        for source_type, target_type in patterns:
            sources = comp_by_type.get(source_type, [])
            targets = comp_by_type.get(target_type, [])
            
            for src in sources:
                for tgt in targets:
                    edges.append({
                        "source": src["id"],
                        "target": tgt["id"],
                        "relationship": f"{source_type}_to_{target_type}",
                        "metadata": {}
                    })
        
        return edges
    
    def _merge_graphs(self, graph1: Dict, graph2: Dict) -> Dict:
        """Merge two graphs into one."""
        # Combine nodes (deduplicated)
        node_ids = set()
        nodes = []
        
        for node in graph1.get("nodes", []) + graph2.get("nodes", []):
            if node["id"] not in node_ids:
                nodes.append(node)
                node_ids.add(node["id"])
        
        # Combine edges (deduplicated)
        edge_keys = set()
        edges = []
        
        for edge in graph1.get("edges", []) + graph2.get("edges", []):
            key = (edge["source"], edge["target"], edge.get("relationship", ""))
            if key not in edge_keys:
                edges.append(edge)
                edge_keys.add(key)
        
        return {
            "nodes": nodes,
            "edges": edges,
            "graph_type": "full",
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges)
            }
        }

