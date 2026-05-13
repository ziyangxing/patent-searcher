from sentence_transformers import SentenceTransformer
from app.core.config import settings


class EmbeddingService:
    def __init__(self):
        self.model: SentenceTransformer | None = None

    def load_model(self):
        self.model = SentenceTransformer(
            settings.EMBEDDING_MODEL,
            device=settings.EMBEDDING_DEVICE,
        )

    def encode(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        if self.model is None:
            self.load_model()
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return embeddings.tolist()

    def encode_single(self, text: str) -> list[float]:
        result = self.encode([text])
        return result[0]

    @property
    def dim(self) -> int:
        if self.model is None:
            self.load_model()
        return self.model.get_embedding_dimension()


embedding_service = EmbeddingService()
