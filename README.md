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

GEMINI_API_KEY=your_rotated_gemini_api_key
GEMINI_MODEL=gemini-3.5-flash-lite

GEMINI_EMBEDDING_MODEL=gemini-embedding-2
EMBEDDING_DIMENSION=768

SUPABASE_URL=your_supabase_url
SUPABASE_SECRET_KEY=your_rotated_supabase_secret_key

FRONTEND_URL=http://localhost:5173
JWT_SECRET_KEY=replace_with_a_long_random_secret
APP_TOKEN_TTL_SECONDS=900
MAX_IN_MEMORY_SESSIONS=5000

Run the API:

PYTHONPATH=src python -m uvicorn second_brain.api:app --reload

API:
http://localhost:8000

Swagger documentation:
http://localhost:8000/docs

### Authentication and notes setup

Run `supabase_schema.sql` in the Supabase SQL editor before using account login
or the Notes feature. Registered accounts are created and authenticated by
Supabase Auth using email/password; the application never stores passwords.
After Supabase validates the credentials, the frontend uses the signed
Supabase access JWT for API requests. FastAPI validates that token through
Supabase Auth, so authorization works across Vercel serverless instances.
Supabase refresh tokens are used only by the backend refresh endpoint to issue
a new access token and are delivered as an HttpOnly cookie. The frontend
stores only the access token, never a refresh token or the Supabase service
key. Guest sessions use a separate application JWT and bounded in-memory TTL
registry.

The guest registry is intentionally dependency-free and local to one running
process; guest sessions can be lost when a serverless instance is recycled.
Registered-user sessions are managed by Supabase Auth and remain valid across
instances. Enable Supabase email confirmation
if required by your project; users must confirm before a session is returned.
The frontend starts at a login screen; “Skip for now” creates a signed guest
session. Guest sessions do not create a Supabase Auth user. Chat requests are
rejected without a valid access token.

The same SQL file also creates `answer_feedback`. Run the complete file again
after pulling updates so the five-star answer rating control can save feedback.

For correct per-user retrieval, run the complete SQL file after this update.
It adds user ownership to documents/chunks and creates
`match_document_chunks_for_user`. Until that migration is applied, the backend
keeps a legacy fallback so existing installations continue to work, but old
unowned chunks may still appear in retrieval results. Re-upload documents after
the migration to associate them with the account that uploaded them.

For faster vector retrieval as the chunk count grows, run
`supabase_hnsw_migration.sql` manually in Supabase SQL Editor. It creates an
HNSW cosine index on `document_chunks.embedding` and a B-tree index on
`document_chunks.user_id`; it is not run by the application. `SET
hnsw.ef_search = 40` is session-scoped, so use it in the same SQL session as
benchmarks or configure it separately at the database/role level if desired.

Chat answers are streamed through `POST /api/chat/stream` as server-sent
events. The existing `POST /api/chat` JSON endpoint remains available for
clients that do not support streaming.

### RBAC and search logging

Registered-user roles are read only from Supabase Auth `app_metadata`; the
client cannot select or change a role. Promote an account manually with:

```bash
SUPABASE_URL=... SUPABASE_SECRET_KEY=... MY_SUPABASE_USER_ID=... python promote_admin.py
```

Run `supabase_rbac_migration.sql` manually in Supabase SQL Editor before using
the admin console. It creates RLS-protected `search_logs` and append-only
`admin_audit_log` tables. Search queries are retained for
`SEARCH_LOG_RETENTION_DAYS` (default 30); schedule the documented cleanup SQL
with Supabase pg_cron or a scheduled function.

The admin deletion path hard-deletes the Supabase Auth account, profile,
documents, chunks/embeddings, Storage files, Notes, feedback, and search logs.
It requires typing the target email, blocks self-deletion and last-admin
deletion, and requires an explicit confirmation when deleting another admin.
Database and Storage operations cannot share one Postgres transaction, so the
backend performs them in an idempotent ordered sequence and audits failures.

For Vercel, deploy the `frontend` directory as the frontend project and set
`VITE_API_URL` to the deployed backend URL, for example
`https://second-brain-virid-eta.vercel.app`. Set `FRONTEND_URL` on the backend
to the Vercel frontend URL (plus `http://localhost:5173` when developing
locally). Vercel environment variables must be configured separately for
Preview and Production deployments, and a new deployment is required after
changing them.

Never paste secret values into source files, GitHub issues, pull requests, or
frontend `VITE_*` variables. Rotate any key that has been exposed, then store
the replacement only in local `.env` files or Vercel's encrypted backend
environment variables. The frontend must never receive `GEMINI_API_KEY` or
`SUPABASE_SECRET_KEY`.


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
