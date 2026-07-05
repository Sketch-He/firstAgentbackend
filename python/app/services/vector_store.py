"""向量存储服务：基于 ChromaDB 的文档向量化与检索。"""

from dataclasses import dataclass

import chromadb
from openai import AsyncOpenAI

from app.core.config import get_settings

COLLECTION_NAME = "knowledge_base"


@dataclass
class SearchResult:
    """向量检索结果。"""

    document_id: str
    filename: str
    chunk_index: int
    snippet: str
    score: float


class VectorStoreService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client: chromadb.ClientAPI | None = None
        self._embedding_client: AsyncOpenAI | None = None

    def _get_chroma_client(self) -> chromadb.ClientAPI:
        if self._client is None:
            persist_dir = str(self.settings.resolved_chroma_dir)
            self._client = chromadb.PersistentClient(path=persist_dir)
        return self._client

    def _get_collection(self) -> chromadb.Collection:
        return self._get_chroma_client().get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )

    def _get_embedding_client(self) -> AsyncOpenAI:
        if self._embedding_client is None:
            self._embedding_client = AsyncOpenAI(
                api_key=self.settings.effective_embedding_api_key,
                base_url=self.settings.effective_embedding_base_url,
            )
        return self._embedding_client

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """调用 Embedding API 将文本向量化。"""
        client = self._get_embedding_client()
        response = await client.embeddings.create(
            model=self.settings.embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def add_document(
        self,
        user_id: str,
        document_id: str,
        filename: str,
        chunks: list[str],
    ) -> None:
        """将文档分块向量化并存入 ChromaDB。"""
        if not chunks:
            return

        embeddings = await self.embed_texts(chunks)
        collection = self._get_collection()

        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "user_id": user_id,
                "document_id": document_id,
                "chunk_index": i,
                "filename": filename,
            }
            for i in range(len(chunks))
        ]

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

    async def search(
        self,
        user_id: str,
        query: str,
        top_k: int | None = None,
    ) -> list[SearchResult]:
        """按用户隔离进行向量检索。"""
        if top_k is None:
            top_k = self.settings.rag_top_k

        query_embeddings = await self.embed_texts([query])
        collection = self._get_collection()

        results = collection.query(
            query_embeddings=query_embeddings,
            n_results=top_k,
            where={"user_id": user_id},
        )

        search_results: list[SearchResult] = []
        if not results["ids"] or not results["ids"][0]:
            return search_results

        for i in range(len(results["ids"][0])):
            metadata = results["metadatas"][0][i] if results["metadatas"] else {}
            distance = results["distances"][0][i] if results["distances"] else 0.0
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score: 1 - distance/2
            score = 1.0 - distance / 2.0

            search_results.append(
                SearchResult(
                    document_id=metadata.get("document_id", ""),
                    filename=metadata.get("filename", ""),
                    chunk_index=metadata.get("chunk_index", 0),
                    snippet=results["documents"][0][i] if results["documents"] else "",
                    score=score,
                )
            )

        return search_results

    def delete_document(self, user_id: str, document_id: str) -> None:
        """删除指定文档的所有向量。"""
        collection = self._get_collection()
        collection.delete(
            where={"$and": [{"user_id": user_id}, {"document_id": document_id}]}
        )
