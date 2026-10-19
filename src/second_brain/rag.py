import logging
from typing import List, Dict, Any

from .supabase_client import supabase
from .embedding import EmbeddingManager
from .llm import GeminiLLM


class RAGPipeline:

    def __init__(self):
        self.embedding_manager = EmbeddingManager()
        self.llm = GeminiLLM()
        self.logger = logging.getLogger(__name__)

    def add_chunks(
        self,
        document_id: str,
        user_id: str,
        chunks: List[Dict[str, Any]]
    ):
        if not chunks:
            return []

        texts = [
            chunk["content"]
            for chunk in chunks
        ]

        embeddings = self.embedding_manager.embed_texts(texts)

        rows = []

        for index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            rows.append({
                "document_id": document_id,
                "user_id": user_id,
                "chunk_index": index,
                "content": chunk["content"],
                "page_number": chunk.get("page_number"),
                "metadata": chunk.get("metadata", {}),
                "embedding": embedding
            })

        try:
            response = supabase.table("document_chunks").insert(rows).execute()
        except Exception as exc:
            if "user_id" not in str(exc).lower():
                raise
            self.logger.warning("Document user_id column is not migrated; storing legacy chunk")
            legacy_rows = [{key: value for key, value in row.items() if key != "user_id"} for row in rows]
            response = supabase.table("document_chunks").insert(legacy_rows).execute()

        return response.data

    def search(
        self,
        query: str,
        user_id: str,
        top_k: int = 5
    ):
        query_embedding = (
            self.embedding_manager
            .embed_query(query)
        )

        try:
            response = supabase.rpc(
                "match_document_chunks_for_user",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.30,
                    "match_count": top_k,
                    "requesting_user_id": user_id,
                }
            ).execute()
        except Exception as exc:
            self.logger.warning("User-scoped retrieval is not migrated: %s", exc)
            response = supabase.rpc(
                "match_document_chunks",
                {
                    "query_embedding": query_embedding,
                    "match_threshold": 0.30,
                    "match_count": top_k,
                }
            ).execute()

        unique_results = []
        seen = set()
        for result in response.data or []:
            key = (
                result.get("document_id"),
                result.get("page_number"),
                result.get("content", "").strip(),
            )
            if key in seen:
                continue
            seen.add(key)
            unique_results.append(result)
        return unique_results

    def query(
        self,
        question: str,
        user_id: str,
        top_k: int = 8
    ):
        results = self.search(
            question,
            user_id,
            top_k
        )

        if not results:
            return {
                "answer": (
                    "I couldn't find relevant information "
                    "in your uploaded documents."
                ),
                "sources": []
            }

        context_parts = []

        sources = []

        for index, result in enumerate(results, start=1):

            content = result.get("content", "")

            filename = result.get(
                "filename",
                "Unknown document"
            )

            page = result.get("page_number")

            similarity = result.get(
                "similarity",
                0
            )

            context_parts.append(
                f"""
SOURCE {index}
Document: {filename}
Page: {page}

Content:
{content}
"""
            )

            sources.append({
                "source": filename,
                "page": page,
                "score": round(
                    float(similarity),
                    4
                )
            })

        context = "\n".join(context_parts)

        answer = self.llm.generate_answer(
            question,
            context
        )

        return {
            "answer": answer,
            "sources": sources
        }