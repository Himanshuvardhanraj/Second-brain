import os
from typing import List

from google import genai
from google.genai import types


class EmbeddingManager:
    def __init__(self):
        self.client = genai.Client(
            api_key=os.environ["GEMINI_API_KEY"]
        )

        self.model = os.getenv(
            "GEMINI_EMBEDDING_MODEL",
            "gemini-embedding-2"
        )

        self.dimension = int(
            os.getenv("EMBEDDING_DIMENSION", "768")
        )

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        result = self.client.models.embed_content(
            model=self.model,
            contents=texts,
            config=types.EmbedContentConfig(
                output_dimensionality=self.dimension
            )
        )

        return [
            embedding.values
            for embedding in result.embeddings
        ]

    def embed_query(self, query: str) -> List[float]:
        result = self.client.models.embed_content(
            model=self.model,
            contents=query,
            config=types.EmbedContentConfig(
                output_dimensionality=self.dimension
            )
        )

        return result.embeddings[0].values