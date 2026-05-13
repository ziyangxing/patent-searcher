from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "Patent Searcher"
    DEBUG: bool = False
    CORS_ORIGINS: list[str] = ["*"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://patent:patent123@localhost:5432/patent_search"

    # Elasticsearch
    ES_HOST: str = "http://localhost:9200"
    ES_INDEX_NAME: str = "patents"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # LLM
    LLM_PROVIDER: str = "openai"
    LLM_MODEL: str = "gpt-4o"
    OPENAI_API_KEY: str = ""
    OPENAI_BASE_URL: str = ""
    ANTHROPIC_API_KEY: str = ""

    # Embedding
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DEVICE: str = "cpu"

    # Patent APIs
    EPO_OPS_KEY: str = ""
    EPO_OPS_SECRET: str = ""
    SERPAPI_KEY: str = ""  # Free at https://serpapi.com (100 searches/month)

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  # 50MB

    # FAISS
    FAISS_INDEX_PATH: str = "./data/faiss_index.bin"
    FAISS_DIM: int = 384

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
