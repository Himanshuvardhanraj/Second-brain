-- Destructive cleanup: preserves Supabase Auth accounts only.
delete from public.document_chunks;
delete from public.documents;
delete from public.notes;
delete from public.answer_feedback;
