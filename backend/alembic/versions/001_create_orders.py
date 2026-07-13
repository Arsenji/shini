"""create orders table

Revision ID: 001
Revises:
Create Date: 2026-07-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    order_status = sa.Enum("NEW", "IN_PROGRESS", "DONE", "CANCELED", name="order_status")
    order_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("profile", sa.Integer(), nullable=False),
        sa.Column("radius", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("status", order_status, nullable=False),
        sa.Column("manager_name", sa.String(length=255), nullable=True),
        sa.Column("manager_vk_id", sa.BigInteger(), nullable=True),
        sa.Column("vk_message_id", sa.Integer(), nullable=True),
        sa.Column("vk_peer_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("orders")
    sa.Enum(name="order_status").drop(op.get_bind(), checkfirst=True)
