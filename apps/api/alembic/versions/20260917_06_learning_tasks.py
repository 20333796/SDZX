"""add learning tasks and submissions

Revision ID: 20260917_06
Revises: 20260917_05
Create Date: 2026-09-17
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision: str = "20260917_06"
down_revision: Union[str, None] = "20260917_05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if not inspector.has_table("learning_tasks"):
        op.create_table(
            "learning_tasks",
            sa.Column("id", sa.String(length=120), nullable=False),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("course_name", sa.String(length=255), nullable=False),
            sa.Column("objective", sa.Text(), nullable=False),
            sa.Column("instructions_json", sa.Text(), nullable=False),
            sa.Column("estimated_minutes", sa.Integer(), nullable=False),
            sa.Column("difficulty", sa.String(length=32), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_by", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_learning_tasks_course_name", "learning_tasks", ["course_name"])
        op.create_index("ix_learning_tasks_status", "learning_tasks", ["status"])
    if not inspector.has_table("learning_submissions"):
        op.create_table(
            "learning_submissions",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("task_id", sa.String(length=120), nullable=False),
            sa.Column("learner_id", sa.String(length=255), nullable=False),
            sa.Column("response", sa.Text(), nullable=False),
            sa.Column("evidence", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False),
            sa.Column("score", sa.Float(), nullable=True),
            sa.Column("feedback", sa.Text(), nullable=True),
            sa.Column("feedback_by", sa.String(length=255), nullable=True),
            sa.Column("feedback_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
            sa.ForeignKeyConstraint(["task_id"], ["learning_tasks.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_learning_submissions_task_id", "learning_submissions", ["task_id"])
        op.create_index("ix_learning_submissions_learner_id", "learning_submissions", ["learner_id"])
        op.create_index("ix_learning_submissions_status", "learning_submissions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_learning_submissions_status", table_name="learning_submissions")
    op.drop_index("ix_learning_submissions_learner_id", table_name="learning_submissions")
    op.drop_index("ix_learning_submissions_task_id", table_name="learning_submissions")
    op.drop_table("learning_submissions")
    op.drop_index("ix_learning_tasks_status", table_name="learning_tasks")
    op.drop_index("ix_learning_tasks_course_name", table_name="learning_tasks")
    op.drop_table("learning_tasks")
