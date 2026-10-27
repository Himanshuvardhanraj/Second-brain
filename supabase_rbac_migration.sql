-- RBAC, search logging, and append-only admin audit migration.
create table if not exists public.search_logs (
  id uuid primary key default gen_random_uuid(),
  user_id text,
  query_text text not null,
  result_count integer,
  latency_ms integer,
  created_at timestamptz not null default now()
);

create index if not exists search_logs_created_idx
  on public.search_logs (created_at desc);
create index if not exists search_logs_user_created_idx
  on public.search_logs (user_id, created_at desc);

alter table public.search_logs enable row level security;
revoke all on public.search_logs from anon, authenticated;

create table if not exists public.admin_audit_log (
  id uuid primary key default gen_random_uuid(),
  admin_id text not null,
  action text not null,
  target_user_id text,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists admin_audit_created_idx
  on public.admin_audit_log (created_at desc);
alter table public.admin_audit_log enable row level security;
revoke all on public.admin_audit_log from anon, authenticated;

-- Retention: run this daily using Supabase Scheduled Functions or pg_cron.
-- Keep the interval configurable through SEARCH_LOG_RETENTION_DAYS in the API.
-- delete from public.search_logs
-- where created_at < now() - interval '30 days';
