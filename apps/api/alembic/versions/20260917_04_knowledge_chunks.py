"""add parsed knowledge chunks

Revision ID: 20260917_04
Revises: 20260917_03
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260917_04"
down_revision: Union[str, None] = "20260917_03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    document_columns = {column["name"] for column in inspector.get_columns("knowledge_documents")}
    if "parsing_attempts" not in document_columns:
        op.add_column("knowledge_documents", sa.Column("parsing_attempts", sa.Integer(), nullable=False, server_default="0"))
    if "processing_error" not in document_columns:
        op.add_column("knowledge_documents", sa.Column("processing_error", sa.Text(), nullable=True))
    if "parsed_at" not in document_columns:
        op.add_column("knowledge_documents", sa.Column("parsed_at", sa.DateTime(timezone=True), nullable=True))
    if inspector.has_table("knowledge_chunks"):
        return
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("document_id", sa.String(length=36), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("source_locator", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_chunks_document_id", "knowledge_chunks", ["document_id"])
    op.create_index("ix_knowledge_chunks_content_hash", "knowledge_chunks", ["content_hash"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunks_content_hash", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_document_id", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
    op.drop_column("knowledge_documents", "parsed_at")
    op.drop_column("knowledge_documents", "processing_error")
    op.drop_column("knowledge_documents", "parsing_attempts")
