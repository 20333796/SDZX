"""create resource catalog and click event tables

Revision ID: 20260917_01
Revises:
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260917_01"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    inspector = inspect(op.get_bind())
    if not inspector.has_table("external_resources"):
        op.create_table(
            "external_resources",
            sa.Column("id", sa.String(length=120), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("provider", sa.String(length=255), nullable=False),
            sa.Column("category", sa.String(length=32), nullable=False),
            sa.Column("course_level", sa.String(length=32), nullable=False),
            sa.Column("audience", sa.String(length=255), nullable=False),
            sa.Column("credits", sa.Float(), nullable=True),
            sa.Column("language", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("url", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
    if not any(index["name"] == "ix_external_resources_category" for index in inspector.get_indexes("external_resources")):
        op.create_index("ix_external_resources_category", "external_resources", ["category"])
    if not inspector.has_table("resource_click_events"):
        op.create_table(
            "resource_click_events",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("resource_id", sa.String(length=120), nullable=False),
            sa.Column("source", sa.String(length=80), nullable=False),
            sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["resource_id"], ["external_resources.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
    if not any(index["name"] == "ix_resource_click_events_resource_id" for index in inspector.get_indexes("resource_click_events")):
        op.create_index("ix_resource_click_events_resource_id", "resource_click_events", ["resource_id"])


def downgrade() -> None:
    op.drop_index("ix_resource_click_events_resource_id", table_name="resource_click_events")
    op.drop_table("resource_click_events")
    op.drop_index("ix_external_resources_category", table_name="external_resources")
    op.drop_table("external_resources")
