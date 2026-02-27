"""
RAG Engine - Core RAG functionality for code understanding
"""

import asyncio
from typing import List, Dict, Optional

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document

from app.core.config import settings, EmbeddingProvider
from app.services.loader import FileLoader, LoadedFile
from app.services.chunker import Chunker, Chunk


def get_embeddings(provider: Optional[str] = None):
    """
    Get the embedding model.
    Supports OpenAI and HuggingFace (Jina) embeddings.
    
    Args:
        provider: "openai" or "huggingface". Defaults to settings.EMBEDDING_PROVIDER.
    """
    use_huggingface = (
        provider == "huggingface" or 
        (provider is None and settings.EMBEDDING_PROVIDER == EmbeddingProvider.HUGGINGFACE)
    )
    
    if use_huggingface:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        
        print(f"🔧 Using HuggingFace embeddings: {settings.HUGGINGFACE_EMBEDDING_MODEL}")
        print(f"   Device: {settings.EMBEDDING_DEVICE}")
        print("   (First load may take a few minutes to download the model...)")
        
        return HuggingFaceEmbeddings(
            model_name=settings.HUGGINGFACE_EMBEDDING_MODEL,
            model_kwargs={"device": settings.EMBEDDING_DEVICE, "trust_remote_code": True},
            encode_kwargs={"normalize_embeddings": True}
        )
    else:
        print(f"🔧 Using OpenAI embeddings: {settings.EMBEDDING_MODEL}")
        return OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            openai_api_base=settings.OPENAI_BASE_URL
        )


class RAGEngine:
    """
    RAG Engine for indexing and querying codebases.
    Uses FileLoader for loading, Chunker for smart chunking,
    ChromaDB for vector storage, and configurable embeddings.
    """
    
    def __init__(self, embedding_provider: Optional[str] = None, project_name: Optional[str] = None):
        """
        Initialize RAG Engine.
        
        Args:
            embedding_provider: "openai" or "huggingface". Defaults to config setting.
            project_name: Project name to use as ChromaDB collection name.
        """
        self.embedding_provider = embedding_provider
        self.embeddings = get_embeddings(provider=embedding_provider)
        self.llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            openai_api_key=settings.OPENAI_API_KEY,
            temperature=0.1
        )
        self.loader = FileLoader(max_file_size_kb=settings.MAX_FILE_SIZE_KB)
        self.chunker = Chunker()
        self.vectorstore = None
        # Use project_name as collection name, fallback to default
        self.collection_name = project_name or settings.CHROMA_COLLECTION_NAME
    
    async def index_codebase(
        self,
        path: str,
        project_name: Optional[str] = None,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None
    ) -> Dict:
        """
        Index a codebase by:
        1. Loading files with FileLoader
        2. Chunking with smart Chunker
        3. Generating embeddings
        4. Storing in ChromaDB
        """
        # Configure loader with exclude patterns
        if exclude_patterns:
            self.loader.exclude_patterns = exclude_patterns
        
        # Step 1: Load all files (run in thread to avoid blocking)
        print(f"📂 Loading files from {path}...")
        loaded_files: List[LoadedFile] = await asyncio.to_thread(
            self.loader.load_directory, path
        )
        
        if not loaded_files:
            return {
                "files_indexed": 0,
                "chunks_created": 0,
                "path": path,
                "error": "No supported files found"
            }
        
        # Get loading stats
        load_stats = self.loader.get_stats(loaded_files)
        print(f"📄 Loaded {load_stats['total_files']} files")
        
        # Step 2: Chunk files based on their type (run in thread to avoid blocking)
        print("✂️  Chunking files...")
        chunks: List[Chunk] = await asyncio.to_thread(
            self.chunker.chunk_files, loaded_files
        )
        
        # Get chunking stats
        chunk_stats = self.chunker.get_stats(chunks)
        print(f"📦 Created {chunk_stats['total_chunks']} chunks")
        
        # Step 3: Convert to LangChain Documents
        documents = []
        for chunk in chunks:
            # Build rich metadata
            metadata = {
                "source": chunk.source_file,
                "file_type": chunk.file_type.value,
                "chunk_type": chunk.chunk_type,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line,
                "chunk_id": chunk.id,
            }
            # Add extra metadata from the chunk
            for key, value in chunk.metadata.items():
                # Skip complex objects, only keep simple types
                if isinstance(value, (str, int, float, bool)):
                    metadata[key] = value
                elif isinstance(value, list) and value and isinstance(value[0], str):
                    metadata[key] = ", ".join(value[:5])  # Join first 5 items
            
            documents.append(Document(
                page_content=chunk.content,
                metadata=metadata
            ))
        
        # Update collection name if project_name is provided
        if project_name:
            self.collection_name = project_name
        
        # Step 4: Create vector store (run in thread - embedding is CPU intensive)
        print(f"🧠 Generating embeddings and storing in ChromaDB (collection: {self.collection_name})...")
        self.vectorstore = await asyncio.to_thread(
            Chroma.from_documents,
            documents=documents,
            embedding=self.embeddings,
            persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
            collection_name=self.collection_name
        )
        
        print("✅ Indexing complete!")
        
        return {
            "files_indexed": load_stats['total_files'],
            "chunks_created": chunk_stats['total_chunks'],
            "path": path,
            "stats": {
                "files_by_type": load_stats['by_type'],
                "chunks_by_type": chunk_stats['by_type'],
                "avg_chunk_size": chunk_stats['avg_chunk_size'],
            }
        }
    
    async def query(
        self,
        question: str,
        context_limit: int = 5
    ) -> Dict:
        """
        Query the indexed codebase using RAG.
        """
        if self.vectorstore is None:
            # Try to load existing vectorstore
            self.vectorstore = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
        
        # Custom prompt for code understanding
        prompt_template = """You are an expert software engineer analyzing a codebase.
Use the following code context to answer the question. Be specific and reference
the actual code when possible.

Context:
{context}

Question: {question}

Provide a clear, detailed answer that:
1. Directly addresses the question
2. References specific files and code when relevant
3. Explains the reasoning and connections
4. Suggests where to look for more details if applicable

Answer:"""

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context", "question"]
        )
        
        # Create retrieval chain
        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": context_limit}
            ),
            return_source_documents=True,
            chain_type_kwargs={"prompt": PROMPT}
        )
        
        result = qa_chain.invoke({"query": question})
        
        # Extract sources with rich metadata
        sources = []
        for doc in result.get("source_documents", []):
            source_info = {
                "file": doc.metadata.get("source", "unknown"),
                "chunk_type": doc.metadata.get("chunk_type", "unknown"),
                "lines": f"{doc.metadata.get('start_line', '?')}-{doc.metadata.get('end_line', '?')}",
                "snippet": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
            }
            
            # Add terraform-specific info if available
            if "terraform_id" in doc.metadata:
                source_info["terraform_id"] = doc.metadata["terraform_id"]
            
            sources.append(source_info)
        
        return {
            "answer": result["result"],
            "sources": sources
        }
    
    def get_relevant_context(self, query: str, k: int = 5) -> List[Dict]:
        """
        Get relevant code chunks for a query without generating an answer.
        Useful for the agent to gather context before synthesizing.
        """
        if self.vectorstore is None:
            self.vectorstore = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
        
        docs = self.vectorstore.similarity_search(query, k=k)
        
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "file_type": doc.metadata.get("file_type", "unknown"),
                "chunk_type": doc.metadata.get("chunk_type", "unknown"),
                "lines": f"{doc.metadata.get('start_line', '?')}-{doc.metadata.get('end_line', '?')}",
            }
            for doc in docs
        ]
    
    def get_relevant_context_with_scores(
        self, 
        query: str, 
        k: int = 5,
        score_threshold: float = 0.0
    ) -> List[Dict]:
        """
        Get relevant chunks with similarity scores.
        Higher scores = more relevant.
        """
        if self.vectorstore is None:
            self.vectorstore = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
        
        # Get docs with scores
        docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)
        
        results = []
        for doc, score in docs_with_scores:
            if score >= score_threshold:
                results.append({
                    "content": doc.page_content,
                    "source": doc.metadata.get("source", "unknown"),
                    "file_type": doc.metadata.get("file_type", "unknown"),
                    "chunk_type": doc.metadata.get("chunk_type", "unknown"),
                    "score": score,
                })
        
        return results
    
    async def search_by_file_type(
        self,
        query: str,
        file_type: str,
        k: int = 5
    ) -> List[Dict]:
        """
        Search within a specific file type.
        e.g., search_by_file_type("state machine", "terraform", k=5)
        """
        if self.vectorstore is None:
            self.vectorstore = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
        
        # Use metadata filtering
        docs = self.vectorstore.similarity_search(
            query,
            k=k,
            filter={"file_type": file_type}
        )
        
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "chunk_type": doc.metadata.get("chunk_type", "unknown"),
            }
            for doc in docs
        ]
    
    async def search_by_chunk_type(
        self,
        query: str,
        chunk_type: str,
        k: int = 5
    ) -> List[Dict]:
        """
        Search within a specific chunk type.
        e.g., search_by_chunk_type("authentication", "function", k=5)
        """
        if self.vectorstore is None:
            self.vectorstore = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
        
        docs = self.vectorstore.similarity_search(
            query,
            k=k,
            filter={"chunk_type": chunk_type}
        )
        
        return [
            {
                "content": doc.page_content,
                "source": doc.metadata.get("source", "unknown"),
                "file_type": doc.metadata.get("file_type", "unknown"),
            }
            for doc in docs
        ]
    
    def clear_index(self):
        """Clear the vector store."""
        if self.vectorstore:
            self.vectorstore.delete_collection()
            self.vectorstore = None
