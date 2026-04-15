"""Configuration settings for the research agent system."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # LLM Configuration
    LLM_API_KEY: Optional[str] = None
    LLM_MODEL_ID: str = "ark-code-latest"
    LLM_BASE_URL: Optional[str] = None

    # Keep OPENAI_* for backward compatibility
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL_NAME: str = "gpt-4o"
    OPENAI_BASE_URL: Optional[str] = None

    # Search Configuration
    TAVILY_API_KEY: Optional[str] = None
    SEARCH_ENGINE: str = "tavily"  # "tavily" or "duckduckgo"
    MAX_SEARCH_RESULTS: int = 5
    MAX_RESULT_LENGTH: int = 500  # Max characters per search result

    # Server Configuration
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # Agent Configuration
    MAX_RETRIES: int = 2
    ENABLE_SEARCH_CACHE: bool = True

    # Local knowledge base and RAG configuration
    DATA_DIR: str = "backend/data"
    PENDING_REPORT_DIR: str = "backend/data/pending_reports"
    KNOWLEDGE_BASE_DIR: str = "backend/data/markdown"

    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "research_agent_chunks_v2"

    EMBEDDING_MODEL_NAME: str = "BAAI/bge-small-zh-v1.5"
    EMBEDDING_DIM: int = 512

    RAG_CHUNK_SIZE: int = 800
    RAG_CHUNK_OVERLAP: int = 120
    RAG_TOP_K: int = 5
    RAG_MAX_SECTION_CHARS: int = 1800

    DENSE_TOP_K: int = 20
    SPARSE_TOP_K: int = 20
    HYBRID_TOP_K: int = 8
    RERANK_TOP_K: int = 5
    RRF_K: int = 60

    RERANK_MODEL_NAME: str = "BAAI/bge-reranker-base"
    ENABLE_RERANK: bool = False
    ENABLE_QUERY_REWRITE: bool = True
    ENABLE_SPARSE_SEARCH: bool = True

    # Get the effective API key (prefer LLM_API_KEY if set)
    def get_effective_api_key(self) -> Optional[str]:
        return self.LLM_API_KEY or self.OPENAI_API_KEY

    # Get the effective model name
    def get_effective_model(self) -> str:
        # If LLM_API_KEY is set, use LLM_MODEL_ID
        if self.LLM_API_KEY:
            return self.LLM_MODEL_ID
        return self.OPENAI_MODEL_NAME

    # Get the effective base URL
    def get_effective_base_url(self) -> Optional[str]:
        if self.LLM_API_KEY and self.LLM_BASE_URL:
            return self.LLM_BASE_URL
        return self.OPENAI_BASE_URL or None

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
