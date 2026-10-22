-- Second Brain vector-search performance migration.
-- Run this manually in Supabase SQL Editor; the application never executes it.
--
-- The repository stores embeddings in public.document_chunks.embedding as
-- vector(768), and the retrieval RPC uses the cosine-distance operator (<=>).
-- HNSW with vector_cosine_ops therefore matches the query metric.

create index if not exists document_chunks_embedding_hnsw_idx
  on public.document_chunks
  using hnsw (embedding vector_cosine_ops);

-- The RPC filters by user_id before returning results. Keep that predicate
-- indexed as well; HNSW alone is not a replacement for this B-tree index.
create index if not exists document_chunks_user_id_idx
  on public.document_chunks (user_id);

-- Optional per-session tuning for benchmark queries. This is not persistent:
-- apply it in the same SQL session as EXPLAIN ANALYZE or the vector query.
set hnsw.ef_search = 40;

-- Benchmark the user-scoped retrieval RPC after replacing the placeholders:
--
-- explain (analyze, buffers, settings, verbose)
-- select *
-- from public.match_document_chunks_for_user(
--   query_embedding => '[...]'::vector,
--   match_threshold => 0.30,
--   match_count => 8,
--   requesting_user_id => 'YOUR_SUPABASE_AUTH_USER_UUID'
-- );
