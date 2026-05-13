"""Run the patent search API server."""
import sys
import time

print("Patent Searcher Server")
print("======================")

# Show progress during slow startup
print("[1/3] Importing modules...", end=" ", flush=True)
t0 = time.time()

# Pre-load to show progress instead of silent hang
from app.services.embedding import embedding_service
from app.search.faiss_index import faiss_manager

print(f"({time.time()-t0:.1f}s)")

print("[2/3] Loading embedding model (downloading on first run)...", end=" ", flush=True)
t1 = time.time()
embedding_service.load_model()
print(f"({time.time()-t1:.1f}s)  dim={embedding_service.dim}")

print("[3/3] Loading FAISS index...", end=" ", flush=True)
t2 = time.time()
ok = faiss_manager.load()
if ok:
    print(f"({time.time()-t2:.1f}s)  {faiss_manager.size} patents loaded")
else:
    print("(not found, run: python -m app.services.data_importer)")

print(f"Starting server on http://0.0.0.0:8766")
print(f"API docs: http://localhost:8766/docs")
print()

import uvicorn
uvicorn.run(
    "app.main:app",
    host="0.0.0.0",
    port=8766,
    log_level="info",
)
