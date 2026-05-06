"""
Agentic workflow using LangGraph.
Dynamically decides whether to: use RAG, search the web, summarize, or compare.

State Machine:
  START → classify_query → [rag_search | web_search | summarize | compare] → apply_guardrails → END
"""

from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END

from app.core.logging import logger
from app.models.schemas import QueryRequest, QueryResponse
from app.services.vector_store import VectorStoreBase
from app.services.llm_service import LLMService
from app.services.rag_pipeline import RAGPipeline
from app.services.web_scraper import WebScraper
from app.services.guardrails import Guardrails


class AgentState(TypedDict):
    """State passed through the agent workflow graph."""
    query: str
    request: QueryRequest
    strategy: str
    response: QueryResponse | None
    context_score: float
    error: str | None


class ResearchAgent:
    """
    LangGraph-based agent that orchestrates the RAG pipeline.
    Chooses the best strategy based on query analysis and available context.
    """

    def __init__(
        self,
        vector_store: VectorStoreBase,
        llm_service: LLMService,
    ):
        self.vector_store = vector_store
        self.llm = llm_service
        self.rag = RAGPipeline(vector_store, llm_service)
        self.web_scraper = WebScraper()
        self.guardrails = Guardrails()
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Construct the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("classify", self._classify_query)
        workflow.add_node("rag_search", self._rag_search)
        workflow.add_node("web_search", self._web_search)
        workflow.add_node("summarize", self._summarize)
        workflow.add_node("compare", self._compare)
        workflow.add_node("guardrails", self._apply_guardrails)

        # Set entry point
        workflow.set_entry_point("classify")

        # Conditional routing based on classification
        workflow.add_conditional_edges(
            "classify",
            self._route_strategy,
            {
                "rag": "rag_search",
                "web": "web_search",
                "summarize": "summarize",
                "compare": "compare",
            },
        )

        # All strategy nodes lead to guardrails
        workflow.add_edge("rag_search", "guardrails")
        workflow.add_edge("web_search", "guardrails")
        workflow.add_edge("summarize", "guardrails")
        workflow.add_edge("compare", "guardrails")

        # Guardrails lead to end
        workflow.add_edge("guardrails", END)

        return workflow.compile()

    async def run(self, request: QueryRequest) -> QueryResponse:
        """Execute the agent workflow for a given query."""
        # Check for prompt injection first
        is_safe, reason = self.guardrails.check_prompt_injection(request.query)
        if not is_safe:
            return QueryResponse(
                answer=f"Query rejected: {reason}",
                sources=[],
                confidence_score=0.0,
                strategy_used="blocked",
            )

        sanitized_query = self.guardrails.sanitize_input(request.query)

        initial_state: AgentState = {
            "query": sanitized_query,
            "request": request,
            "strategy": "",
            "response": None,
            "context_score": 0.0,
            "error": None,
        }

        try:
            final_state = await self.graph.ainvoke(initial_state)
            if final_state.get("response"):
                return final_state["response"]
            return QueryResponse(
                answer="I was unable to generate a response. Please try rephrasing your question.",
                sources=[],
                confidence_score=0.0,
                strategy_used="error",
            )
        except Exception as e:
            logger.error(f"Agent workflow failed: {e}")
            return QueryResponse(
                answer=f"An error occurred while processing your query: {str(e)}",
                sources=[],
                confidence_score=0.0,
                strategy_used="error",
            )

    async def _classify_query(self, state: AgentState) -> AgentState:
        """Classify the query to determine the best strategy."""
        query = state["query"]
        request = state["request"]

        # If user explicitly requested web search or comparison
        if request.use_web_search:
            state["strategy"] = "web"
            return state
        if request.compare_sources:
            state["strategy"] = "compare"
            return state

        # Check how much relevant context we have
        docs_with_scores = await self.vector_store.similarity_search_with_score(query, k=3)

        if not docs_with_scores:
            state["context_score"] = 0.0
            state["strategy"] = "web"
            return state

        # Average relevance score (lower distance = better for FAISS)
        avg_score = sum(1 - score for _, score in docs_with_scores) / len(docs_with_scores)
        state["context_score"] = avg_score

        # Keyword-based classification
        query_lower = query.lower()
        if any(kw in query_lower for kw in ["summarize", "summary", "overview", "digest"]):
            state["strategy"] = "summarize"
        elif any(kw in query_lower for kw in ["compare", "difference", "versus", "vs"]):
            state["strategy"] = "compare"
        elif avg_score < 0.3:
            # Context too weak, supplement with web search
            state["strategy"] = "web"
        else:
            state["strategy"] = "rag"

        logger.info(f"Query classified as: {state['strategy']} (context_score: {avg_score:.3f})")
        return state

    def _route_strategy(self, state: AgentState) -> str:
        """Route to the appropriate strategy node."""
        return state["strategy"]

    async def _rag_search(self, state: AgentState) -> AgentState:
        """Execute standard RAG search."""
        request = state["request"]
        top_k = request.top_k
        response = await self.rag.query(state["query"], top_k=top_k)
        state["response"] = response
        return state

    async def _web_search(self, state: AgentState) -> AgentState:
        """Execute web search and merge with RAG results."""
        web_docs = await self.web_scraper.search_web(state["query"])
        request = state["request"]
        top_k = request.top_k
        response = await self.rag.query(
            state["query"],
            top_k=top_k,
            extra_context=web_docs,
        )
        response.strategy_used = "web_search"
        state["response"] = response
        return state

    async def _summarize(self, state: AgentState) -> AgentState:
        """Summarize documents related to the query."""
        response = await self.rag.summarize(state["query"])
        state["response"] = response
        return state

    async def _compare(self, state: AgentState) -> AgentState:
        """Compare multiple sources."""
        request = state["request"]
        top_k = request.top_k
        response = await self.rag.query(state["query"], top_k=top_k, compare=True)
        state["response"] = response
        return state

    async def _apply_guardrails(self, state: AgentState) -> AgentState:
        """Apply guardrails to the response."""
        if state.get("response"):
            state["response"] = self.guardrails.check_confidence(state["response"])
        return state
