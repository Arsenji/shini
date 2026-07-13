"""add customer_name to orders

Revision ID: 002
Revises: 001
Create Date: 2026-07-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "orders" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("orders")}
    if "customer_name" in columns:
        return

    op.add_column("orders", sa.Column("customer_name", sa.String(length=64), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "orders" not in inspector.get_table_names():
        return

    columns = {col["name"] for col in inspector.get_columns("orders")}
    if "customer_name" not in columns:
        return

    op.drop_column("orders", "customer_name")

