Smart Research Assistant (Multi-Source RAG System)
A production-grade AI research assistant that ingests PDFs, searches the web, and answers questions with citations, confidence scores, and comparative analysis — powered by LangChain, LangGraph, OpenAI/Claude, and FAISS/Pinecone.

Architecture
React Frontend ──> FastAPI Backend ──> LangGraph Agent
                                          │
                        ┌─────────────────┼─────────────────┐
                        ▼                 ▼                 ▼
                   RAG Search        Web Search        Summarize/Compare
                        │                 │                 │
                        └────────┬────────┘                 │
                                 ▼                          │
                          Vector Store (FAISS/Pinecone)     │
                                 │                          │
                                 └──────────┬───────────────┘
                                            ▼
                                    LLM (OpenAI/Claude)
                                            │
                                            ▼
                                    Guardrails Layer
                                            │
                                            ▼
                                  Structured Response
                                  (Answer + Citations + Confidence)
Data Flow
Ingestion: PDF upload → text extraction (PyPDF) → recursive chunking (1000 chars, 200 overlap) → embedding (OpenAI) → vector store
Query: User query → LangGraph agent classifies intent → retrieves context → injects into prompt → LLM generates grounded answer
Output: Structured response with answer, source citations, confidence score, optional comparison table
Evaluation: RAGAS metrics (faithfulness, relevancy, precision, recall)
Project Structure
smart-research-assistant/
├── backend/
│   ├── app/
│   │   ├── api/routes.py              # FastAPI endpoints
│   │   ├── core/
│   │   │   ├── config.py              # Environment config
│   │   │   ├── logging.py             # Structured logging
│   │   │   └── prompts.py             # All prompt templates
│   │   ├── models/schemas.py          # Pydantic request/response models
│   │   ├── services/
│   │   │   ├── document_processor.py  # PDF ingestion + chunking
│   │   │   ├── vector_store.py        # FAISS/Pinecone abstraction
│   │   │   ├── llm_service.py         # OpenAI/Claude LLM wrapper
│   │   │   ├── rag_pipeline.py        # Core RAG pipeline
│   │   │   ├── agent_workflow.py      # LangGraph agentic workflow
│   │   │   ├── web_scraper.py         # Web search + scraping
│   │   │   ├── guardrails.py          # Safety: injection, hallucination, confidence
│   │   │   └── evaluator.py           # RAGAS evaluation
│   │   └── main.py                    # FastAPI app entry point
│   ├── data/
│   │   ├── uploads/                   # Uploaded PDFs
│   │   └── vectorstore/               # FAISS index persistence
│   ├── tests/test_api.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ConfidenceIndicator.jsx
│   │   │   ├── SourcesList.jsx
│   │   │   └── ComparisonTable.jsx
│   │   ├── pages/
│   │   │   ├── UploadPage.jsx
│   │   │   ├── ChatPage.jsx
│   │   │   └── EvalPage.jsx
│   │   ├── services/api.js
│   │   ├── hooks/useApi.js
│   │   ├── styles/global.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── evaluation/run_evaluation.py
├── docker/
│   ├── Dockerfile.backend
│   ├── Dockerfile.frontend
│   └── nginx.conf
├── docker-compose.yml
└── README.md
Quick Start
Prerequisites
Python 3.11+
Node.js 18+
OpenAI API key (or Anthropic API key)
1. Backend Setup
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start backend
uvicorn app.main:app --reload --port 8000
2. Frontend Setup
cd frontend

npm install
npm run dev
# Opens at http://localhost:3000
3. Docker Deployment
# Copy and configure env
cp backend/.env.example backend/.env
# Edit backend/.env

# Build and run
docker-compose up --build
# Frontend: http://localhost
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
API Endpoints
Endpoint	Method	Description
/api/v1/upload-doc	POST	Upload and ingest a PDF document
/api/v1/query	POST	Query the research assistant
/api/v1/evaluate	POST	Run RAGAS evaluation
/api/v1/health	GET	System health check
Example: Upload Document
curl -X POST http://localhost:8000/api/v1/upload-doc \
  -F "file=@research_paper.pdf"
Response:

{
  "document_id": "a3b2c1d4e5f6g7h8",
  "filename": "research_paper.pdf",
  "total_chunks": 47,
  "message": "Successfully processed research_paper.pdf: 47 chunks indexed."
}
Example: Query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What methodology was used in the study?",
    "top_k": 5,
    "use_web_search": false,
    "compare_sources": false
  }'
Response:

{
  "answer": "The study employed a mixed-methods approach combining quantitative analysis with qualitative interviews. Specifically, the researchers used a randomized controlled trial (RCT) design with 500 participants [Source: research_paper]...",
  "sources": [
    {
      "title": "research_paper",
      "source": "research_paper.pdf",
      "page": 3,
      "relevance_score": 0.892,
      "snippet": "Our methodology follows a mixed-methods design..."
    }
  ],
  "confidence_score": 0.85,
  "comparison_table": null,
  "strategy_used": "rag",
  "token_usage": {
    "prompt_tokens": 1250,
    "completion_tokens": 340,
    "total_tokens": 1590
  }
}
Example: Evaluate
curl -X POST http://localhost:8000/api/v1/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "queries": [
      "What are the main findings?",
      "What limitations exist?"
    ],
    "ground_truths": [
      "The main findings show...",
      "Key limitations include..."
    ]
  }'
Key Design Decisions
Chunking Strategy
Recursive Character Splitting (1000 chars, 200 overlap) because:

Respects natural text boundaries (paragraphs > sentences > words)
1000 chars balances context richness with embedding precision
200-char overlap prevents information loss at chunk boundaries
Agentic Workflow (LangGraph)
The agent dynamically selects from 4 strategies:

RAG Search — documents have high-relevance matches
Web Search — documents lack context, supplement from web
Summarize — query asks for overview/digest
Compare — query asks to contrast sources
Vector Store Switching
Factory pattern allows swapping FAISS (local dev) ↔ Pinecone (production) via a single env variable, with no code changes.

Guardrails
Prompt injection detection: Regex patterns for common attacks
Confidence thresholding: Low-confidence answers get explicit warnings
Hallucination check: Optional LLM-based verification against context
Input sanitization: Null byte removal, length limits
Running Tests
cd backend
pip install pytest
pytest tests/ -v
Running RAGAS Evaluation
cd smart-research-assistant
python evaluation/run_evaluation.py
Configuration Reference
Variable	Default	Description
LLM_PROVIDER	openai	openai or anthropic
VECTOR_STORE_TYPE	faiss	faiss or pinecone
CHUNK_SIZE	1000	Characters per chunk
CHUNK_OVERLAP	200	Overlap between chunks
TOP_K_RESULTS	5	Default retrieval count
CONFIDENCE_THRESHOLD	0.6	Below this, answers get warnings
MAX_FILE_SIZE_MB	50	Upload size limit
Tech Stack
Layer	Technology
Frontend	React 18, Vite, Axios, react-dropzone, react-markdown
Backend	Python, FastAPI, Uvicorn
AI/ML	LangChain, LangGraph, OpenAI/Claude APIs
Vector DB	FAISS (local) / Pinecone (cloud)
Evaluation	RAGAS (faithfulness, relevancy, precision, recall)
Deployment	Docker, docker-compose, nginx
