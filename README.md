# 🧠 Second Brain
 An AI-powered personal knowledge assistant that uses Retrieval-Augmented Generation (RAG) to turn your documents and notes into a searchable, conversational knowledge base.

Second Brain allows users to upload documents, process their contents into semantic embeddings, store them in a vector database, and ask natural-language questions over their personal knowledge.

Instead of relying only on an LLM's pre-trained knowledge, Second Brain retrieves relevant information from the user's own documents and provides it as context to the LLM before generating an answer.

---

## 🚀 Live Project

### Frontend
https://second-brain-frontend-beige.vercel.app

### Backend API
https://second-brain-virid-eta.vercel.app

### GitHub
https://github.com/Himanshuvardhanraj/Second-brain

---

# ✨ Features

- 📄 Upload PDF documents
- 🧩 Automatic document parsing and chunking
- 🔢 Semantic embeddings
- 🔍 Vector similarity search
- 🧠 Retrieval-Augmented Generation (RAG)
- 💬 Natural-language question answering
- 📚 Source-aware responses
- 📑 Page-level source references
- ⚡ FastAPI backend
- ⚛️ React + Vite frontend
- 🗄️ PostgreSQL database
- 🔎 PostgreSQL + pgvector semantic search
- ☁️ Supabase storage and database
- 🤖 Gemini LLM integration
- 🔐 Environment-based secret management
- 🚀 Vercel deployment

---

# 🏗️ Architecture
                        ┌─────────────────────┐
                        │       User          │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │   React + Vite      │
                        │     Frontend        │
                        └──────────┬──────────┘
                                   │
                                   ▼
                        ┌─────────────────────┐
                        │    FastAPI API      │
                        └──────────┬──────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
          ┌─────────────────┐          ┌─────────────────┐
          │ Document        │          │ User Query      │
          │ Ingestion       │          │                 │
          └────────┬────────┘          └────────┬────────┘
                   │                            │
                   ▼                            ▼
          ┌─────────────────┐          ┌─────────────────┐
          │ PDF Extraction  │          │ Query Embedding │
          │ + Chunking      │          └────────┬────────┘
          └────────┬────────┘                   │
                   │                            ▼
                   ▼                   ┌─────────────────┐
          ┌─────────────────┐           │ Vector Search   │
          │ Gemini          │           │   pgvector      │
          │ Embeddings      │           └────────┬────────┘
          └────────┬────────┘                    │
                   │                             ▼
                   ▼                    ┌─────────────────┐
          ┌─────────────────┐           │ Relevant        │
          │ Supabase        │           │ Context         │
          │ PostgreSQL      │           └────────┬────────┘
          │ + pgvector      │                    │
          └─────────────────┘                    ▼
                                        ┌─────────────────┐
                                        │ Gemini LLM      │
                                        │ Generation      │
                                        └────────┬────────┘
                                                 │
                                                 ▼
                                        ┌─────────────────┐
                                        │ Final Answer    │
                                        │ + Sources       │
                                        └─────────────────┘
🛠️ Tech Stack :-

Frontend :

React
Vite
JavaScript
HTML
CSS

Backend :

Python
FastAPI
Uvicorn

AI / GenAI :

Gemini API
Gemini Embeddings
Retrieval-Augmented Generation (RAG)
Prompt Engineering
Structured context generation

Vector Search :

PostgreSQL
pgvector
HNSW vector index
Cosine similarity search

Database & Storage :

Supabase
PostgreSQL
Supabase Storage
pgvector

Document Processing :

PyPDF
PDF text extraction
Document chunking

Development :

Git
GitHub
VS Code
Python virtual environments
Environment variables

Deployment :

Vercel
Vercel serverless backend
Supabase

📊 RAG Quality Considerations

While building Second Brain, several RAG engineering problems were explored:

Retrieval quality
Similarity thresholds
Top-K retrieval
Compound questions
Chunking strategies
Embedding quality
Context quality
Hallucination prevention
Retrieval latency
Token usage
Cost optimization
Caching
RAG evaluation

One important lesson was that a fixed similarity cutoff can sometimes remove useful chunks, particularly for questions containing multiple concepts.

This led to focusing more heavily on retrieval quality and query handling rather than treating the similarity threshold as a universal constant.

🔮 Future Roadmap
Phase 1 — Core RAG ✅
 ✅ PDF upload
 ✅ PDF text extraction
 ✅ Document chunking
 ✅ Embeddings
 ✅ Vector database
 ✅ Semantic search
 ✅ RAG pipeline
 ✅ LLM generation
 ✅ Source references
 ✅ React frontend
 ✅ FastAPI backend
 ✅ Supabase integration
 ✅ Vercel deployment

Phase 2 — Advanced Retrieval 🚧

 Semantic chunking
 Hybrid search
 BM25 + vector search
 Query rewriting
 Query decomposition
 HyDE
 RAG Fusion
 Advanced retrievers
 Reranking
 Metadata filtering
 Better handling of compound questions

Phase 3 — RAG Evaluation 📊

 RAGAS integration
 Retrieval evaluation dataset
 Answer evaluation
 Faithfulness evaluation
 Context relevance evaluation
 Automated regression testing
 User feedback loop

Phase 4 — Observability & Optimization ⚡

 Request tracing
 Retrieval latency tracking
 LLM latency tracking
 Token usage tracking
 Cost monitoring
 RAG signals
 Retrieval score monitoring
 Query caching
 Semantic caching
 Performance dashboards

Phase 5 — AI Safety & Guardrails 🛡️

 Prompt injection detection
 Jailbreak detection
 Input validation
 Output validation
 Malicious document detection
 PII detection
 Content filtering
 Retrieval security

🔐 Security Roadmap

Security improvements planned for production:

 User authentication
 Authorization
 Row-level security
 Per-user document isolation
 Secure file uploads
 File type validation
 File size limits
 Rate limiting
 API authentication
 Prompt injection protection
 Secret rotation
 Audit logging

☁️ Production Architecture

The long-term production architecture is planned around:

                    ┌───────────────┐
                    │    React      │
                    │   Frontend    │
                    └───────┬───────┘
                            │
                            ▼
                    ┌───────────────┐
                    │    FastAPI    │
                    │      API      │
                    └───────┬───────┘
                            │
             ┌──────────────┼──────────────┐
             │              │              │
             ▼              ▼              ▼
       ┌──────────┐   ┌───────────┐   ┌──────────┐
       │ Supabase │   │  Gemini   │   │  Cache   │
       │ Postgres │   │    API    │   │          │
       │ pgvector │   │           │   │          │
       └──────────┘   └───────────┘   └──────────┘

As the system grows, additional infrastructure such as background workers, queues, observability systems, and dedicated vector/search infrastructure may be introduced


🧑‍💻 Running Locally

Clone the repository

git clone https://github.com/Himanshuvardhanraj/Second-brain.git
cd Second-brain

Backend
Create a virtual environment:

python -m venv .venv

Activate it:

macOS / Linux
source .venv/bin/activate

Windows
.venv\Scripts\activate

Install dependencies:

pip install -r requirements.txt

Create .env:

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite

GEMINI_EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768

SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_supabase_secret_key

FRONTEND_URL=http://localhost:5173

Run the API:

PYTHONPATH=src python -m uvicorn second_brain.api:app --reload

API:
http://localhost:8000

Swagger documentation:
http://localhost:8000/docs


👨‍💻 Author

Himanshu Raj

B.Tech Student | Full-Stack Developer | AI / GenAI Engineer

Interested in:

Full-Stack Development
AI Engineering
Generative AI
RAG Systems
LLM Applications
Backend Engineering
Distributed & Production Systems


⭐ If you find this project interesting

Feel free to explore the repository, experiment with the architecture, and provide feedback.

Built to learn.
Built to experiment.
Built to understand how production AI systems work.
