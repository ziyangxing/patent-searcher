"""Import real patent data into the local search index."""
import asyncio
import json
import os
from app.search.faiss_index import faiss_manager
from app.services.embedding import embedding_service

DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "real_patents.json")


def load_patents() -> list[dict]:
    """Load real patent data from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []


async def build_index():
    """Build FAISS index from real patent data."""
    patents = load_patents()
    if not patents:
        print("No patent data found. Run download first.")
        return 0

    texts = []
    ids_list = []
    for p in patents:
        full_text = f"{p['title']} {p['abstract']}"
        texts.append(full_text)
        ids_list.append(p["patent_number"])

    faiss_manager.build_index(texts, ids_list)
    faiss_manager.save()
    print(f"FAISS index built: {len(texts)} patents -> {faiss_manager.size} vectors")
    return len(texts)


async def main():
    print(f"Loading patents from {DATA_FILE}...")
    count = await build_index()
    if count == 0:
        print("ERROR: No patent data. Download patents first via SerpAPI.")
    else:
        print(f"Done: {count} real patents indexed for semantic search.")


if __name__ == "__main__":
    asyncio.run(main())
