"""
Codebase API - Endpoints for codebase analysis and explanation
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import os

from app.services.rag_engine import RAGEngine
from app.services.code_analyzer import CodeAnalyzer

router = APIRouter()


class IndexRequest(BaseModel):
    """Request to index a codebase"""
    path: str
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = ["node_modules", ".git", "__pycache__", "venv"]


class QueryRequest(BaseModel):
    """Request to query the codebase"""
    question: str
    context_limit: int = 5


class ExplainRequest(BaseModel):
    """Request to explain a specific file or directory"""
    path: str
    detail_level: str = "summary"  # summary, detailed, verbose


class CodebaseResponse(BaseModel):
    """Response for codebase operations"""
    success: bool
    message: str
    data: Optional[dict] = None


@router.post("/index", response_model=CodebaseResponse)
async def index_codebase(request: IndexRequest):
    """
    Index a codebase for RAG queries.
    Parses files, generates embeddings, and stores in vector DB.
    """
    try:
        if not os.path.exists(request.path):
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
        
        rag_engine = RAGEngine()
        result = await rag_engine.index_codebase(
            path=request.path,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns
        )
        
        return CodebaseResponse(
            success=True,
            message="Codebase indexed successfully",
            data=result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=CodebaseResponse)
async def query_codebase(request: QueryRequest):
    """
    Ask questions about the indexed codebase.
    Uses RAG to find relevant code and generate answers.
    """
    try:
        rag_engine = RAGEngine()
        result = await rag_engine.query(
            question=request.question,
            context_limit=request.context_limit
        )
        
        return CodebaseResponse(
            success=True,
            message="Query processed successfully",
            data={"answer": result["answer"], "sources": result["sources"]}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/explain", response_model=CodebaseResponse)
async def explain_code(request: ExplainRequest):
    """
    Get an explanation of what a specific file or directory does.
    """
    try:
        if not os.path.exists(request.path):
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
        
        analyzer = CodeAnalyzer()
        explanation = await analyzer.explain(
            path=request.path,
            detail_level=request.detail_level
        )
        
        return CodebaseResponse(
            success=True,
            message="Explanation generated successfully",
            data={"explanation": explanation}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/structure/{path:path}", response_model=CodebaseResponse)
async def get_structure(path: str):
    """
    Get the directory structure of a codebase path.
    """
    try:
        full_path = f"/{path}" if not path.startswith("/") else path
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail=f"Path not found: {full_path}")
        
        analyzer = CodeAnalyzer()
        structure = analyzer.get_structure(full_path)
        
        return CodebaseResponse(
            success=True,
            message="Structure retrieved successfully",
            data={"structure": structure}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

