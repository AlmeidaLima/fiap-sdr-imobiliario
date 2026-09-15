from sentence_transformers import SentenceTransformer


class EmbeddingService:

    MODEL_NAME = "intfloat/multilingual-e5-small"

    def __init__(self):
        self.model = SentenceTransformer(
            self.MODEL_NAME
        )

    def embed_document(
            self,
            content: str,
    ) -> list[float]:
        text = f"passage: {content}"

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()

    def embed_query(
            self,
            query: str,
    ) -> list[float]:
        text = f"query: {query}"

        embedding = self.model.encode(
            text,
            normalize_embeddings=True,
        )

        return embedding.tolist()