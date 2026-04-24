"""Configuration settings for the research agent system."""
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"
load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Search Configuration
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
    KNOWLEDGE_BASE_DIR: str = "backend/data/markdown"

    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION: str = "research_agent_chunks_v2_d768"

    EMBEDDING_MODEL_NAME: str = "nlp_gte_sentence-embedding_chinese-base"
    EMBEDDING_MODEL_PATH: str = "backend/model/nlp_gte_sentence-embedding_chinese-base"
    # Must match the local embedding model output dimension and the Milvus dense_vector dimension.
    EMBEDDING_DIM: int = 768

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


settings = Settings()
