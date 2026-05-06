"""
FastAPI application entry point.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.api.auth_routes import auth_router
from app.core.config import get_settings
from app.core.logging import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Starting Smart Research Assistant...")
    settings = get_settings()
    logger.info(f"LLM Provider: {settings.llm_provider}")
    logger.info(f"Vector Store: {settings.vector_store_type}")
    yield
    logger.info("Shutting down Smart Research Assistant...")


app = FastAPI(
    title="Smart Research Assistant",
    description="Multi-Source RAG System with agentic workflow, "
                "citation tracking, and evaluation pipeline.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(auth_router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
    )
