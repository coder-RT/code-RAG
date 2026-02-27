"""
Async indexing tasks using Celery
"""

import time
from typing import List, Optional, Dict, Any
from celery import current_task

from app.core.celery_app import celery_app
from app.services.rag_engine import RAGEngine


@celery_app.task(bind=True, name="index_codebase_async")
def index_codebase_task(
    self,
    path: str,
    project_name: str,
    include_patterns: Optional[List[str]] = None,
    exclude_patterns: Optional[List[str]] = None,
    embedding_provider: Optional[str] = None
) -> Dict[str, Any]:
    """
    Async task to index a codebase.
    Updates task state with progress information.
    
    Args:
        path: Path to the codebase
        project_name: Name for the project (used as ChromaDB collection name)
        include_patterns: File patterns to include
        exclude_patterns: File patterns to exclude
        embedding_provider: "openai" or "huggingface"
    """
    start_time = time.time()
    
    try:
        provider_name = "OpenAI" if embedding_provider == "openai" else "HuggingFace"
        self.update_state(
            state="PROGRESS",
            meta={
                "stage": "initializing",
                "message": f"Initializing RAG engine for project '{project_name}' with {provider_name} embeddings...",
                "progress": 5
            }
        )
        
        rag_engine = RAGEngine(embedding_provider=embedding_provider, project_name=project_name)
        
        # Debug: print exclusion patterns
        print(f"🔍 Exclude patterns: {rag_engine.loader.exclude_patterns[:10]}... (showing first 10)")
        print(f"🔍 'i18n' in patterns: {'i18n' in rag_engine.loader.exclude_patterns}")
        
        self.update_state(
            state="PROGRESS",
            meta={
                "stage": "loading",
                "message": f"Loading files from {path}...",
                "progress": 10
            }
        )
        
        if exclude_patterns:
            # Extend default patterns instead of replacing
            rag_engine.loader.exclude_patterns = list(set(rag_engine.loader.exclude_patterns + exclude_patterns))
        
        loaded_files = rag_engine.loader.load_directory(path)
        
        if not loaded_files:
            return {
                "success": False,
                "files_indexed": 0,
                "chunks_created": 0,
                "path": path,
                "error": "No supported files found",
                "elapsed_seconds": time.time() - start_time
            }
        
        load_stats = rag_engine.loader.get_stats(loaded_files)
        
        self.update_state(
            state="PROGRESS",
            meta={
                "stage": "chunking",
                "message": f"Chunking {load_stats['total_files']} files...",
                "progress": 30,
                "files_loaded": load_stats['total_files']
            }
        )
        
        chunks = rag_engine.chunker.chunk_files(loaded_files)
        chunk_stats = rag_engine.chunker.get_stats(chunks)
        
        self.update_state(
            state="PROGRESS",
            meta={
                "stage": "embedding",
                "message": f"Generating embeddings for {chunk_stats['total_chunks']} chunks...",
                "progress": 50,
                "files_loaded": load_stats['total_files'],
                "chunks_created": chunk_stats['total_chunks']
            }
        )
        
        from langchain.schema import Document
        from langchain_community.vectorstores import Chroma
        from app.core.config import settings
        
        documents = []
        for chunk in chunks:
            metadata = {
                "source": chunk.source_file,
                "file_type": chunk.file_type.value,
                "chunk_type": chunk.chunk_type,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_id": chunk.id,
            }
            for key, value in chunk.metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value
                elif isinstance(value, list) and value and isinstance(value[0], str):
                    metadata[key] = ", ".join(value[:5])
            
            documents.append(Document(
                page_content=chunk.content,
                metadata=metadata
            ))
        
        self.update_state(
            state="PROGRESS",
            meta={
                "stage": "storing",
                "message": "Storing embeddings in ChromaDB...",
                "progress": 80,
                "files_loaded": load_stats['total_files'],
                "chunks_created": chunk_stats['total_chunks']
            }
        )
        
        # Add documents in batches to avoid OpenAI token limits (max 300k tokens per request)
        BATCH_SIZE = 500  # ~500 chunks * ~500 tokens = ~250k tokens per batch
        
        # Create or get existing collection (use rag_engine.collection_name for project-specific storage)
        rag_engine.vectorstore = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            collection_name=rag_engine.collection_name,
            embedding_function=rag_engine.embeddings
        )
        
        total_docs = len(documents)
        for i in range(0, total_docs, BATCH_SIZE):
            batch = documents[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            total_batches = (total_docs + BATCH_SIZE - 1) // BATCH_SIZE
            
            self.update_state(
                state="PROGRESS",
                meta={
                    "stage": "embedding",
                    "message": f"Embedding batch {batch_num}/{total_batches}...",
                    "progress": 80 + int(15 * i / total_docs),
                    "files_loaded": load_stats['total_files'],
                    "chunks_created": chunk_stats['total_chunks']
                }
            )
            
            rag_engine.vectorstore.add_documents(batch)
        
        elapsed = time.time() - start_time
        
        return {
            "success": True,
            "files_indexed": load_stats['total_files'],
            "chunks_created": chunk_stats['total_chunks'],
            "path": path,
            "project_name": project_name,
            "elapsed_seconds": round(elapsed, 2),
            "stats": {
                "files_by_type": load_stats['by_type'],
                "chunks_by_type": chunk_stats['by_type'],
                "avg_chunk_size": chunk_stats['avg_chunk_size'],
            }
        }
        
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta={
                "stage": "error",
                "message": str(e),
                "progress": 0
            }
        )
        raise
