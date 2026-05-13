import os
import pickle
import numpy as np
import faiss
from app.core.config import settings
from app.services.embedding import embedding_service


class FaissIndexManager:
    def __init__(self):
        self.index: faiss.IndexFlatIP | None = None
        self.id_map: list[str] = []

    def build_index(self, texts: list[str], ids: list[str]):
        embeddings = np.array(embedding_service.encode(texts)).astype("float32")
        dim = embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dim)
        self.index.add(embeddings)
        self.id_map = ids

    def save(self, path: str | None = None):
        if self.index is None:
            raise ValueError("No index to save")
        save_path = path or settings.FAISS_INDEX_PATH
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        faiss.write_index(self.index, save_path)
        with open(save_path + ".ids", "wb") as f:
            pickle.dump(self.id_map, f)

    def load(self, path: str | None = None):
        load_path = path or settings.FAISS_INDEX_PATH
        if not os.path.exists(load_path):
            return False
        self.index = faiss.read_index(load_path)
        with open(load_path + ".ids", "rb") as f:
            self.id_map = pickle.load(f)
        return True

    def search(self, query_text: str, k: int = 10) -> list[tuple[str, float]]:
        if self.index is None:
            raise ValueError("Index not loaded. Call load() or build_index() first.")
        query_vec = np.array([embedding_service.encode_single(query_text)]).astype(
            "float32"
        )
        scores, indices = self.index.search(query_vec, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.id_map):
                continue
            results.append((self.id_map[idx], float(score)))
        return results

    def search_by_vector(
        self, vector: list[float], k: int = 10
    ) -> list[tuple[str, float]]:
        if self.index is None:
            raise ValueError("Index not loaded.")
        query_vec = np.array([vector]).astype("float32")
        scores, indices = self.index.search(query_vec, k)
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.id_map):
                continue
            results.append((self.id_map[idx], float(score)))
        return results

    @property
    def size(self) -> int:
        return self.index.ntotal if self.index else 0


faiss_manager = FaissIndexManager()
