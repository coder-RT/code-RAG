"""
Terraform API - Endpoints for infrastructure analysis
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict

from app.services.terraform_analyzer import TerraformAnalyzer

router = APIRouter()


class TerraformRequest(BaseModel):
    """Request for Terraform analysis"""
    path: str
    include_modules: bool = True


class ResourceLink(BaseModel):
    """Link between infrastructure and application"""
    resource_type: str
    resource_name: str
    connected_to: List[str]
    connection_type: str


class TerraformResponse(BaseModel):
    """Response for Terraform operations"""
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/analyze", response_model=TerraformResponse)
async def analyze_terraform(request: TerraformRequest):
    """
    Analyze Terraform/infrastructure configuration.
    Parses .tf files and identifies resources, modules, and connections.
    """
    try:
        analyzer = TerraformAnalyzer()
        result = await analyzer.analyze(
            path=request.path,
            include_modules=request.include_modules
        )
        
        return TerraformResponse(
            success=True,
            message="Terraform analysis complete",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resources/{path:path}", response_model=TerraformResponse)
async def get_resources(path: str):
    """
    List all Terraform resources in the configuration.
    """
    try:
        full_path = f"/{path}" if not path.startswith("/") else path
        
        analyzer = TerraformAnalyzer()
        resources = await analyzer.list_resources(full_path)
        
        return TerraformResponse(
            success=True,
            message="Resources listed successfully",
            data={"resources": resources}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/modules/{path:path}", response_model=TerraformResponse)
async def get_terraform_modules(path: str):
    """
    List all Terraform modules and their relationships.
    """
    try:
        full_path = f"/{path}" if not path.startswith("/") else path
        
        analyzer = TerraformAnalyzer()
        modules = await analyzer.list_modules(full_path)
        
        return TerraformResponse(
            success=True,
            message="Modules listed successfully",
            data={"modules": modules}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/app-links", response_model=TerraformResponse)
async def get_application_links(request: TerraformRequest):
    """
    Show how Terraform resources connect to the application.
    Maps infrastructure → cloud resources → services → APIs → frontend
    """
    try:
        analyzer = TerraformAnalyzer()
        links = await analyzer.map_application_links(request.path)
        
        return TerraformResponse(
            success=True,
            message="Application links mapped successfully",
            data={"links": links}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain", response_model=TerraformResponse)
async def explain_infrastructure(request: TerraformRequest):
    """
    Generate a human-readable summary of the infrastructure.
    """
    try:
        analyzer = TerraformAnalyzer()
        explanation = await analyzer.explain(request.path)
        
        return TerraformResponse(
            success=True,
            message="Infrastructure explanation generated",
            data={"explanation": explanation}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/variables/{path:path}", response_model=TerraformResponse)
async def get_variables(path: str):
    """
    List all Terraform variables and their usage.
    """
    try:
        full_path = f"/{path}" if not path.startswith("/") else path
        
        analyzer = TerraformAnalyzer()
        variables = await analyzer.list_variables(full_path)
        
        return TerraformResponse(
            success=True,
            message="Variables listed successfully",
            data={"variables": variables}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

