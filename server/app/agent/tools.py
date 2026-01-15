"""
Agent Tools - Tool definitions and executors for the Code-RAG agent
"""

from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass
from enum import Enum

from app.services.rag_engine import RAGEngine
from app.services.code_analyzer import CodeAnalyzer
from app.services.architecture_analyzer import ArchitectureAnalyzer
from app.services.terraform_analyzer import TerraformAnalyzer
from app.services.graph_generator import GraphGenerator


class ToolName(str, Enum):
    """Available tool names"""
    QUERY_CODEBASE = "query_codebase"
    EXPLAIN_CODE = "explain_code"
    ANALYZE_ARCHITECTURE = "analyze_architecture"
    ANALYZE_TERRAFORM = "analyze_terraform"
    GENERATE_GRAPH = "generate_graph"
    GET_STRUCTURE = "get_structure"


@dataclass
class ToolResult:
    """Result from a tool execution"""
    tool_name: str
    success: bool
    data: Any
    error: Optional[str] = None


@dataclass
class Tool:
    """Tool definition"""
    name: ToolName
    description: str
    parameters: Dict[str, Dict[str, str]]
    executor: Callable


class ToolRegistry:
    """
    Registry of available tools for the agent.
    Handles tool definitions and execution.
    """
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
        self._rag_engine = RAGEngine()
        self._code_analyzer = CodeAnalyzer()
        self._arch_analyzer = ArchitectureAnalyzer()
        self._tf_analyzer = TerraformAnalyzer()
        self._graph_generator = GraphGenerator()
        
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        
        # Query Codebase
        self.register(Tool(
            name=ToolName.QUERY_CODEBASE,
            description="Search the indexed codebase using RAG and get AI-generated answers",
            parameters={
                "question": {"type": "string", "description": "The question to ask", "required": "true"},
                "context_limit": {"type": "integer", "description": "Number of chunks to retrieve", "required": "false"}
            },
            executor=self._query_codebase
        ))
        
        # Explain Code
        self.register(Tool(
            name=ToolName.EXPLAIN_CODE,
            description="Get a detailed explanation of a file or directory",
            parameters={
                "path": {"type": "string", "description": "Path to explain", "required": "true"},
                "detail_level": {"type": "string", "description": "summary|detailed|verbose", "required": "false"}
            },
            executor=self._explain_code
        ))
        
        # Analyze Architecture
        self.register(Tool(
            name=ToolName.ANALYZE_ARCHITECTURE,
            description="Analyze system architecture for modules, layers, and patterns",
            parameters={
                "path": {"type": "string", "description": "Path to codebase", "required": "true"},
                "analysis_type": {"type": "string", "description": "full|modules|layers|dependencies", "required": "false"}
            },
            executor=self._analyze_architecture
        ))
        
        # Analyze Terraform
        self.register(Tool(
            name=ToolName.ANALYZE_TERRAFORM,
            description="Parse and analyze Terraform configuration",
            parameters={
                "path": {"type": "string", "description": "Path to Terraform files", "required": "true"},
                "include_modules": {"type": "boolean", "description": "Include module analysis", "required": "false"}
            },
            executor=self._analyze_terraform
        ))
        
        # Generate Graph
        self.register(Tool(
            name=ToolName.GENERATE_GRAPH,
            description="Generate dependency or integration graph",
            parameters={
                "path": {"type": "string", "description": "Path to codebase", "required": "true"},
                "graph_type": {"type": "string", "description": "full|dependencies|integration|terraform", "required": "false"}
            },
            executor=self._generate_graph
        ))
        
        # Get Structure
        self.register(Tool(
            name=ToolName.GET_STRUCTURE,
            description="Get directory structure of a codebase",
            parameters={
                "path": {"type": "string", "description": "Path to directory", "required": "true"}
            },
            executor=self._get_structure
        ))
    
    def register(self, tool: Tool):
        """Register a tool"""
        self._tools[tool.name.value] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[Dict]:
        """List all available tools with their schemas"""
        return [
            {
                "name": tool.name.value,
                "description": tool.description,
                "parameters": tool.parameters
            }
            for tool in self._tools.values()
        ]
    
    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name"""
        tool = self.get_tool(tool_name)
        
        if not tool:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=f"Unknown tool: {tool_name}"
            )
        
        try:
            result = await tool.executor(**kwargs)
            return ToolResult(
                tool_name=tool_name,
                success=True,
                data=result
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                data=None,
                error=str(e)
            )
    
    # Tool executors
    async def _query_codebase(self, question: str, context_limit: int = 5) -> Dict:
        """Execute query_codebase tool"""
        return await self._rag_engine.query(question, context_limit)
    
    async def _explain_code(self, path: str, detail_level: str = "summary") -> str:
        """Execute explain_code tool"""
        return await self._code_analyzer.explain(path, detail_level)
    
    async def _analyze_architecture(self, path: str, analysis_type: str = "full") -> Dict:
        """Execute analyze_architecture tool"""
        return await self._arch_analyzer.analyze(path, analysis_type)
    
    async def _analyze_terraform(self, path: str, include_modules: bool = True) -> Dict:
        """Execute analyze_terraform tool"""
        return await self._tf_analyzer.analyze(path, include_modules)
    
    async def _generate_graph(self, path: str, graph_type: str = "full") -> Dict:
        """Execute generate_graph tool"""
        return await self._graph_generator.generate(path, graph_type)
    
    async def _get_structure(self, path: str) -> Dict:
        """Execute get_structure tool"""
        return self._code_analyzer.get_structure(path)


def get_tools_for_openai() -> List[Dict]:
    """
    Get tool definitions in OpenAI function calling format.
    """
    registry = ToolRegistry()
    tools = []
    
    for tool in registry._tools.values():
        properties = {}
        required = []
        
        for param_name, param_info in tool.parameters.items():
            properties[param_name] = {
                "type": param_info.get("type", "string"),
                "description": param_info.get("description", "")
            }
            if param_info.get("required") == "true":
                required.append(param_name)
        
        tools.append({
            "type": "function",
            "function": {
                "name": tool.name.value,
                "description": tool.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            }
        })
    
    return tools

