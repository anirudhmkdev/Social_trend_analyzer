"""create initial datasets and posts tables

Revision ID: 001_initial
Revises:
Create Date: 2026-09-28 21:55:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

portable_json = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    op.create_table(
        "datasets",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("source_type", sa.String(length=50), nullable=False, server_default="csv"),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("row_count", sa.Integer(), nullable=True),
        sa.Column("valid_row_count", sa.Integer(), nullable=True),
        sa.Column("column_mapping", portable_json, nullable=True),
        sa.Column("validation_results", portable_json, nullable=True),
        sa.Column(
            "preprocessing_version",
            sa.String(length=20),
            nullable=False,
            server_default="1.0.0",
        ),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="uploaded"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "posts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("original_text", sa.Text(), nullable=False),
        sa.Column("cleaned_text", sa.Text(), nullable=True),
        sa.Column("sentiment_ready_text", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=True),
        sa.Column("hashtags", portable_json, nullable=True),
        sa.Column("likes", sa.Integer(), nullable=True),
        sa.Column("comments", sa.Integer(), nullable=True),
        sa.Column("shares", sa.Integer(), nullable=True),
        sa.Column("author_id", sa.String(length=255), nullable=True),
        sa.Column("mentions", portable_json, nullable=True),
        sa.Column("urls", portable_json, nullable=True),
        sa.Column("is_duplicate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("preprocessing_meta", portable_json, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("idx_posts_dataset_id", "posts", ["dataset_id"])
    op.create_index("idx_posts_timestamp", "posts", ["timestamp"])
    op.create_index("idx_posts_platform", "posts", ["platform"])


def downgrade() -> None:
    op.drop_index("idx_posts_platform", table_name="posts")
    op.drop_index("idx_posts_timestamp", table_name="posts")
    op.drop_index("idx_posts_dataset_id", table_name="posts")
    op.drop_table("posts")
    op.drop_table("datasets")
