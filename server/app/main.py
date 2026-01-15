"""
Code-RAG Server - Main FastAPI Application
A coding agent powered by RAG for codebase understanding
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import codebase, architecture, terraform, graph, agent
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    print("🚀 Code-RAG Server starting...")
    yield
    # Shutdown
    print("👋 Code-RAG Server shutting down...")


app = FastAPI(
    title="Code-RAG API",
    description="A coding agent powered by Code-RAG for codebase understanding, architecture analysis, and dependency graphing",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(codebase.router, prefix="/api/codebase", tags=["Codebase"])
app.include_router(architecture.router, prefix="/api/architecture", tags=["Architecture"])
app.include_router(terraform.router, prefix="/api/terraform", tags=["Terraform"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Code-RAG API",
        "version": "1.0.0",
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "components": {
            "api": "up",
            "rag_engine": "up",
        }
    }

