"""
FastAPI route definitions for all API endpoints.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.core.config import get_settings
from app.core.logging import logger
from app.models.schemas import (
    QueryRequest,
    QueryResponse,
    UploadResponse,
    EvaluationRequest,
    EvaluationResult,
    HealthResponse,
    ErrorResponse,
    UserResponse,
)
from app.services.document_processor import DocumentProcessor
from app.services.vector_store import VectorStoreBase, create_vector_store
from app.services.llm_service import LLMService
from app.services.agent_workflow import ResearchAgent
from app.services.auth_service import get_current_user

router = APIRouter()

# ── Dependency injection (singleton services) ────────────────────

_vector_store: VectorStoreBase | None = None
_llm_service: LLMService | None = None
_agent: ResearchAgent | None = None
_doc_processor: DocumentProcessor | None = None


def get_vector_store() -> VectorStoreBase:
    global _vector_store
    if _vector_store is None:
        _vector_store = create_vector_store()
    return _vector_store


def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


def get_agent() -> ResearchAgent:
    global _agent
    if _agent is None:
        _agent = ResearchAgent(get_vector_store(), get_llm_service())
    return _agent


def get_doc_processor() -> DocumentProcessor:
    global _doc_processor
    if _doc_processor is None:
        _doc_processor = DocumentProcessor()
    return _doc_processor


# ── Endpoints ────────────────────────────────────────────────────

@router.post(
    "/upload-doc",
    response_model=UploadResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def upload_document(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Upload a PDF document for ingestion into the RAG system.
    The document is extracted, chunked, embedded, and stored in the vector database.
    """
    settings = get_settings()

    # Validate file type
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Maximum is {settings.max_file_size_mb}MB.",
        )

    try:
        processor = get_doc_processor()
        vector_store = get_vector_store()

        # Save and process
        file_path = await processor.save_upload(content, file.filename)
        chunks = await processor.process_pdf(file_path, file.filename)

        # Store in vector DB
        count = await vector_store.add_documents(chunks)

        doc_id = chunks[0].metadata.get("document_id", "unknown") if chunks else "unknown"

        logger.info(f"Document uploaded: {file.filename} ({count} chunks)")
        return UploadResponse(
            document_id=doc_id,
            filename=file.filename,
            total_chunks=count,
            message=f"Successfully processed {file.filename}: {count} chunks indexed.",
        )

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/query",
    response_model=QueryResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def query_documents(
    request: QueryRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Query the research assistant. The agent automatically decides the best
    strategy: RAG search, web search, summarization, or comparison.
    """
    try:
        agent = get_agent()
        response = await agent.run(request)
        return response

    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/evaluate",
    response_model=EvaluationResult,
    responses={500: {"model": ErrorResponse}},
)
async def evaluate_system(
    request: EvaluationRequest,
    current_user: UserResponse = Depends(get_current_user),
):
    """
    Evaluate the RAG system using RAGAS metrics.
    Runs the provided queries through the pipeline and measures quality.
    """
    try:
        from app.services.evaluator import RAGEvaluator

        evaluator = RAGEvaluator(get_agent())
        result = await evaluator.evaluate(
            queries=request.queries,
            ground_truths=request.ground_truths,
        )
        return result

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="RAGAS evaluation dependencies not installed. Run: pip install ragas",
        )
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint returning system status."""
    settings = get_settings()
    vs = get_vector_store()

    return HealthResponse(
        status="healthy",
        version="1.0.0",
        vector_store=settings.vector_store_type,
        llm_provider=settings.llm_provider,
        documents_loaded=vs.document_count(),
    )
