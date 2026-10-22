create extension if not exists pgcrypto;

insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do update set public = false;

create table if not exists public.users (
  id text primary key,
  email text unique,
  username text unique,
  name text not null,
  avatar_url text,
  password_hash text,
  provider text not null default 'password',
  updated_at timestamptz not null default now()
);

alter table public.users add column if not exists username text unique;
alter table public.users add column if not exists password_hash text;

alter table public.documents add column if not exists user_id text;
alter table public.document_chunks add column if not exists user_id text;

-- Ownership is keyed by Supabase Auth's user UUID. Do not require a row in
-- the legacy public.users profile table for uploads or retrieval.
alter table public.documents drop constraint if exists documents_user_id_fkey;
alter table public.document_chunks drop constraint if exists document_chunks_user_id_fkey;

create table if not exists public.notes (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  question text not null,
  answer text not null,
  sources jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists notes_user_created_idx
  on public.notes (user_id, created_at desc);

delete from public.notes duplicate
using public.notes keeper
where duplicate.id > keeper.id
  and duplicate.user_id = keeper.user_id
  and duplicate.question = keeper.question
  and duplicate.answer = keeper.answer;

-- Prevent future duplicate wishlist entries.
create unique index if not exists notes_user_question_answer_uidx
  on public.notes (user_id, question, answer);

create table if not exists public.answer_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  question text not null,
  answer text not null,
  rating integer not null check (rating between 1 and 5),
  sources jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);

create or replace function public.match_document_chunks_for_user(
  query_embedding vector(768),
  match_threshold float,
  match_count int,
  requesting_user_id text
)
returns table (
  document_id uuid,
  content text,
  page_number integer,
  metadata jsonb,
  similarity float,
  filename text
)
language sql stable
as $$
  select
    dc.document_id,
    dc.content,
    dc.page_number,
    dc.metadata,
    1 - (dc.embedding <=> query_embedding) as similarity,
    d.filename
  from public.document_chunks dc
  join public.documents d on d.id = dc.document_id
  where dc.user_id = requesting_user_id
    and 1 - (dc.embedding <=> query_embedding) >= match_threshold
  order by dc.embedding <=> query_embedding
  limit match_count;
$$;
