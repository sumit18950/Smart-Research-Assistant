"""
Core RAG pipeline: query → embed → retrieve → re-rank → context → LLM.
"""

from langchain.schema import Document

from app.core.config import get_settings
from app.core.logging import logger
from app.core.prompts import QUERY_TEMPLATE, COMPARISON_TEMPLATE, SUMMARIZATION_TEMPLATE
from app.models.schemas import QueryResponse, SourceReference, ComparisonEntry
from app.services.vector_store import VectorStoreBase
from app.services.llm_service import LLMService


class RAGPipeline:
    def __init__(self, vector_store: VectorStoreBase, llm_service: LLMService):
        self.vector_store = vector_store
        self.llm = llm_service
        self.settings = get_settings()

    async def query(
        self,
        query: str,
        top_k: int = 5,
        compare: bool = False,
        extra_context: list[Document] | None = None,
    ) -> QueryResponse:
        """Execute the full RAG pipeline for a query."""
        self.llm.reset_token_usage()

        # Step 1: Retrieve relevant documents with scores
        results_with_scores = await self.vector_store.similarity_search_with_score(
            query, k=top_k
        )

        # Merge with any extra context (e.g., from web search)
        all_docs = []
        for doc, score in results_with_scores:
            doc.metadata["relevance_score"] = 1 - score  # Convert distance to similarity
            all_docs.append(doc)

        if extra_context:
            for doc in extra_context:
                doc.metadata.setdefault("relevance_score", 0.5)
                all_docs.append(doc)

        if not all_docs:
            return QueryResponse(
                answer="I don't have any relevant documents to answer this question. "
                       "Please upload documents or enable web search.",
                sources=[],
                confidence_score=0.0,
                strategy_used="rag",
            )

        # Step 2: Re-rank by relevance score (simple score-based re-ranking)
        all_docs.sort(key=lambda d: d.metadata.get("relevance_score", 0), reverse=True)
        top_docs = all_docs[:top_k]

        # Step 3: Build context string
        context = self._build_context(top_docs)

        # Step 4: Choose prompt template and generate
        if compare:
            prompt = COMPARISON_TEMPLATE.format(context=context, query=query)
        else:
            prompt = QUERY_TEMPLATE.format(context=context, query=query)

        result = await self.llm.generate(prompt)

        # Step 5: Build source references
        sources = self._build_sources(top_docs)

        # Step 6: Build comparison table if requested
        comparison = None
        if compare and len(set(d.metadata.get("source", "") for d in top_docs)) > 1:
            comparison = self._build_comparison(result["answer"], top_docs)

        return QueryResponse(
            answer=result["answer"],
            sources=sources,
            confidence_score=result["confidence"],
            comparison_table=comparison,
            strategy_used="rag_compare" if compare else "rag",
            token_usage=result["token_usage"],
        )

    async def summarize(self, query: str, top_k: int = 10) -> QueryResponse:
        """Summarize documents related to a query."""
        self.llm.reset_token_usage()

        docs = await self.vector_store.similarity_search(query, k=top_k)
        if not docs:
            return QueryResponse(
                answer="No documents available to summarize.",
                sources=[],
                confidence_score=0.0,
                strategy_used="summarize",
            )

        context = self._build_context(docs)
        prompt = SUMMARIZATION_TEMPLATE.format(context=context)
        result = await self.llm.generate(prompt)

        return QueryResponse(
            answer=result["answer"],
            sources=self._build_sources(docs),
            confidence_score=result["confidence"],
            strategy_used="summarize",
            token_usage=result["token_usage"],
        )

    def _build_context(self, docs: list[Document]) -> str:
        """Format documents into a context string for the LLM prompt."""
        sections = []
        for i, doc in enumerate(docs, 1):
            title = doc.metadata.get("title", "Unknown")
            source = doc.metadata.get("source", "Unknown")
            page = doc.metadata.get("page_number", "N/A")
            sections.append(
                f"[Document {i}] Title: {title} | Source: {source} | Page: {page}\n"
                f"{doc.page_content}"
            )
        return "\n\n---\n\n".join(sections)

    def _build_sources(self, docs: list[Document]) -> list[SourceReference]:
        """Convert retrieved documents to source references."""
        seen = set()
        sources = []
        for doc in docs:
            source_key = doc.metadata.get("source", "")
            if source_key in seen:
                continue
            seen.add(source_key)

            sources.append(SourceReference(
                title=doc.metadata.get("title", "Unknown"),
                source=source_key,
                page=doc.metadata.get("page_number"),
                relevance_score=round(doc.metadata.get("relevance_score", 0.0), 3),
                snippet=doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
            ))
        return sources

    def _build_comparison(self, answer: str, docs: list[Document]) -> list[ComparisonEntry]:
        """Extract comparison entries from the answer and source documents."""
        entries = []
        source_groups: dict[str, list[Document]] = {}
        for doc in docs:
            src = doc.metadata.get("source", "Unknown")
            source_groups.setdefault(src, []).append(doc)

        for source, group_docs in source_groups.items():
            key_content = group_docs[0].page_content[:150]
            entries.append(ComparisonEntry(
                source=source,
                key_point=key_content,
                stance="See full analysis above",
            ))
        return entries
