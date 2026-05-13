from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api import search, patent, upload, chat
from app.services.embedding import embedding_service
from app.search.faiss_index import faiss_manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load models and indexes
    try:
        embedding_service.load_model()
    except Exception:
        pass
    try:
        faiss_manager.load()
    except Exception:
        pass
    yield
    # Shutdown: nothing to clean up


app = FastAPI(
    title="Patent Searcher API",
    description="智能专利检索工具 API",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(patent.router, prefix="/api/patent", tags=["patent"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "0.2.0"}
