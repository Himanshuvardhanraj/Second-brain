"""Add safe indexes for existing ownership and foreign-key lookup paths."""
from typing import Sequence, Union

from alembic import op

revision: str = "20261027_0002"
down_revision: Union[str, Sequence[str], None] = "20261027_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # CONCURRENTLY keeps production reads and writes available. It must not
    # execute inside Alembic's normal transaction.
    with op.get_context().autocommit_block():
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
            "document_chunks_document_id_idx "
            "ON public.document_chunks (document_id)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
            "documents_user_id_idx "
            "ON public.documents (user_id)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
            "document_chunks_user_id_idx "
            "ON public.document_chunks (user_id)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
            "answer_feedback_user_id_idx "
            "ON public.answer_feedback (user_id)"
        )
        op.execute(
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS "
            "answer_feedback_note_id_idx "
            "ON public.answer_feedback (note_id)"
        )


def downgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.document_chunks_document_id_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.documents_user_id_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.document_chunks_user_id_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.answer_feedback_user_id_idx")
        op.execute("DROP INDEX CONCURRENTLY IF EXISTS public.answer_feedback_note_id_idx")
