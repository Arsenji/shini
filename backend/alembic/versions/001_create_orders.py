"""create orders table

Revision ID: 001
Revises:
Create Date: 2026-07-13
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ORDER_STATUS = postgresql.ENUM(
    "NEW",
    "IN_PROGRESS",
    "DONE",
    "CANCELED",
    name="order_status",
    create_type=False,
)


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE order_status AS ENUM ('NEW', 'IN_PROGRESS', 'DONE', 'CANCELED');
        EXCEPTION
            WHEN duplicate_object THEN NULL;
        END $$;
        """
    )

    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "orders" in inspector.get_table_names():
        return

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("profile", sa.Integer(), nullable=False),
        sa.Column("radius", sa.Integer(), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            ORDER_STATUS,
            nullable=False,
            server_default="NEW",
        ),
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
    op.execute("DROP TYPE IF EXISTS order_status")
