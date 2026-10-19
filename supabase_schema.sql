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

create table if not exists public.answer_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  question text not null,
  answer text not null,
  rating integer not null check (rating between 1 and 5),
  sources jsonb not null default '[]'::jsonb,
  created_at timestamptz not null default now()
);
