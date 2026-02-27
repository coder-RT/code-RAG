"""
RAG Engine - Core RAG functionality for code understanding
"""

import asyncio
import re
from typing import List, Dict, Optional, Tuple

from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain.schema import Document
import chromadb

from app.core.config import settings, EmbeddingProvider
from app.services.loader import FileLoader, LoadedFile
from app.services.chunker import Chunker, Chunk


# Common file extensions to detect in queries
FILE_EXTENSIONS = r'\.(?:md|py|ts|tsx|js|jsx|go|rs|java|tf|yaml|yml|json|sql|sh|css|scss|html)'

def extract_file_path_from_query(query: str) -> Optional[str]:
    """
    Extract a file path from a query if the user is asking about a specific file.
    Returns the file path pattern to search for, or None if no file path detected.
    """
    query_lower = query.lower()
    
    # Pattern to match file paths with common extensions
    # Matches: path/to/file.ext (with various path formats)
    file_path_pattern = r'([a-zA-Z0-9_\-./]+' + FILE_EXTENSIONS + r')'
    
    # First, check for backtick quoted paths: `path/to/file.md`
    backtick_match = re.search(r'`([^`]+' + FILE_EXTENSIONS + r')`', query_lower)
    if backtick_match:
        return backtick_match.group(1)
    
    # Common action words that precede file paths
    action_patterns = [
        r'(?:read|explain|show|open|view|look\s+at|analyze|understand|summarize)\s+(?:the\s+)?(?:file\s+)?(?:contents?\s+of\s+)?' + file_path_pattern,
        r'(?:what\s+(?:does|is\s+in)|contents?\s+of|about)\s+' + file_path_pattern,
    ]
    
    for pattern in action_patterns:
        match = re.search(pattern, query_lower, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # Try to find any file path in the query
    all_paths = re.findall(file_path_pattern, query_lower)
    if all_paths:
        # Return the most specific path (longest one)
        return max(all_paths, key=len)
    
    return None


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
    
    def __init__(
        self, 
        embedding_provider: Optional[str] = None, 
        project_name: Optional[str] = None,
        llm_model: Optional[str] = None
    ):
        """
        Initialize RAG Engine.
        
        Args:
            embedding_provider: "openai" or "huggingface". Defaults to config setting.
            project_name: Project name to use as ChromaDB collection name.
            llm_model: LLM model to use for answering queries. Defaults to settings.LLM_MODEL.
        """
        self.embedding_provider = embedding_provider
        self.embeddings = get_embeddings(provider=embedding_provider)
        self.llm_model = llm_model or settings.LLM_MODEL
        self.llm = ChatOpenAI(
            model=self.llm_model,
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
    
    def _get_chunks_by_file_path(self, file_path: str, limit: int = 10) -> List[Document]:
        """
        Retrieve chunks that match a specific file path pattern.
        Uses direct ChromaDB access for metadata filtering.
        """
        client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        try:
            collection = client.get_collection(name=self.collection_name)
        except Exception:
            return []
        
        # Get all chunks (we'll filter in Python since ChromaDB doesn't support $contains)
        total = collection.count()
        matching_docs = []
        
        # Normalize file path for matching
        file_path_lower = file_path.lower()
        
        # Sample in batches to find matching files
        batch_size = 1000
        for offset in range(0, min(total, 20000), batch_size):
            results = collection.get(
                limit=batch_size,
                offset=offset,
                include=['metadatas', 'documents']
            )
            
            for i, meta in enumerate(results['metadatas']):
                source = meta.get('source', '').lower()
                # Check if the file path pattern matches
                if file_path_lower in source or source.endswith(file_path_lower):
                    doc = Document(
                        page_content=results['documents'][i],
                        metadata=meta
                    )
                    matching_docs.append(doc)
                    
                    if len(matching_docs) >= limit:
                        return matching_docs
        
        return matching_docs

    async def query(
        self,
        question: str,
        context_limit: int = 5,
        user_context: Optional[str] = None
    ) -> Dict:
        """
        Query the indexed codebase using RAG.
        Supports file-path-aware retrieval for specific file queries.
        Also supports user-provided context for direct LLM chat.
        
        Args:
            question: The question to answer
            context_limit: Max number of chunks to retrieve from codebase
            user_context: Optional user-provided content to include in context
        """
        # Custom prompt for code understanding
        prompt_template = """You are an expert software engineer assistant.
{context_intro}

{context}

Question: {question}

Provide a clear, detailed answer that:
1. Directly addresses the question
2. References specific code when relevant
3. Explains the reasoning and connections
4. Suggests where to look for more details if applicable

Answer:"""

        # If user provides context and no codebase retrieval needed
        if user_context and context_limit == 0:
            print("💬 Using user-provided context only (no RAG)")
            context_intro = "The user has provided the following content for you to analyze:"
            
            PROMPT = PromptTemplate(
                template=prompt_template,
                input_variables=["context_intro", "context", "question"]
            )
            
            formatted_prompt = PROMPT.format(
                context_intro=context_intro,
                context=user_context,
                question=question
            )
            response = self.llm.invoke(formatted_prompt)
            
            return {
                "answer": response.content if hasattr(response, 'content') else str(response),
                "sources": [{"file": "user-provided", "chunk_type": "user_context", "lines": "N/A", "snippet": user_context[:300] + "..." if len(user_context) > 300 else user_context}]
            }
        
        # Initialize vectorstore if needed for RAG
        if self.vectorstore is None:
            self.vectorstore = Chroma(
                persist_directory=settings.CHROMA_PERSIST_DIRECTORY,
                embedding_function=self.embeddings,
                collection_name=self.collection_name
            )
        
        # Check if the query is asking about a specific file
        file_path = extract_file_path_from_query(question)
        file_specific_docs = []
        
        if file_path:
            # Get chunks from the specific file
            file_specific_docs = self._get_chunks_by_file_path(file_path, limit=context_limit)
            if file_specific_docs:
                print(f"📂 Found {len(file_specific_docs)} chunks from file matching: {file_path}")
        
        # Build context intro based on what we have
        if user_context:
            context_intro = "You have access to BOTH user-provided content AND an indexed codebase. Use both to answer."
        else:
            context_intro = "You have FULL ACCESS to an indexed codebase. The relevant content is provided below. DO NOT say you cannot access files."

        PROMPT = PromptTemplate(
            template=prompt_template,
            input_variables=["context_intro", "context", "question"]
        )
        
        # If we found file-specific docs, use them directly with the LLM
        if file_specific_docs:
            # Build context from file-specific documents
            context_parts = []
            
            # Add user context first if provided
            if user_context:
                context_parts.append(f"### User-Provided Content:\n{user_context}")
            
            context_parts.append("### From Indexed Codebase:")
            for doc in file_specific_docs:
                source = doc.metadata.get('source', 'unknown')
                lines = f"{doc.metadata.get('start_line', '?')}-{doc.metadata.get('end_line', '?')}"
                context_parts.append(f"#### File: {source} (lines {lines})\n{doc.page_content}")
            
            context_text = "\n\n".join(context_parts)
            
            # Call LLM directly with the file-specific context
            formatted_prompt = PROMPT.format(
                context_intro=context_intro,
                context=context_text, 
                question=question
            )
            response = self.llm.invoke(formatted_prompt)
            
            # Build sources list
            sources = []
            if user_context:
                sources.append({
                    "file": "user-provided",
                    "chunk_type": "user_context",
                    "lines": "N/A",
                    "snippet": user_context[:300] + "..." if len(user_context) > 300 else user_context
                })
            for doc in file_specific_docs:
                sources.append({
                    "file": doc.metadata.get("source", "unknown"),
                    "chunk_type": doc.metadata.get("chunk_type", "unknown"),
                    "lines": f"{doc.metadata.get('start_line', '?')}-{doc.metadata.get('end_line', '?')}",
                    "snippet": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
                })
            
            return {
                "answer": response.content if hasattr(response, 'content') else str(response),
                "sources": sources
            }
        
        # Fall back to standard semantic search
        retrieved_docs = self.vectorstore.similarity_search(question, k=context_limit)
        
        # Build context from retrieved documents
        context_parts = []
        
        # Add user context first if provided
        if user_context:
            print("💬 Combining user context with RAG retrieval")
            context_parts.append(f"### User-Provided Content:\n{user_context}")
        
        context_parts.append("### From Indexed Codebase:")
        for doc in retrieved_docs:
            source = doc.metadata.get('source', 'unknown')
            lines = f"{doc.metadata.get('start_line', '?')}-{doc.metadata.get('end_line', '?')}"
            context_parts.append(f"#### File: {source} (lines {lines})\n{doc.page_content}")
        
        context_text = "\n\n".join(context_parts)
        
        # Call LLM with combined context
        formatted_prompt = PROMPT.format(
            context_intro=context_intro,
            context=context_text,
            question=question
        )
        response = self.llm.invoke(formatted_prompt)
        
        # Build sources list
        sources = []
        if user_context:
            sources.append({
                "file": "user-provided",
                "chunk_type": "user_context",
                "lines": "N/A",
                "snippet": user_context[:300] + "..." if len(user_context) > 300 else user_context
            })
        for doc in retrieved_docs:
            source_info = {
                "file": doc.metadata.get("source", "unknown"),
                "chunk_type": doc.metadata.get("chunk_type", "unknown"),
                "lines": f"{doc.metadata.get('start_line', '?')}-{doc.metadata.get('end_line', '?')}",
                "snippet": doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content
            }
            if "terraform_id" in doc.metadata:
                source_info["terraform_id"] = doc.metadata["terraform_id"]
            sources.append(source_info)
        
        return {
            "answer": response.content if hasattr(response, 'content') else str(response),
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
