"""
Application configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional, Literal
from enum import Enum


class LLMProvider(str, Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    BEDROCK = "bedrock"
    AZURE = "azure"


class VectorDBProvider(str, Enum):
    """Supported vector database providers"""
    CHROMA = "chroma"
    PGVECTOR = "pgvector"
    PINECONE = "pinecone"
    QDRANT = "qdrant"


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # =========================================================================
    # Server Configuration
    # =========================================================================
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # =========================================================================
    # LLM Provider Selection
    # =========================================================================
    LLM_PROVIDER: LLMProvider = LLMProvider.OPENAI
    
    # =========================================================================
    # OpenAI Configuration
    # =========================================================================
    OPENAI_API_KEY: str = ""
    LLM_MODEL: str = "gpt-4o"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # =========================================================================
    # Anthropic Configuration
    # =========================================================================
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    
    # =========================================================================
    # AWS Bedrock Configuration
    # =========================================================================
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    BEDROCK_MODEL_ID: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    
    # =========================================================================
    # Azure OpenAI Configuration
    # =========================================================================
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"
    AZURE_OPENAI_API_VERSION: str = "2024-02-15-preview"
    
    # =========================================================================
    # Vector Database Selection
    # =========================================================================
    VECTOR_DB_PROVIDER: VectorDBProvider = VectorDBProvider.CHROMA
    
    # =========================================================================
    # ChromaDB Configuration (Default)
    # =========================================================================
    CHROMA_PERSIST_DIRECTORY: str = "./data/chroma"
    CHROMA_COLLECTION_NAME: str = "codebase"
    
    # =========================================================================
    # PostgreSQL + pgvector Configuration
    # =========================================================================
    POSTGRES_URL: str = ""
    PGVECTOR_COLLECTION: str = "codebase"
    
    # =========================================================================
    # Pinecone Configuration
    # =========================================================================
    PINECONE_API_KEY: str = ""
    PINECONE_ENVIRONMENT: str = ""
    PINECONE_INDEX_NAME: str = "coderag"
    
    # =========================================================================
    # Qdrant Configuration
    # =========================================================================
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "codebase"
    
    # =========================================================================
    # RAG Configuration
    # =========================================================================
    MAX_FILE_SIZE_KB: int = 500
    CHUNK_SIZE: int = 1500
    CHUNK_OVERLAP: int = 200
    CONTEXT_LIMIT: int = 5
    
    SUPPORTED_EXTENSIONS: List[str] = [
        ".py", ".pyi",                    # Python
        ".js", ".jsx", ".mjs",            # JavaScript
        ".ts", ".tsx",                    # TypeScript
        ".go",                            # Go
        ".rs",                            # Rust
        ".java",                          # Java
        ".cpp", ".c", ".h", ".hpp",       # C/C++
        ".tf", ".tfvars",                 # Terraform
        ".yaml", ".yml",                  # YAML
        ".json",                          # JSON
        ".toml",                          # TOML
        ".md", ".mdx",                    # Markdown
        ".sql",                           # SQL
        ".sh", ".bash",                   # Shell
        ".dockerfile",                    # Docker
    ]
    
    # =========================================================================
    # Agent Configuration
    # =========================================================================
    AGENT_MAX_ITERATIONS: int = 10
    AGENT_TEMPERATURE: float = 0.1
    
    # =========================================================================
    # Security (Production)
    # =========================================================================
    API_KEY: Optional[str] = None
    JWT_SECRET: Optional[str] = None
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        use_enum_values = True
    
    def get_llm_config(self) -> dict:
        """Get configuration for the selected LLM provider."""
        if self.LLM_PROVIDER == LLMProvider.OPENAI:
            return {
                "provider": "openai",
                "api_key": self.OPENAI_API_KEY,
                "model": self.LLM_MODEL,
            }
        elif self.LLM_PROVIDER == LLMProvider.ANTHROPIC:
            return {
                "provider": "anthropic",
                "api_key": self.ANTHROPIC_API_KEY,
                "model": self.ANTHROPIC_MODEL,
            }
        elif self.LLM_PROVIDER == LLMProvider.BEDROCK:
            return {
                "provider": "bedrock",
                "aws_access_key_id": self.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": self.AWS_SECRET_ACCESS_KEY,
                "region": self.AWS_REGION,
                "model_id": self.BEDROCK_MODEL_ID,
            }
        elif self.LLM_PROVIDER == LLMProvider.AZURE:
            return {
                "provider": "azure",
                "api_key": self.AZURE_OPENAI_API_KEY,
                "endpoint": self.AZURE_OPENAI_ENDPOINT,
                "deployment": self.AZURE_OPENAI_DEPLOYMENT,
                "api_version": self.AZURE_OPENAI_API_VERSION,
            }
        else:
            raise ValueError(f"Unknown LLM provider: {self.LLM_PROVIDER}")
    
    def get_vectordb_config(self) -> dict:
        """Get configuration for the selected vector database."""
        if self.VECTOR_DB_PROVIDER == VectorDBProvider.CHROMA:
            return {
                "provider": "chroma",
                "persist_directory": self.CHROMA_PERSIST_DIRECTORY,
                "collection_name": self.CHROMA_COLLECTION_NAME,
            }
        elif self.VECTOR_DB_PROVIDER == VectorDBProvider.PGVECTOR:
            return {
                "provider": "pgvector",
                "connection_string": self.POSTGRES_URL,
                "collection_name": self.PGVECTOR_COLLECTION,
            }
        elif self.VECTOR_DB_PROVIDER == VectorDBProvider.PINECONE:
            return {
                "provider": "pinecone",
                "api_key": self.PINECONE_API_KEY,
                "environment": self.PINECONE_ENVIRONMENT,
                "index_name": self.PINECONE_INDEX_NAME,
            }
        elif self.VECTOR_DB_PROVIDER == VectorDBProvider.QDRANT:
            return {
                "provider": "qdrant",
                "url": self.QDRANT_URL,
                "api_key": self.QDRANT_API_KEY,
                "collection_name": self.QDRANT_COLLECTION,
            }
        else:
            raise ValueError(f"Unknown vector DB provider: {self.VECTOR_DB_PROVIDER}")


settings = Settings()
