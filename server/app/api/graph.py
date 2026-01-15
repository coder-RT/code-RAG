"""
Graph API - Endpoints for dependency and integration graph generation
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import io

from app.services.graph_generator import GraphGenerator

router = APIRouter()


class GraphRequest(BaseModel):
    """Request for graph generation"""
    path: str
    graph_type: str = "full"  # full, dependencies, integration, terraform
    output_format: str = "json"  # json, svg, png, mermaid


class GraphNode(BaseModel):
    """A node in the graph"""
    id: str
    label: str
    type: str
    metadata: Optional[Dict] = None


class GraphEdge(BaseModel):
    """An edge in the graph"""
    source: str
    target: str
    relationship: str
    metadata: Optional[Dict] = None


class GraphData(BaseModel):
    """Graph data structure"""
    nodes: List[GraphNode]
    edges: List[GraphEdge]


class GraphResponse(BaseModel):
    """Response for graph operations"""
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/generate", response_model=GraphResponse)
async def generate_graph(request: GraphRequest):
    """
    Generate a dependency or integration graph.
    Supports multiple output formats.
    """
    try:
        generator = GraphGenerator()
        result = await generator.generate(
            path=request.path,
            graph_type=request.graph_type,
            output_format=request.output_format
        )
        
        return GraphResponse(
            success=True,
            message="Graph generated successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dependencies", response_model=GraphResponse)
async def generate_dependency_graph(request: GraphRequest):
    """
    Generate a dependency graph showing module/package dependencies.
    """
    try:
        generator = GraphGenerator()
        result = await generator.generate_dependency_graph(request.path)
        
        return GraphResponse(
            success=True,
            message="Dependency graph generated",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/integration", response_model=GraphResponse)
async def generate_integration_graph(request: GraphRequest):
    """
    Generate an integration graph showing:
    Terraform → Cloud Resources → Services → APIs → Frontend
    """
    try:
        generator = GraphGenerator()
        result = await generator.generate_integration_graph(request.path)
        
        return GraphResponse(
            success=True,
            message="Integration graph generated",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summary", response_model=GraphResponse)
async def get_graph_summary(request: GraphRequest):
    """
    Get a readable summary of the graph relationships.
    """
    try:
        generator = GraphGenerator()
        summary = await generator.summarize(request.path, request.graph_type)
        
        return GraphResponse(
            success=True,
            message="Summary generated",
            data={"summary": summary}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/svg")
async def export_graph_svg(request: GraphRequest):
    """
    Export the graph as an SVG image.
    """
    try:
        generator = GraphGenerator()
        svg_data = await generator.export_svg(request.path, request.graph_type)
        
        return StreamingResponse(
            io.BytesIO(svg_data.encode()),
            media_type="image/svg+xml",
            headers={"Content-Disposition": "attachment; filename=graph.svg"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export/mermaid", response_model=GraphResponse)
async def export_graph_mermaid(request: GraphRequest):
    """
    Export the graph as Mermaid diagram syntax.
    """
    try:
        generator = GraphGenerator()
        mermaid_code = await generator.export_mermaid(request.path, request.graph_type)
        
        return GraphResponse(
            success=True,
            message="Mermaid diagram generated",
            data={"mermaid": mermaid_code}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

