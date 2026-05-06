# Smart Research Assistant - Complete Documentation

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Technology Stack](#2-technology-stack)
3. [System Architecture & How Components Connect](#3-system-architecture--how-components-connect)
4. [Complete Project Structure](#4-complete-project-structure)
5. [How to Run the Application](#5-how-to-run-the-application)
6. [How Each Technology Works Together](#6-how-each-technology-works-together)
7. [API Reference](#7-api-reference)
8. [Frontend Pages & Features](#8-frontend-pages--features)
9. [RAG Pipeline - Deep Dive](#9-rag-pipeline---deep-dive)
10. [Agentic Workflow Explained](#10-agentic-workflow-explained)
11. [Evaluation Pipeline (RAGAS)](#11-evaluation-pipeline-ragas)
12. [Security & Guardrails](#12-security--guardrails)
13. [Authentication System](#13-authentication-system)
14. [Configuration Reference](#14-configuration-reference)
15. [Deployment Guide](#15-deployment-guide)
16. [Example Input/Output](#16-example-inputoutput)
17. [Troubleshooting](#17-troubleshooting)

---

## 1. Project Overview

The **Smart Research Assistant** is a production-grade Multi-Source RAG (Retrieval-Augmented Generation) system that allows users to:

- Upload PDF documents to build a searchable knowledge base
- Ask natural language questions and receive AI-generated answers
- Get accurate source citations with every answer
- See confidence scores indicating answer reliability
- Compare findings across multiple sources
- Optionally supplement answers with live web search results
- Evaluate the system's quality using industry-standard RAGAS metrics

This is not a simple chatbot. It is an **agentic AI system** that dynamically decides the best strategy to answer each query - whether to search uploaded documents, fetch information from the web, summarize content, or compare across sources.

---

## 2. Technology Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.3 | UI framework with modern hooks (useState, useEffect, useCallback, useContext) |
| **Vite** | 6.0 | Fast build tool and dev server with hot module replacement |
| **Axios** | 1.7 | HTTP client for API calls with interceptors for JWT auth |
| **react-dropzone** | 14.3 | Drag-and-drop file upload component |
| **react-markdown** | 9.0 | Renders Markdown-formatted AI responses |
| **lucide-react** | 0.468 | Icon library (optional) |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.11+ | Core backend language |
| **FastAPI** | 0.115 | Async web framework with automatic OpenAPI docs |
| **Uvicorn** | 0.34 | ASGI server to run FastAPI |
| **Pydantic** | 2.10 | Data validation and serialization for all request/response models |
| **pydantic-settings** | 2.7 | Environment variable configuration management |

### AI / ML Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **LangChain** | 0.3.14 | Framework for building LLM-powered pipelines (chains, retrievers, document loaders) |
| **LangGraph** | 0.2.60 | State machine framework for building agentic workflows with conditional routing |
| **OpenAI API** | 1.58 | LLM (GPT-4o) for answer generation + embeddings (text-embedding-3-small) for vector search |
| **Anthropic API** | - | Alternative LLM provider (Claude) - switchable via config |
| **FAISS** | 1.9 | Facebook's vector similarity search library for local vector storage |
| **Pinecone** | 5.0 | Cloud-managed vector database (production alternative to FAISS) |

### Document Processing

| Technology | Version | Purpose |
|------------|---------|---------|
| **PyPDF** | 5.1 | PDF text extraction |
| **BeautifulSoup4** | 4.12 | HTML parsing for web scraping |
| **httpx** | 0.28 | Async HTTP client for web requests |

### Evaluation

| Technology | Version | Purpose |
|------------|---------|---------|
| **RAGAS** | 0.2.6 | RAG evaluation framework measuring faithfulness, relevancy, precision, recall |
| **datasets** | 3.2 | HuggingFace datasets library (required by RAGAS) |

### Authentication

| Technology | Version | Purpose |
|------------|---------|---------|
| **passlib** | 1.7.4 | Password hashing with BCrypt |
| **python-jose** | 3.3.0 | JWT token creation and verification |

### Deployment

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization for backend and frontend |
| **docker-compose** | Multi-container orchestration |
| **nginx** | Reverse proxy for frontend serving and API routing |

---

## 3. System Architecture & How Components Connect

### High-Level Architecture

```
+------------------------------------------------------------------+
|                         USER'S BROWSER                           |
|                                                                  |
|   +------------------+  +----------------+  +-----------------+  |
|   |  Upload Page     |  |  Chat Page     |  |  Eval Page      |  |
|   |  (Drag & Drop)   |  |  (Q&A + Cite)  |  |  (RAGAS Metrics)|  |
|   +--------+---------+  +-------+--------+  +--------+--------+  |
|            |                     |                     |          |
|   +--------+---------------------+---------------------+-------+  |
|   |                    React App (Vite)                         |  |
|   |  - AuthProvider (JWT Context)                               |  |
|   |  - Axios (auto-attaches Bearer token)                       |  |
|   +------------------------------+------------------------------+  |
+----------------------------------|-------------------------------+
                                   | HTTP (JSON + multipart)
                                   | Port 3000 → proxy → 8000
                                   v
+------------------------------------------------------------------+
|                       FASTAPI BACKEND                            |
|                       (Port 8000)                                |
|                                                                  |
|  +--------------------+  +------------------------------------+  |
|  | Auth Routes        |  | Protected Routes                   |  |
|  | POST /auth/register|  | POST /upload-doc  (JWT required)   |  |
|  | POST /auth/login   |  | POST /query       (JWT required)   |  |
|  | GET  /auth/me      |  | POST /evaluate    (JWT required)   |  |
|  +--------------------+  | GET  /health      (public)         |  |
|                          +------------------------------------+  |
|                                    |                             |
|  +-----------------------------+   |   +----------------------+  |
|  |     AUTH SERVICE            |   |   |   GUARDRAILS         |  |
|  |  - BCrypt password hash     |   |   | - Prompt injection   |  |
|  |  - JWT create/verify        |   |   | - Input sanitization |  |
|  |  - User store (JSON file)   |   |   | - Confidence check   |  |
|  +-----------------------------+   |   | - Hallucination      |  |
|                                    |   +----------------------+  |
|                                    v                             |
|  +----------------------------------------------------------+   |
|  |              LANGGRAPH AGENT WORKFLOW                     |   |
|  |                                                          |   |
|  |   START --> [Classify Query]                             |   |
|  |                   |                                      |   |
|  |        +----------+----------+-----------+               |   |
|  |        v          v          v           v               |   |
|  |    [RAG Search] [Web Search] [Summarize] [Compare]       |   |
|  |        |          |          |           |               |   |
|  |        +----------+----------+-----------+               |   |
|  |                   |                                      |   |
|  |                   v                                      |   |
|  |           [Apply Guardrails]                             |   |
|  |                   |                                      |   |
|  |                   v                                      |   |
|  |                  END --> Response                        |   |
|  +----------------------------------------------------------+   |
|                   |                      |                       |
|                   v                      v                       |
|  +------------------------+  +---------------------------+      |
|  |   DOCUMENT PROCESSOR   |  |     RAG PIPELINE          |      |
|  | - PDF extraction       |  | - Query embedding         |      |
|  | - Text chunking        |  | - Similarity search       |      |
|  | - Metadata tagging     |  | - Re-ranking              |      |
|  +----------+-------------+  | - Context building        |      |
|             |                | - Prompt construction      |      |
|             v                | - LLM generation          |      |
|  +------------------------+  +-------------+-------------+      |
|  |    VECTOR STORE        |                |                     |
|  |  (Factory Pattern)     |                v                     |
|  |                        |  +---------------------------+      |
|  |  if FAISS:             |  |     LLM SERVICE           |      |
|  |    Local disk index    |  | - OpenAI (GPT-4o)         |      |
|  |                        |  |   OR                      |      |
|  |  if Pinecone:          |  | - Anthropic (Claude)      |      |
|  |    Cloud managed       |  | - Token usage tracking    |      |
|  +------------------------+  +---------------------------+      |
|                                                                  |
|  +----------------------------------------------------------+   |
|  |   WEB SCRAPER (httpx + BeautifulSoup)                    |   |
|  |   - SerpAPI for Google search results                     |   |
|  |   - Page fetching and text extraction                     |   |
|  +----------------------------------------------------------+   |
|                                                                  |
|  +----------------------------------------------------------+   |
|  |   RAGAS EVALUATOR                                        |   |
|  |   - Runs queries through full pipeline                    |   |
|  |   - Measures: faithfulness, relevancy, precision, recall  |   |
|  +----------------------------------------------------------+   |
+------------------------------------------------------------------+
```

### How the Connections Work

**1. Browser --> React Frontend (Port 3000)**
- User interacts with the React UI
- Vite dev server serves the frontend and proxies `/api/*` requests to port 8000
- Axios HTTP client sends all API requests with JWT token in Authorization header

**2. React Frontend --> FastAPI Backend (Port 8000)**
- All communication happens over HTTP REST API (JSON)
- File uploads use `multipart/form-data`
- JWT Bearer tokens authenticate every protected request
- CORS middleware allows cross-origin requests from the frontend

**3. FastAPI Backend --> LangGraph Agent**
- When a `/query` request arrives, FastAPI passes it to the `ResearchAgent`
- The agent is a LangGraph state machine that processes the query through nodes
- Each node is an async function that modifies the shared state

**4. LangGraph Agent --> Vector Store**
- The agent retrieves relevant document chunks using similarity search
- Embeddings are generated via OpenAI's `text-embedding-3-small` model
- FAISS stores vectors locally on disk; Pinecone stores them in the cloud
- The factory pattern (`create_vector_store()`) picks the right backend from config

**5. LangGraph Agent --> LLM (OpenAI / Claude)**
- Retrieved context is injected into a carefully crafted prompt
- The LLM generates a grounded answer with citations
- Token usage is tracked for cost monitoring

**6. FastAPI Backend --> Auth Service**
- Registration hashes passwords with BCrypt and stores users in a JSON file
- Login verifies credentials and returns a signed JWT token
- Protected endpoints use FastAPI's `Depends(get_current_user)` to validate tokens

---

## 4. Complete Project Structure

```
smart-research-assistant/
|
+-- backend/                          # Python FastAPI backend
|   +-- app/
|   |   +-- __init__.py
|   |   +-- main.py                   # FastAPI app entry point, CORS, router mounting
|   |   +-- api/
|   |   |   +-- __init__.py
|   |   |   +-- routes.py             # Protected endpoints: upload, query, evaluate, health
|   |   |   +-- auth_routes.py        # Auth endpoints: register, login, me
|   |   +-- core/
|   |   |   +-- __init__.py
|   |   |   +-- config.py             # Settings class loading from .env
|   |   |   +-- logging.py            # Structured logger setup
|   |   |   +-- prompts.py            # All LLM prompt templates
|   |   +-- models/
|   |   |   +-- __init__.py
|   |   |   +-- schemas.py            # Pydantic models for all request/response types
|   |   +-- services/
|   |   |   +-- __init__.py
|   |   |   +-- auth_service.py       # User registration, login, JWT management
|   |   |   +-- document_processor.py # PDF extraction, text chunking, metadata
|   |   |   +-- vector_store.py       # FAISS + Pinecone with factory pattern
|   |   |   +-- llm_service.py        # OpenAI/Claude wrapper with token tracking
|   |   |   +-- rag_pipeline.py       # Core RAG: retrieve -> rerank -> generate
|   |   |   +-- agent_workflow.py     # LangGraph state machine with 4 strategies
|   |   |   +-- web_scraper.py        # SerpAPI search + page scraping (async httpx)
|   |   |   +-- guardrails.py         # Prompt injection, hallucination, confidence
|   |   |   +-- evaluator.py          # RAGAS evaluation pipeline
|   |   +-- utils/
|   |       +-- __init__.py
|   +-- data/
|   |   +-- uploads/                  # Stored PDF files
|   |   +-- vectorstore/              # FAISS index files
|   +-- tests/
|   |   +-- __init__.py
|   |   +-- test_api.py               # API endpoint tests
|   +-- requirements.txt              # All Python dependencies
|   +-- .env.example                  # Template environment variables
|   +-- .env                          # Your actual API keys (git-ignored)
|   +-- .gitignore
|
+-- frontend/                         # React frontend
|   +-- public/
|   +-- src/
|   |   +-- components/
|   |   |   +-- ConfidenceIndicator.jsx  # Visual confidence score bar
|   |   |   +-- SourcesList.jsx          # Citation/source reference list
|   |   |   +-- ComparisonTable.jsx      # Multi-source comparison table
|   |   +-- pages/
|   |   |   +-- LoginPage.jsx            # User sign-in form
|   |   |   +-- RegisterPage.jsx         # User registration form
|   |   |   +-- UploadPage.jsx           # PDF drag-and-drop upload
|   |   |   +-- ChatPage.jsx             # Main Q&A chat interface
|   |   |   +-- EvalPage.jsx             # RAGAS evaluation dashboard
|   |   +-- services/
|   |   |   +-- api.js                   # All API functions + JWT interceptor
|   |   +-- hooks/
|   |   |   +-- useApi.js                # Generic hook for API calls with loading/error
|   |   |   +-- useAuth.jsx              # Auth context provider + login/register/logout
|   |   +-- styles/
|   |   |   +-- global.css               # Complete dark theme CSS
|   |   +-- App.jsx                      # Root app with auth gating + tab navigation
|   |   +-- main.jsx                     # React DOM entry point
|   +-- index.html
|   +-- package.json
|   +-- vite.config.js                   # Vite config with API proxy
|   +-- .gitignore
|
+-- evaluation/
|   +-- run_evaluation.py             # Standalone RAGAS evaluation script
|
+-- docker/
|   +-- Dockerfile.backend            # Python backend container
|   +-- Dockerfile.frontend           # Node build + nginx container
|   +-- nginx.conf                    # Reverse proxy config
|
+-- docker-compose.yml                # Multi-container orchestration
+-- README.md                         # Quick-start guide
+-- DOCUMENTATION.md                  # This file
```

---

## 5. How to Run the Application

### Prerequisites

Before starting, ensure you have:

| Requirement | Minimum Version | Check Command |
|-------------|----------------|---------------|
| Python | 3.11+ | `python --version` |
| Node.js | 18+ | `node --version` |
| npm | 9+ | `npm --version` |
| OpenAI API Key | - | Get from https://platform.openai.com/api-keys |

### Step 1: Install Python (if not installed)

**Windows (PowerShell):**
```powershell
winget install Python.Python.3.12 --accept-package-agreements --accept-source-agreements
```

**Mac:**
```bash
brew install python@3.12
```

**Linux:**
```bash
sudo apt update && sudo apt install python3.12 python3.12-venv
```

After installing, **close and reopen your terminal**.

### Step 2: Set Up the Backend

```bash
# Navigate to backend
cd smart-research-assistant/backend

# Create a Python virtual environment
python -m venv venv

# Activate it
# Windows PowerShell:
.\venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Mac/Linux:
source venv/bin/activate

# Install all Python dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Open .env in a text editor and add your OpenAI API key:
#   OPENAI_API_KEY=sk-proj-your-key-here

# Start the backend server
uvicorn app.main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Started reloader process
```

Verify it works: open http://localhost:8000/docs in your browser to see the Swagger API docs.

### Step 3: Set Up the Frontend

Open a **new terminal** (keep the backend running):

```bash
# Navigate to frontend
cd smart-research-assistant/frontend

# Install Node.js dependencies
npm install

# Start the development server
npm run dev
```

You should see:
```
  VITE v6.0.5  ready in 300ms
  -> Local: http://localhost:3000/
```

### Step 4: Use the Application

1. Open **http://localhost:3000** in your browser
2. You will see the **Register** page - create an account
3. After registering, you are automatically logged in
4. Go to **Upload Documents** tab - drag and drop PDF files
5. Go to **Research Chat** tab - ask questions about your documents
6. Go to **Evaluation** tab - run RAGAS quality metrics

### Running with Docker (Alternative)

If you prefer Docker instead of manual setup:

```bash
cd smart-research-assistant

# Configure your API keys
cp backend/.env.example backend/.env
# Edit backend/.env with your keys

# Build and start both containers
docker-compose up --build

# Access:
# Frontend: http://localhost
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

---

## 6. How Each Technology Works Together

### The Complete Request Flow (Step by Step)

Here is exactly what happens when a user asks a question:

```
User types: "What are the key findings of the study?"
    |
    v
[1] React ChatPage captures the query
    - Calls queryAssistant() from api.js
    - Axios interceptor attaches JWT token: "Authorization: Bearer <token>"
    |
    v
[2] HTTP POST arrives at FastAPI /api/v1/query
    - FastAPI validates request body against QueryRequest Pydantic model
    - get_current_user() dependency extracts JWT, verifies it, loads user
    - If token invalid -> 401 Unauthorized
    |
    v
[3] ResearchAgent.run() is called (LangGraph)
    - Guardrails.check_prompt_injection() scans query for injection patterns
    - If injection detected -> returns blocked response immediately
    - Guardrails.sanitize_input() cleans the query (removes null bytes, limits length)
    |
    v
[4] LangGraph State Machine starts
    - Entry node: _classify_query()
    - Checks if user explicitly requested web_search or compare_sources
    - If not, runs similarity_search on vector store to check context quality
    - Calculates average relevance score
    - Classifies as: "rag" | "web" | "summarize" | "compare"
    |
    v
[5] Strategy Node executes (e.g., _rag_search)
    - RAGPipeline.query() is called
    |
    v
[6] RAG Pipeline executes:
    a) vector_store.similarity_search_with_score(query, k=5)
       - Query text -> OpenAI Embedding API -> 1536-dim vector
       - FAISS finds nearest neighbors by L2 distance
       - Returns top-5 document chunks with distances
    |
    b) Re-rank results by relevance score (distance -> similarity)
    |
    c) Build context string from top chunks:
       "[Document 1] Title: paper.pdf | Source: paper.pdf | Page: 3
        <chunk text content>"
    |
    d) Inject context into prompt template:
       SYSTEM_PROMPT (grounding rules + citation rules) +
       QUERY_TEMPLATE.format(context=..., query=...)
    |
    e) LLMService.generate() sends to OpenAI GPT-4o:
       - SystemMessage: grounding rules
       - HumanMessage: context + query
       - Returns answer with citations and CONFIDENCE score
       - Tracks token usage (prompt + completion tokens)
    |
    v
[7] Guardrails node: _apply_guardrails()
    - Checks confidence score against threshold (default: 0.6)
    - If low confidence: prepends warning to answer
    |
    v
[8] QueryResponse is built:
    {
      answer: "The study found that... [Source: paper.pdf]",
      sources: [{title, source, page, relevance_score, snippet}],
      confidence_score: 0.85,
      comparison_table: null,
      strategy_used: "rag",
      token_usage: {prompt_tokens: 1250, completion_tokens: 340, total_tokens: 1590}
    }
    |
    v
[9] FastAPI serializes response as JSON and sends to frontend
    |
    v
[10] React ChatPage receives response:
     - Displays answer with Markdown rendering
     - Shows strategy badge ("RAG Search")
     - Renders confidence bar (green/yellow/red)
     - Lists source citations with relevance scores
     - Shows token count
```

### How Key Technologies Connect

**React <-> FastAPI:**
- Vite's proxy (`vite.config.js`) forwards `/api/*` to `localhost:8000`
- Axios interceptor auto-attaches JWT from localStorage
- FastAPI's CORS middleware allows cross-origin requests

**FastAPI <-> LangChain:**
- FastAPI routes call service classes that use LangChain components
- `DocumentProcessor` uses LangChain's `PyPDFLoader` and `RecursiveCharacterTextSplitter`
- `VectorStore` uses LangChain's `FAISS` and `PineconeVectorStore` wrappers
- `LLMService` uses LangChain's `ChatOpenAI` and `ChatAnthropic`

**LangChain <-> LangGraph:**
- LangGraph provides the state machine that orchestrates multiple LangChain components
- The agent workflow is a directed graph where each node calls LangChain services
- State flows through the graph: classify -> strategy -> guardrails -> end

**LangChain <-> OpenAI API:**
- Embeddings: `OpenAIEmbeddings` calls `text-embedding-3-small` to convert text to 1536-dim vectors
- Chat: `ChatOpenAI` calls `gpt-4o` with system + human messages
- All calls go through LangChain's abstraction layer (easy to swap providers)

**FAISS <-> Disk:**
- FAISS index is an in-memory data structure
- `save_local()` persists it to `data/vectorstore/faiss_index/`
- `load_local()` restores it on startup
- This means your indexed documents survive server restarts

---

## 7. API Reference

All endpoints are prefixed with `/api/v1`.

### Authentication Endpoints (Public)

#### POST /api/v1/auth/register
Create a new user account.

**Request Body:**
```json
{
  "username": "researcher1",
  "email": "researcher@example.com",
  "password": "securepass123",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "a1b2c3d4e5f6g7h8",
  "username": "researcher1",
  "email": "researcher@example.com",
  "full_name": "John Doe",
  "created_at": "2026-05-06T10:30:00+00:00"
}
```

**Errors:** 409 if username or email already exists.

#### POST /api/v1/auth/login
Authenticate and receive a JWT token.

**Request Body:**
```json
{
  "username": "researcher1",
  "password": "securepass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

**Errors:** 401 if credentials are wrong.

#### GET /api/v1/auth/me
Get current user profile. Requires `Authorization: Bearer <token>` header.

**Response (200):**
```json
{
  "id": "a1b2c3d4e5f6g7h8",
  "username": "researcher1",
  "email": "researcher@example.com",
  "full_name": "John Doe",
  "created_at": "2026-05-06T10:30:00+00:00"
}
```

### Protected Endpoints (Require JWT)

All requests must include: `Authorization: Bearer <your-jwt-token>`

#### POST /api/v1/upload-doc
Upload a PDF document for ingestion.

**Request:** `multipart/form-data` with `file` field (PDF only, max 50MB).

**Response (200):**
```json
{
  "document_id": "a3b2c1d4e5f6g7h8",
  "filename": "research_paper.pdf",
  "total_chunks": 47,
  "message": "Successfully processed research_paper.pdf: 47 chunks indexed."
}
```

#### POST /api/v1/query
Query the research assistant.

**Request Body:**
```json
{
  "query": "What methodology was used in the study?",
  "top_k": 5,
  "use_web_search": false,
  "compare_sources": false
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| query | string | required | The research question (1-2000 chars) |
| top_k | int | 5 | Number of documents to retrieve (1-20) |
| use_web_search | bool | false | Force web search supplementation |
| compare_sources | bool | false | Force multi-source comparison mode |

**Response (200):**
```json
{
  "answer": "The study employed a mixed-methods approach... [Source: research_paper]",
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
  },
  "timestamp": "2026-05-06T10:35:00Z"
}
```

#### POST /api/v1/evaluate
Run RAGAS evaluation on test queries.

**Request Body:**
```json
{
  "queries": [
    "What are the main findings?",
    "What limitations exist?"
  ],
  "ground_truths": [
    "The main findings show significant improvement...",
    "Key limitations include small sample size..."
  ]
}
```

**Response (200):**
```json
{
  "faithfulness": 0.875,
  "answer_relevancy": 0.812,
  "context_precision": 0.793,
  "context_recall": 0.756,
  "overall_score": 0.809,
  "per_query_scores": [...]
}
```

#### GET /api/v1/health
Public health check endpoint.

**Response (200):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "vector_store": "faiss",
  "llm_provider": "openai",
  "documents_loaded": 142
}
```

---

## 8. Frontend Pages & Features

### Login Page
- Clean dark-themed sign-in form
- Username + password fields
- Error messages displayed inline
- Link to switch to registration

### Register Page
- Full name, username, email, password + confirm password
- Client-side validation (password match, min length)
- Auto-login after successful registration
- Error display for duplicate username/email

### Upload Documents Page
- Drag-and-drop zone powered by react-dropzone
- Accepts PDF files only (validated client + server side)
- Shows processing spinner during upload
- Lists uploaded documents with chunk counts and document IDs
- Success/failure indicators per file

### Research Chat Page
- Chat-style interface with user/assistant message bubbles
- Markdown rendering for AI responses (headers, lists, bold, code)
- **Strategy badge**: Shows which strategy was used (RAG / Web / Summary / Compare)
- **Confidence indicator**: Color-coded bar (green >70%, yellow 40-70%, red <40%)
- **Source citations**: Expandable list with title, snippet, relevance score, page number
- **Comparison table**: Rendered when compare mode finds multiple sources
- **Token counter**: Shows prompt + completion token usage
- Options checkboxes: "Include web search" and "Compare sources"
- Loading spinner with animated dots during processing

### Evaluation Page
- Text areas for entering test queries (one per line)
- Optional ground truth answers for recall measurement
- Score cards showing overall, faithfulness, relevancy, precision, recall
- Color-coded scores (green/yellow/red)
- Per-query results table with individual metric breakdowns

---

## 9. RAG Pipeline - Deep Dive

### What is RAG?

RAG (Retrieval-Augmented Generation) solves a fundamental LLM limitation: LLMs only know what was in their training data. RAG gives them access to your specific documents by:

1. **Indexing**: Converting documents into searchable vectors
2. **Retrieving**: Finding relevant chunks for each query
3. **Generating**: Using retrieved context to produce grounded answers

### Our Chunking Strategy

We use **Recursive Character Text Splitting** because:

```
Document Text
    |
    v
Split by: "\n\n" (paragraphs first)
    |
    v
If chunk > 1000 chars, split by: "\n" (line breaks)
    |
    v
If still > 1000 chars, split by: ". " (sentences)
    |
    v
If still > 1000 chars, split by: " " (words)
    |
    v
Result: chunks of ~1000 chars with 200-char overlap
```

**Why 1000 characters?**
- Too small (200): Loses context, retrieval finds irrelevant fragments
- Too large (5000): Dilutes relevant information, wastes embedding precision
- 1000: Good balance of context richness and retrieval accuracy

**Why 200-char overlap?**
- Prevents information loss at chunk boundaries
- If a key sentence spans two chunks, both chunks contain it
- Retrieval can find it regardless of which chunk is matched

### Embedding and Retrieval

```
Query: "What methodology was used?"
    |
    v
OpenAI text-embedding-3-small
    |
    v
Query Vector: [0.023, -0.156, 0.089, ...] (1536 dimensions)
    |
    v
FAISS similarity search (L2 distance)
    |
    v
Top-5 nearest chunk vectors returned with distances
    |
    v
Re-rank by relevance score (1 - distance)
    |
    v
Build context string from top chunks
```

---

## 10. Agentic Workflow Explained

### Why an Agent Instead of a Simple Chain?

A simple RAG chain always does the same thing: retrieve -> generate. But users ask different types of questions:

- "What does the paper say about X?" -> needs RAG
- "What's the latest research on Y?" -> needs web search
- "Give me a summary of all uploaded documents" -> needs summarization
- "Compare what paper A and paper B say" -> needs comparison

Our LangGraph agent **dynamically chooses the best strategy** based on the query.

### State Machine Flow

```
State = {query, request, strategy, response, context_score, error}

[1] CLASSIFY NODE
    - Check explicit user flags (use_web_search, compare_sources)
    - Run quick similarity search to gauge context quality
    - Keyword detection: "summarize", "compare", "vs", etc.
    - Set strategy: "rag" | "web" | "summarize" | "compare"

[2] ROUTING (conditional edges)
    strategy == "rag"       --> RAG_SEARCH node
    strategy == "web"       --> WEB_SEARCH node
    strategy == "summarize" --> SUMMARIZE node
    strategy == "compare"   --> COMPARE node

[3] STRATEGY NODE (one of four)
    - Executes the chosen strategy
    - Stores response in state

[4] GUARDRAILS NODE
    - Checks confidence threshold
    - Adds warnings if needed

[5] END
    - Returns final response
```

---

## 11. Evaluation Pipeline (RAGAS)

### What RAGAS Measures

| Metric | What It Checks | Score Range |
|--------|---------------|-------------|
| **Faithfulness** | Is every claim in the answer supported by the retrieved context? | 0.0 - 1.0 |
| **Answer Relevancy** | Does the answer actually address the question asked? | 0.0 - 1.0 |
| **Context Precision** | Are the retrieved documents relevant to the query? | 0.0 - 1.0 |
| **Context Recall** | Does the context contain all information needed? (requires ground truth) | 0.0 - 1.0 |

### How to Interpret Scores

- **> 0.8**: Excellent - production ready
- **0.6 - 0.8**: Good - may need prompt tuning or better chunking
- **0.4 - 0.6**: Fair - investigate retrieval quality and prompt design
- **< 0.4**: Poor - significant issues to debug

### Running Evaluation

**Via the UI:** Go to Evaluation tab, enter test queries, click "Run Evaluation"

**Via the API:**
```bash
curl -X POST http://localhost:8000/api/v1/evaluate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"queries": ["What are the findings?"], "ground_truths": ["The findings show..."]}'
```

**Via standalone script:**
```bash
cd smart-research-assistant
python evaluation/run_evaluation.py
```

---

## 12. Security & Guardrails

### Prompt Injection Protection

The system detects and blocks queries containing patterns like:
- "ignore all previous instructions"
- "you are now a different AI"
- "system prompt:"
- "override instructions"
- Excessive special characters (>40% ratio)

### Input Sanitization
- Null byte removal
- Length limiting to 2000 characters
- Whitespace trimming

### Confidence Thresholding
- LLM self-reports confidence (0.0-1.0) based on context quality
- Below threshold (default 0.6): answer gets a visible warning
- Users see red/yellow/green confidence bars

### Hallucination Control
- System prompt enforces strict grounding: "ONLY use information in the provided context"
- Citation requirement: every factual claim must cite [Source: title]
- Optional post-generation verification: second LLM call checks answer against context

---

## 13. Authentication System

### Flow

```
Register: username + email + password
    --> BCrypt hash password
    --> Store user in data/users.json
    --> Return user profile

Login: username + password
    --> Verify BCrypt hash
    --> Create JWT (24h expiry)
    --> Return access_token

Protected Request: Authorization: Bearer <token>
    --> Decode JWT
    --> Verify signature + expiry
    --> Load user from store
    --> Allow request to proceed
```

### JWT Token Structure
```json
{
  "sub": "username",
  "uid": "user_id_hash",
  "exp": 1717720000
}
```

### Password Security
- BCrypt hashing with automatic salt
- Passwords never stored in plain text
- Original password cannot be recovered from hash

---

## 14. Configuration Reference

All settings are in `backend/.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | openai | LLM provider: `openai` or `anthropic` |
| `OPENAI_API_KEY` | - | Your OpenAI API key (required if provider=openai) |
| `OPENAI_MODEL` | gpt-4o | OpenAI model for answer generation |
| `OPENAI_EMBEDDING_MODEL` | text-embedding-3-small | Model for text embeddings |
| `ANTHROPIC_API_KEY` | - | Your Anthropic key (required if provider=anthropic) |
| `ANTHROPIC_MODEL` | claude-sonnet-4-20250514 | Claude model for generation |
| `VECTOR_STORE_TYPE` | faiss | Vector DB: `faiss` (local) or `pinecone` (cloud) |
| `PINECONE_API_KEY` | - | Pinecone API key (if using pinecone) |
| `PINECONE_INDEX_NAME` | research-assistant | Pinecone index name |
| `FAISS_INDEX_PATH` | ./data/vectorstore/faiss_index | Local FAISS index path |
| `SERPAPI_KEY` | - | SerpAPI key for web search feature |
| `JWT_SECRET_KEY` | (default) | Secret for signing JWT tokens (change in production!) |
| `JWT_ALGORITHM` | HS256 | JWT signing algorithm |
| `JWT_EXPIRE_MINUTES` | 1440 | Token expiry in minutes (default: 24 hours) |
| `CHUNK_SIZE` | 1000 | Characters per text chunk |
| `CHUNK_OVERLAP` | 200 | Overlap between consecutive chunks |
| `TOP_K_RESULTS` | 5 | Default number of documents to retrieve |
| `CONFIDENCE_THRESHOLD` | 0.6 | Below this score, answers show warnings |
| `MAX_FILE_SIZE_MB` | 50 | Maximum upload file size |
| `LOG_LEVEL` | INFO | Logging verbosity: DEBUG, INFO, WARNING, ERROR |

---

## 15. Deployment Guide

### Option A: Local Development

See [Section 5](#5-how-to-run-the-application) for full local setup instructions.

### Option B: Docker

```bash
# Build and run
docker-compose up --build -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

Docker Compose runs:
- **backend** container: Python + FastAPI on port 8000
- **frontend** container: Nginx serving React build on port 80, proxying /api to backend

### Option C: Cloud Deployment

For production deployment:

1. **Backend**: Deploy to AWS ECS, Google Cloud Run, or Azure Container Apps
2. **Frontend**: Deploy to Vercel, Netlify, or serve via CDN
3. **Vector Store**: Switch to Pinecone (`VECTOR_STORE_TYPE=pinecone`)
4. **Secrets**: Use cloud secret managers instead of .env files
5. **Database**: Replace `users.json` with PostgreSQL for user storage
6. **HTTPS**: Add TLS termination via load balancer or reverse proxy

---

## 16. Example Input/Output

### Example 1: Standard RAG Query

**Upload:** A PDF about machine learning optimization techniques.

**Query:** "What optimization algorithms are discussed in the paper?"

**Response:**
```
The paper discusses several optimization algorithms:

1. **Stochastic Gradient Descent (SGD)** - The baseline optimizer used for
   comparison across all experiments [Source: ml_optimization.pdf].

2. **Adam (Adaptive Moment Estimation)** - Described as the most widely used
   optimizer, combining momentum and adaptive learning rates
   [Source: ml_optimization.pdf].

3. **AdaGrad** - Noted for its effectiveness with sparse gradients but
   criticized for its aggressive learning rate decay
   [Source: ml_optimization.pdf].

The authors conclude that Adam provides the best balance of convergence
speed and final accuracy for their benchmark tasks.

Confidence: 0.88 (High)
Strategy: RAG Search
Sources: 3 relevant chunks from ml_optimization.pdf
Tokens: 1,420
```

### Example 2: Web Search Supplementation

**Query:** "What are the latest developments in quantum computing?" (with web search enabled)

**Response:**
```
Based on available documents and web sources:

Recent developments in quantum computing include:

1. **Error correction breakthroughs** - Google's Willow chip demonstrated
   below-threshold quantum error correction [Source: google.com/quantum].

2. **Increased qubit counts** - IBM's latest processors exceeded 1,000
   qubits [Source: ibm.com/quantum].

Note: Web sources supplement the uploaded documents for this query.

Confidence: 0.72 (Medium)
Strategy: Web Search
Sources: 2 web results + 1 uploaded document
```

### Example 3: Low Confidence Warning

**Query:** "What is the GDP of France?" (no relevant documents uploaded)

**Response:**
```
**Low Confidence Warning** (score: 0.15): The following answer may not
be fully supported by the available sources. Please verify independently.

I don't have sufficient information in the provided documents to answer
this question about France's GDP. Please upload relevant economic
documents or enable web search for current data.

Confidence: 0.15 (Low)
Strategy: RAG Search
Sources: none
```

---

## 17. Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| `pip not found` | Python not in PATH | Reinstall Python, check "Add to PATH" |
| `OPENAI_API_KEY not set` | Missing .env configuration | Copy `.env.example` to `.env` and add your key |
| `Connection refused` on frontend | Backend not running | Start backend first: `uvicorn app.main:app --reload` |
| `401 Unauthorized` on API calls | JWT token missing/expired | Log out and log back in |
| `FAISS index not found` | No documents uploaded yet | Upload at least one PDF first |
| `Module not found` errors | Dependencies not installed | Run `pip install -r requirements.txt` |
| CORS errors in browser | Frontend URL not in allowed origins | Check CORS config in `main.py` |
| Slow responses | LLM API latency | Normal for GPT-4o; reduce top_k or switch to faster model |

### Getting Help

- **API Documentation**: http://localhost:8000/docs (auto-generated Swagger UI)
- **Backend Logs**: Check terminal where uvicorn is running
- **Frontend Errors**: Open browser DevTools (F12) -> Console tab
