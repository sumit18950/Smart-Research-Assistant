"""
Pydantic schemas for request/response validation across all API endpoints.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# ── Auth Models ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(default="", max_length=100)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    created_at: str


# ── Document Models ──────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    title: str = ""
    source: str = ""
    date: str = ""
    doc_type: str = "pdf"
    page_number: int | None = None
    chunk_index: int | None = None


class DocumentChunk(BaseModel):
    content: str
    metadata: DocumentMetadata
    embedding: list[float] | None = None


class UploadResponse(BaseModel):
    document_id: str
    filename: str
    total_chunks: int
    message: str


# ── Query Models ─────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    use_web_search: bool = False
    compare_sources: bool = False


class SourceReference(BaseModel):
    title: str
    source: str
    page: int | None = None
    relevance_score: float
    snippet: str


class ComparisonEntry(BaseModel):
    source: str
    key_point: str
    stance: str


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceReference]
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    comparison_table: list[ComparisonEntry] | None = None
    strategy_used: str = "rag"
    token_usage: dict | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── Evaluation Models ────────────────────────────────────────────

class EvaluationRequest(BaseModel):
    queries: list[str]
    ground_truths: list[str] | None = None


class EvaluationResult(BaseModel):
    faithfulness: float
    answer_relevancy: float
    context_precision: float
    context_recall: float | None = None
    overall_score: float
    per_query_scores: list[dict] | None = None


# ── Health Check ─────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "healthy"
    version: str = "1.0.0"
    vector_store: str
    llm_provider: str
    documents_loaded: int = 0


# ── Error Response ───────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
    status_code: int = 500
