-- Run once in Supabase SQL Editor for the current Supabase Auth flow.
alter table public.documents drop constraint if exists documents_user_id_fkey;
alter table public.document_chunks drop constraint if exists document_chunks_user_id_fkey;
alter table public.documents alter column user_id set not null;
alter table public.document_chunks alter column user_id set not null;
