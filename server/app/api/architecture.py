"""
Architecture API - Endpoints for system architecture analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.services.architecture_analyzer import ArchitectureAnalyzer

router = APIRouter()


class AnalyzeRequest(BaseModel):
    """Request to analyze architecture"""
    path: str
    analysis_type: str = "full"  # full, modules, dependencies, layers


class ModuleInfo(BaseModel):
    """Information about a module"""
    name: str
    path: str
    type: str
    description: str
    dependencies: List[str]
    exports: List[str]


class ArchitectureResponse(BaseModel):
    """Response for architecture operations"""
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/analyze", response_model=ArchitectureResponse)
async def analyze_architecture(request: AnalyzeRequest):
    """
    Analyze the architecture of a codebase.
    Identifies modules, layers, and their responsibilities.
    """
    try:
        analyzer = ArchitectureAnalyzer()
        result = await analyzer.analyze(
            path=request.path,
            analysis_type=request.analysis_type
        )
        
        return ArchitectureResponse(
            success=True,
            message="Architecture analyzed successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules/{path:path}", response_model=ArchitectureResponse)
async def get_modules(path: str):
    """
    Get a list of all modules in the codebase with their responsibilities.
    """
    try:
        full_path = f"/{path}" if not path.startswith("/") else path
        
        analyzer = ArchitectureAnalyzer()
        modules = await analyzer.identify_modules(full_path)
        
        return ArchitectureResponse(
            success=True,
            message="Modules identified successfully",
            data={"modules": modules}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/layers/{path:path}", response_model=ArchitectureResponse)
async def get_layers(path: str):
    """
    Identify architectural layers (e.g., presentation, business, data).
    """
    try:
        full_path = f"/{path}" if not path.startswith("/") else path
        
        analyzer = ArchitectureAnalyzer()
        layers = await analyzer.identify_layers(full_path)
        
        return ArchitectureResponse(
            success=True,
            message="Layers identified successfully",
            data={"layers": layers}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain-module", response_model=ArchitectureResponse)
async def explain_module(request: AnalyzeRequest):
    """
    Get a detailed explanation of what a specific module does.
    """
    try:
        analyzer = ArchitectureAnalyzer()
        explanation = await analyzer.explain_module(request.path)
        
        return ArchitectureResponse(
            success=True,
            message="Module explanation generated",
            data={"explanation": explanation}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{path:path}", response_model=ArchitectureResponse)
async def detect_patterns(path: str):
    """
    Detect architectural and design patterns in the codebase.
    """
    try:
        full_path = f"/{path}" if not path.startswith("/") else path
        
        analyzer = ArchitectureAnalyzer()
        patterns = await analyzer.detect_patterns(full_path)
        
        return ArchitectureResponse(
            success=True,
            message="Patterns detected successfully",
            data={"patterns": patterns}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

