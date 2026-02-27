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
    project_name: Optional[str] = None  # If not provided, derives from path
    include_patterns: Optional[List[str]] = None
    exclude_patterns: Optional[List[str]] = ["node_modules", ".git", "__pycache__", "venv"]
    async_mode: bool = False
    embedding_provider: Optional[str] = "openai"  # "openai" or "huggingface"


class QueryRequest(BaseModel):
    """Request to query the codebase"""
    question: str
    project_name: str  # Which project to query
    context_limit: int = 5
    embedding_provider: Optional[str] = "openai"  # Must match what was used during indexing


class ExplainRequest(BaseModel):
    """Request to explain a specific file or directory"""
    path: str
    detail_level: str = "summary"  # summary, detailed, verbose


class CodebaseResponse(BaseModel):
    """Response for codebase operations"""
    success: bool
    message: str
    data: Optional[dict] = None


class TaskStatusResponse(BaseModel):
    """Response for async task status"""
    task_id: str
    status: str
    progress: Optional[int] = None
    stage: Optional[str] = None
    message: Optional[str] = None
    result: Optional[dict] = None


@router.post("/index", response_model=CodebaseResponse)
async def index_codebase(request: IndexRequest):
    """
    Index a codebase for RAG queries.
    Parses files, generates embeddings, and stores in vector DB.
    
    Set async_mode=True for background processing with Celery (requires Redis).
    """
    try:
        if not os.path.exists(request.path):
            raise HTTPException(status_code=404, detail=f"Path not found: {request.path}")
        
        # Derive project name from path if not provided
        project_name = request.project_name or os.path.basename(request.path.rstrip('/'))
        # Sanitize project name for use as collection name
        project_name = project_name.replace(' ', '_').replace('-', '_').lower()
        
        if request.async_mode:
            try:
                from app.tasks.indexing import index_codebase_task
                task = index_codebase_task.delay(
                    path=request.path,
                    project_name=project_name,
                    include_patterns=request.include_patterns,
                    exclude_patterns=request.exclude_patterns,
                    embedding_provider=request.embedding_provider
                )
                return CodebaseResponse(
                    success=True,
                    message="Indexing task started in background",
                    data={
                        "task_id": task.id,
                        "project_name": project_name,
                        "status_url": f"/api/codebase/task/{task.id}"
                    }
                )
            except Exception as e:
                if "redis" in str(e).lower() or "connection" in str(e).lower():
                    raise HTTPException(
                        status_code=503,
                        detail="Celery/Redis not available. Start Redis and Celery worker, or use async_mode=False"
                    )
                raise
        
        rag_engine = RAGEngine(embedding_provider=request.embedding_provider)
        result = await rag_engine.index_codebase(
            path=request.path,
            project_name=project_name,
            include_patterns=request.include_patterns,
            exclude_patterns=request.exclude_patterns
        )
        
        return CodebaseResponse(
            success=True,
            message="Codebase indexed successfully",
            data={**result, "project_name": project_name}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """
    Get the status of an async indexing task.
    """
    try:
        from app.core.celery_app import celery_app
        task = celery_app.AsyncResult(task_id)
        
        response = TaskStatusResponse(
            task_id=task_id,
            status=task.status
        )
        
        if task.status == "PROGRESS":
            meta = task.info or {}
            response.progress = meta.get("progress", 0)
            response.stage = meta.get("stage", "unknown")
            response.message = meta.get("message", "")
        elif task.status == "SUCCESS":
            response.progress = 100
            response.stage = "complete"
            response.message = "Indexing completed successfully"
            response.result = task.result
        elif task.status == "FAILURE":
            response.progress = 0
            response.stage = "error"
            response.message = str(task.result) if task.result else "Task failed"
        elif task.status == "PENDING":
            response.progress = 0
            response.stage = "pending"
            response.message = "Task is waiting to be processed"
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query", response_model=CodebaseResponse)
async def query_codebase(request: QueryRequest):
    """
    Ask questions about the indexed codebase.
    Uses RAG to find relevant code and generate answers.
    """
    try:
        rag_engine = RAGEngine(
            embedding_provider=request.embedding_provider,
            project_name=request.project_name
        )
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


@router.get("/projects", response_model=CodebaseResponse)
async def list_projects():
    """
    List all indexed projects (ChromaDB collections).
    """
    try:
        import chromadb
        from app.core.config import settings
        
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        collections = client.list_collections()
        
        projects = []
        for collection in collections:
            projects.append({
                "name": collection.name,
                "count": collection.count()
            })
        
        return CodebaseResponse(
            success=True,
            message=f"Found {len(projects)} indexed projects",
            data={"projects": projects}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/projects/{project_name}", response_model=CodebaseResponse)
async def delete_project(project_name: str):
    """
    Delete an indexed project (ChromaDB collection).
    """
    try:
        import chromadb
        from app.core.config import settings
        
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        client.delete_collection(name=project_name)
        
        return CodebaseResponse(
            success=True,
            message=f"Project '{project_name}' deleted successfully",
            data={"deleted": project_name}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

