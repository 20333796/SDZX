"""add external resource cover asset

Revision ID: 20260917_03
Revises: 20260917_02
Create Date: 2026-09-17
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision: str = "20260917_03"
down_revision: Union[str, None] = "20260917_02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    columns = {column["name"] for column in inspect(op.get_bind()).get_columns("external_resources")}
    if "cover_asset" not in columns:
        op.add_column("external_resources", sa.Column("cover_asset", sa.String(length=512), nullable=True))


def downgrade() -> None:
    op.drop_column("external_resources", "cover_asset")
