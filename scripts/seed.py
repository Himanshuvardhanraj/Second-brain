"""Insert deterministic demo documents and chunks into the existing schema.

Seed files use fake `seed/` paths; the corresponding Storage objects do not
exist, so downloading or previewing a seeded original file will not work.
Fake embeddings are unit-length vectors for schema compatibility only and
produce meaningless similarity results. Use --real-embeddings sparingly.
"""
from __future__ import annotations

import argparse
import hashlib
import math
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from faker import Faker
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[1]
SEED_USER = "seed-demo-user"
SEED = 20261027
TAGS = ["dsa", "backend", "ml", "career", "system-design", "notes", "productivity", "databases"]
TOPICS = {
    "dsa": "Algorithms and data structures help engineers choose efficient ways to represent data and solve problems. Arrays offer constant-time indexed access, while linked lists trade that convenience for flexible insertion. Hash tables provide expected constant-time lookup when the hash function distributes keys well. Trees and graphs model hierarchical and network relationships. When evaluating an approach, compare time complexity, memory use, input constraints, and whether stable ordering matters.",
    "backend": "A reliable backend separates transport, application, and persistence responsibilities. Validate input at the boundary, authorize every resource access on the server, and return errors that help clients recover without exposing secrets. Idempotency is valuable for retries, while structured logs and health checks make production behavior observable. Database transactions should cover related state changes, and slow work should be measured before it is moved to a queue.",
    "ml": "Machine learning systems depend on data quality, evaluation design, and careful deployment. A training metric can look strong while failing on real user distributions, so hold out representative validation data and inspect errors by segment. Embeddings represent semantic relationships in a continuous vector space. Retrieval-augmented generation combines search with a language model, but still needs access control, source grounding, latency budgets, and tests for unsupported answers.",
    "career": "A strong engineering portfolio explains the user problem, constraints, decisions, and outcome rather than listing technologies. Show how you investigated uncertainty, collaborated with others, tested assumptions, and handled failure. During an interview, clarify ambiguous requirements, communicate trade-offs, and connect implementation details to measurable value. Small projects become compelling when they demonstrate ownership from design through deployment and maintenance.",
    "system-design": "System design starts with requirements and traffic assumptions before choosing components. Define consistency, availability, latency, retention, and failure expectations. Stateless services can scale horizontally, while durable state belongs in a database or object store. Caches reduce repeated work but require invalidation and a clear freshness policy. Observability, retries with limits, idempotency, and graceful degradation are part of the design, not afterthoughts.",
    "notes": "Useful notes preserve enough context to be actionable later. A good note has a descriptive title, a short summary, links to supporting evidence, and a next action when appropriate. Search and tags support retrieval, but consistent naming and concise writing improve both. Periodically review old notes, merge duplicates, and mark uncertain claims so that future decisions do not rely on unverified memory.",
    "productivity": "Productivity systems work best when they reduce the effort required to decide what to do next. Capture tasks quickly, clarify the desired outcome, and choose a small next action. Review commitments regularly instead of trusting an ever-growing list. Protect focused time, batch shallow work, and leave recovery space. A system should adapt to real constraints rather than turning organization itself into another source of work.",
    "databases": "Relational databases provide structured data, constraints, transactions, and expressive queries. Indexes accelerate common predicates but add write and storage cost, so create them from measured access patterns. Foreign keys protect relationships when existing data satisfies the constraint. Migrations should be explicit and reversible where practical. On production systems, inspect query plans, take backups, and prefer online techniques such as concurrent index creation for large tables.",
}
FILENAMES = [
    "system-design-notes.pdf", "backend-api-patterns.md", "machine-learning-review.txt",
    "data-structures-cheatsheet.pdf", "career-interview-notes.md", "postgresql-guide.pdf",
    "productivity-weekly-review.txt", "rag-architecture-notes.md", "python-testing.pdf",
    "distributed-systems-summary.md",
]


def embedding(seed: int, real: bool = False, client=None) -> list[float]:
    if real:
        from google.genai import types

        result = client.models.embed_content(
            model=os.environ["GEMINI_EMBEDDING_MODEL"],
            contents=f"Seed demo topic {seed}: {TOPICS[TAGS[seed % len(TAGS)]]}",
            config=types.EmbedContentConfig(output_dimensionality=768),
        )
        values = list(result.embeddings[0].values)
        norm = math.sqrt(sum(value * value for value in values))
        return [value / norm for value in values]
    rng = random.Random(SEED + seed)
    values = [rng.uniform(-1, 1) for _ in range(768)]
    norm = math.sqrt(sum(value * value for value in values))
    return [value / norm for value in values]


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def confirmation(prompt: str) -> None:
    if input(f"{prompt} Type 'yes' to continue: ").strip().lower() != "yes":
        raise SystemExit("Aborted.")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Delete only seed-demo-user rows first")
    parser.add_argument("--real-embeddings", action="store_true", help="Use Gemini embeddings instead of deterministic fake vectors")
    args = parser.parse_args()
    if os.environ.get("SEED_ALLOWED", "").lower() != "true":
        raise SystemExit("Refusing to seed: set SEED_ALLOWED=true explicitly.")
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise SystemExit("DATABASE_URL is required.")
    host = os.environ.get("PGHOST") or database_url.split("@")[-1].split("/")[0]
    print(f"Database host: {host}")
    confirmation("This writes to the existing database; a development database is strongly recommended.")
    engine = create_engine(database_url, pool_pre_ping=True)
    faker = Faker()
    faker.seed_instance(SEED)
    client = None
    if args.real_embeddings:
        from google import genai
        client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
    now = datetime.now(timezone.utc)
    if args.reset:
        confirmation("Delete only seed-demo-user chunks and documents?")
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM public.document_chunks WHERE user_id = :user_id"), {"user_id": SEED_USER})
            conn.execute(text("DELETE FROM public.documents WHERE user_id = :user_id"), {"user_id": SEED_USER})
    for batch_start in range(0, 50, 10):
        with engine.begin() as conn:
            existing = {
                row.filename for row in conn.execute(
                    text("SELECT filename FROM public.documents WHERE user_id = :user_id"),
                    {"user_id": SEED_USER},
                )
            }
            for index in range(batch_start, batch_start + 10):
                base_name = FILENAMES[index % len(FILENAMES)]
                stem, extension = base_name.rsplit(".", 1)
                filename = f"{stem}-{index + 1:02d}.{extension}"
                if filename in existing:
                    continue
                tag = TAGS[index % len(TAGS)]
                created = now - timedelta(days=(index * 3) % 181, hours=index % 24)
                result = conn.execute(
                    text("""INSERT INTO public.documents
                        (filename, file_path, file_type, file_size, tag, created_at, user_id)
                        VALUES (:filename, :file_path, :file_type, :file_size, :tag, :created_at, :user_id)
                        RETURNING id"""),
                    {"filename": filename, "file_path": f"seed/{hashlib.sha256(filename.encode()).hexdigest()}.{extension}",
                     "file_type": extension, "file_size": faker.random_int(20_000, 900_000),
                     "tag": tag, "created_at": created, "user_id": SEED_USER},
                )
                document_id = result.scalar_one()
                chunk_count = 3 + (index % 4)
                for chunk_index in range(chunk_count):
                    content = TOPICS[tag] + f" Example {chunk_index + 1}: apply this principle to a practical {tag} project and verify the result with a small test."
                    words = content.split()
                    content = " ".join((words * ((100 // len(words)) + 1))[: min(200, 100 + (chunk_index % 3) * 20)])
                    conn.execute(
                        text("""INSERT INTO public.document_chunks
                            (document_id, chunk_index, content, page_number, metadata, created_at, embedding, user_id)
                            VALUES (:document_id, :chunk_index, :content, :page_number, CAST(:metadata AS jsonb),
                                    :created_at, CAST(:embedding AS vector), :user_id)"""),
                        {"document_id": document_id, "chunk_index": chunk_index, "content": content,
                         "page_number": chunk_index + 1, "metadata": '{"seed": true, "source": "demo"}',
                         "created_at": created, "embedding": vector_literal(embedding(index * 10 + chunk_index, args.real_embeddings, client)),
                         "user_id": SEED_USER},
                    )
                existing.add(filename)
        print(f"Committed batch through {batch_start + 10}/50 documents")
    print("Seed complete. Existing matching marker/filename rows were skipped.")


if __name__ == "__main__":
    main()
