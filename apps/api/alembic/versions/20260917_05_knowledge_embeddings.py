"""add knowledge chunk embeddings

Revision ID: 20260917_05
Revises: 20260917_04
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260917_05"
down_revision: Union[str, None] = "20260917_04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("knowledge_chunks")}
    if "embedding" not in columns:
        op.add_column("knowledge_chunks", sa.Column("embedding", sa.Text(), nullable=True))
    if "embedding_model" not in columns:
        op.add_column("knowledge_chunks", sa.Column("embedding_model", sa.String(length=120), nullable=True))


def downgrade() -> None:
    op.drop_column("knowledge_chunks", "embedding_model")
    op.drop_column("knowledge_chunks", "embedding")
