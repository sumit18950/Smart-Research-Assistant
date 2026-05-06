"""
Document ingestion pipeline: PDF extraction, text chunking, and metadata handling.

Chunking Strategy (Recursive Character Splitting):
- We use RecursiveCharacterTextSplitter because it respects natural text boundaries
  (paragraphs, sentences, words) rather than splitting mid-sentence.
- Chunk size of 1000 chars balances context richness with embedding quality.
- 200-char overlap ensures continuity across chunk boundaries so retrieval
  doesn't miss information split across two chunks.
"""

import uuid
import hashlib
from pathlib import Path
from datetime import datetime

from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

from app.core.config import get_settings
from app.core.logging import logger
from app.models.schemas import DocumentMetadata


class DocumentProcessor:
    def __init__(self):
        settings = get_settings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        self.upload_dir = settings.upload_path

    def generate_doc_id(self, filename: str, content_sample: str) -> str:
        """Generate a deterministic document ID from filename + content hash."""
        hash_input = f"{filename}:{content_sample[:500]}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    async def process_pdf(self, file_path: Path, original_filename: str) -> list[Document]:
        """Extract text from PDF and split into chunks with metadata."""
        logger.info(f"Processing PDF: {original_filename}")

        loader = PyPDFLoader(str(file_path))
        raw_pages = loader.load()

        if not raw_pages:
            raise ValueError(f"No content extracted from {original_filename}")

        doc_id = self.generate_doc_id(
            original_filename,
            raw_pages[0].page_content if raw_pages else "",
        )

        # Attach rich metadata to each page before chunking
        for i, page in enumerate(raw_pages):
            page.metadata.update({
                "document_id": doc_id,
                "title": original_filename.rsplit(".", 1)[0],
                "source": original_filename,
                "page_number": i + 1,
                "total_pages": len(raw_pages),
                "doc_type": "pdf",
                "ingested_at": datetime.utcnow().isoformat(),
            })

        # Split into chunks
        chunks = self.text_splitter.split_documents(raw_pages)

        # Add chunk indices
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
            chunk.metadata["total_chunks"] = len(chunks)

        logger.info(
            f"Processed {original_filename}: {len(raw_pages)} pages -> {len(chunks)} chunks"
        )
        return chunks

    async def process_text(self, text: str, metadata: DocumentMetadata) -> list[Document]:
        """Process raw text content into chunks."""
        doc_id = self.generate_doc_id(metadata.title, text)

        doc = Document(
            page_content=text,
            metadata={
                "document_id": doc_id,
                "title": metadata.title,
                "source": metadata.source,
                "doc_type": metadata.doc_type,
                "date": metadata.date,
                "ingested_at": datetime.utcnow().isoformat(),
            },
        )

        chunks = self.text_splitter.split_documents([doc])
        for idx, chunk in enumerate(chunks):
            chunk.metadata["chunk_index"] = idx
            chunk.metadata["total_chunks"] = len(chunks)

        return chunks

    async def save_upload(self, file_content: bytes, filename: str) -> Path:
        """Save uploaded file to disk and return the path."""
        safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
        file_path = self.upload_dir / safe_name
        file_path.write_bytes(file_content)
        logger.info(f"Saved upload: {file_path}")
        return file_path
