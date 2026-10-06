"""initial

Revision ID: 001_initial
Revises:
Create Date: 2026-10-06
"""

import sqlalchemy as sa

from alembic import op

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Применяет начальную миграцию."""

    op.create_table(
        "tariffs",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "title",
            sa.String(length=50),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "price",
            sa.Integer(),
            nullable=False,
        ),
    )

    op.create_table(
        "payments",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
        ),
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "tariff_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "amount",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "discount",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "method",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "installment_months",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "schedule",
            sa.JSON(),
            nullable=True,
        ),
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "idempotency_key",
            sa.String(length=255),
            nullable=True,
            unique=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tariff_id"],
            ["tariffs.id"],
        ),
    )

    op.create_index(
        "ix_payments_email",
        "payments",
        ["email"],
    )

    op.create_index(
        "ix_payments_status",
        "payments",
        ["status"],
    )

    op.bulk_insert(
        sa.table(
            "tariffs",
            sa.column("title", sa.String),
            sa.column("price", sa.Integer),
        ),
        [
            {
                "title": "basic",
                "price": 990000,
            },
            {
                "title": "standard",
                "price": 1990000,
            },
            {
                "title": "premium",
                "price": 2990000,
            },
        ],
    )


def downgrade() -> None:
    """Откатывает начальную миграцию."""

    op.drop_index(
        "ix_payments_status",
        table_name="payments",
    )

    op.drop_index(
        "ix_payments_email",
        table_name="payments",
    )

    op.drop_table("payments")
    op.drop_table("tariffs")
