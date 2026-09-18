"""add geo datasets catalog

Revision ID: 20260918_07
Revises: 20260917_06
Create Date: 2026-09-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260918_07"
down_revision: Union[str, None] = "20260917_06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Dev/test 环境由 lifespan 的 create_all 先建了同名表，这里保持幂等。
    bind = op.get_bind()
    if "geo_datasets" in inspect(bind).get_table_names():
        return
    op.create_table(
        "geo_datasets",
        sa.Column("id", sa.String(length=120), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False, index=True),
        sa.Column("region", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("data_format", sa.String(length=80), nullable=False),
        sa.Column("resolution", sa.String(length=80), nullable=False),
        sa.Column("size_label", sa.String(length=80), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("license", sa.String(length=120), nullable=False),
        sa.Column("access_url", sa.Text(), nullable=True),
        sa.Column("features_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("geo_datasets")
