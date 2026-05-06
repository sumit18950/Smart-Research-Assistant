"""
Vector store abstraction supporting both FAISS (local) and Pinecone (cloud).
Switchable via VECTOR_STORE_TYPE environment variable.

Design Decision:
- Factory pattern lets us swap backends without changing calling code.
- FAISS is default for local dev (zero cost, fast iteration).
- Pinecone for production (managed, scalable, persistent).
"""

from abc import ABC, abstractmethod

from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS as LangchainFAISS

from app.core.config import get_settings
from app.core.logging import logger


class VectorStoreBase(ABC):
    """Abstract base for vector store implementations."""

    @abstractmethod
    async def add_documents(self, documents: list[Document]) -> int:
        """Add documents and return count of documents added."""
        ...

    @abstractmethod
    async def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        """Return top-k documents most similar to the query."""
        ...

    @abstractmethod
    async def similarity_search_with_score(
        self, query: str, k: int = 5
    ) -> list[tuple[Document, float]]:
        """Return top-k documents with their similarity scores."""
        ...

    @abstractmethod
    def document_count(self) -> int:
        """Return total number of documents in the store."""
        ...


class FAISSVectorStore(VectorStoreBase):
    """Local FAISS-based vector store. Persists to disk."""

    def __init__(self, embeddings: OpenAIEmbeddings):
        self.embeddings = embeddings
        self.settings = get_settings()
        self.store: LangchainFAISS | None = None
        self._load_existing()

    def _load_existing(self):
        """Try to load an existing FAISS index from disk."""
        index_path = self.settings.faiss_path
        try:
            if index_path.exists():
                self.store = LangchainFAISS.load_local(
                    str(index_path),
                    self.embeddings,
                    allow_dangerous_deserialization=True,
                )
                logger.info(f"Loaded existing FAISS index from {index_path}")
        except Exception as e:
            logger.warning(f"Could not load FAISS index: {e}")
            self.store = None

    def _save(self):
        """Persist the FAISS index to disk."""
        if self.store:
            self.store.save_local(str(self.settings.faiss_path))

    async def add_documents(self, documents: list[Document]) -> int:
        if not documents:
            return 0

        if self.store is None:
            self.store = LangchainFAISS.from_documents(documents, self.embeddings)
        else:
            self.store.add_documents(documents)

        self._save()
        logger.info(f"Added {len(documents)} documents to FAISS")
        return len(documents)

    async def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        if self.store is None:
            return []
        return self.store.similarity_search(query, k=k)

    async def similarity_search_with_score(
        self, query: str, k: int = 5
    ) -> list[tuple[Document, float]]:
        if self.store is None:
            return []
        return self.store.similarity_search_with_score(query, k=k)

    def document_count(self) -> int:
        if self.store is None:
            return 0
        return self.store.index.ntotal


class PineconeVectorStore(VectorStoreBase):
    """Pinecone cloud-based vector store."""

    def __init__(self, embeddings: OpenAIEmbeddings):
        from pinecone import Pinecone
        from langchain_pinecone import PineconeVectorStore as LCPinecone

        self.embeddings = embeddings
        settings = get_settings()

        pc = Pinecone(api_key=settings.pinecone_api_key)
        self.index = pc.Index(settings.pinecone_index_name)
        self.store = LCPinecone(
            index=self.index,
            embedding=embeddings,
            text_key="text",
        )
        logger.info(f"Connected to Pinecone index: {settings.pinecone_index_name}")

    async def add_documents(self, documents: list[Document]) -> int:
        if not documents:
            return 0
        self.store.add_documents(documents)
        logger.info(f"Added {len(documents)} documents to Pinecone")
        return len(documents)

    async def similarity_search(self, query: str, k: int = 5) -> list[Document]:
        return self.store.similarity_search(query, k=k)

    async def similarity_search_with_score(
        self, query: str, k: int = 5
    ) -> list[tuple[Document, float]]:
        return self.store.similarity_search_with_relevance_scores(query, k=k)

    def document_count(self) -> int:
        stats = self.index.describe_index_stats()
        return getattr(stats, "total_vector_count", 0)


def create_vector_store() -> VectorStoreBase:
    """Factory function to create the configured vector store."""
    settings = get_settings()

    embeddings = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        openai_api_key=settings.openai_api_key,
    )

    if settings.vector_store_type == "pinecone":
        logger.info("Using Pinecone vector store")
        return PineconeVectorStore(embeddings)
    else:
        logger.info("Using FAISS vector store")
        return FAISSVectorStore(embeddings)
