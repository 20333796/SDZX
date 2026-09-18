"""create knowledge document catalog

Revision ID: 20260917_02
Revises: 20260917_01
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260917_02"
down_revision: Union[str, None] = "20260917_01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if not inspector.has_table("knowledge_documents"):
        op.create_table(
            "knowledge_documents",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("document_type", sa.String(length=80), nullable=False),
            sa.Column("course_name", sa.String(length=255), nullable=True),
            sa.Column("original_filename", sa.String(length=255), nullable=False),
            sa.Column("content_type", sa.String(length=120), nullable=False),
            sa.Column("object_key", sa.String(length=512), nullable=False),
            sa.Column("checksum", sa.String(length=64), nullable=False),
            sa.Column("byte_size", sa.Integer(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("version", sa.Integer(), nullable=False),
            sa.Column("created_by", sa.String(length=255), nullable=False),
            sa.Column("reviewed_by", sa.String(length=255), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("object_key"),
        )
    index_names = {index["name"] for index in inspector.get_indexes("knowledge_documents")}
    if "ix_knowledge_documents_checksum" not in index_names:
        op.create_index("ix_knowledge_documents_checksum", "knowledge_documents", ["checksum"])
    if "ix_knowledge_documents_document_type" not in index_names:
        op.create_index("ix_knowledge_documents_document_type", "knowledge_documents", ["document_type"])
    if "ix_knowledge_documents_status" not in index_names:
        op.create_index("ix_knowledge_documents_status", "knowledge_documents", ["status"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_documents_status", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_document_type", table_name="knowledge_documents")
    op.drop_index("ix_knowledge_documents_checksum", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
