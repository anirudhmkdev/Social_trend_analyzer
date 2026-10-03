"""create analysis_runs, topics, sentiment_results, entities, and trend tables

Revision ID: 002_nlp_and_trends
Revises: 001_initial
Create Date: 2026-10-03 17:50:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_nlp_and_trends"
down_revision: Union[str, Sequence[str], None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

portable_json = sa.JSON().with_variant(postgresql.JSONB(), "postgresql")


def upgrade() -> None:
    # 1. analysis_runs
    op.create_table(
        "analysis_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("dataset_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="pending"),
        sa.Column("progress_pct", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_step", sa.String(length=100), nullable=True),
        sa.Column("config", portable_json, nullable=False),
        sa.Column("model_info", portable_json, nullable=True),
        sa.Column("stats", portable_json, nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["dataset_id"], ["datasets.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_analysis_runs_dataset_id", "analysis_runs", ["dataset_id"])
    op.create_index("idx_analysis_runs_status", "analysis_runs", ["status"])

    # 2. topics
    op.create_table(
        "topics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
        sa.Column("topic_index", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("keywords", portable_json, nullable=False),
        sa.Column("representative_docs", portable_json, nullable=True),
        sa.Column("post_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_outlier", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("analysis_run_id", "topic_index", name="uq_topics_run_index"),
    )
    op.create_index("idx_topics_analysis_run", "topics", ["analysis_run_id"])

    # 3. post_topics
    op.create_table(
        "post_topics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
        sa.Column("probability", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "post_id", "topic_id", "analysis_run_id", name="uq_post_topics_composite"
        ),
    )
    op.create_index("idx_post_topics_post", "post_topics", ["post_id"])
    op.create_index("idx_post_topics_topic", "post_topics", ["topic_id"])

    # 4. sentiment_results
    op.create_table(
        "sentiment_results",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
        sa.Column("label", sa.String(length=20), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("score_positive", sa.Float(), nullable=False),
        sa.Column("score_neutral", sa.Float(), nullable=False),
        sa.Column("score_negative", sa.Float(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "analysis_run_id", name="uq_sentiment_post_run"),
    )
    op.create_index("idx_sentiment_post", "sentiment_results", ["post_id"])
    op.create_index("idx_sentiment_run", "sentiment_results", ["analysis_run_id"])
    op.create_index(
        "idx_sentiment_label", "sentiment_results", ["analysis_run_id", "label"]
    )

    # 5. entities
    op.create_table(
        "entities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
        sa.Column("text", sa.String(length=255), nullable=False),
        sa.Column("normalized_text", sa.String(length=255), nullable=False),
        sa.Column("label", sa.String(length=50), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=False, server_default="1"),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "analysis_run_id",
            "normalized_text",
            "label",
            name="uq_entities_run_text_label",
        ),
    )
    op.create_index("idx_entities_run", "entities", ["analysis_run_id"])

    # 6. post_entities
    op.create_table(
        "post_entities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Uuid(), nullable=False),
        sa.Column("entity_id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
        sa.Column("start_char", sa.Integer(), nullable=True),
        sa.Column("end_char", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["entity_id"], ["entities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_post_entities_post", "post_entities", ["post_id"])
    op.create_index("idx_post_entities_entity", "post_entities", ["entity_id"])

    # 7. trend_snapshots
    op.create_table(
        "trend_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
        sa.Column("topic_id", sa.Uuid(), nullable=False),
        sa.Column("time_window", sa.String(length=20), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("trend_score", sa.Float(), nullable=False),
        sa.Column("classification", sa.String(length=20), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=False),
        sa.Column("volume_current", sa.Integer(), nullable=False),
        sa.Column("volume_previous", sa.Integer(), nullable=False),
        sa.Column("volume_growth_pct", sa.Float(), nullable=True),
        sa.Column("engagement_current", sa.Float(), nullable=True),
        sa.Column("engagement_previous", sa.Float(), nullable=True),
        sa.Column("engagement_growth_pct", sa.Float(), nullable=True),
        sa.Column("velocity", sa.Float(), nullable=True),
        sa.Column("burst_score", sa.Float(), nullable=True),
        sa.Column("recency_score", sa.Float(), nullable=True),
        sa.Column("sentiment_positive_pct", sa.Float(), nullable=True),
        sa.Column("sentiment_neutral_pct", sa.Float(), nullable=True),
        sa.Column("sentiment_negative_pct", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "analysis_run_id",
            "topic_id",
            "time_window",
            "window_start",
            name="uq_trend_snapshots_run_topic_window",
        ),
    )
    op.create_index("idx_trend_run", "trend_snapshots", ["analysis_run_id"])
    op.create_index("idx_trend_topic", "trend_snapshots", ["topic_id"])
    op.create_index(
        "idx_trend_score", "trend_snapshots", ["analysis_run_id", "trend_score"]
    )

    # 8. keyword_snapshots
    op.create_table(
        "keyword_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("analysis_run_id", sa.Uuid(), nullable=False),
        sa.Column("keyword", sa.String(length=255), nullable=False),
        sa.Column("keyword_type", sa.String(length=20), nullable=False),
        sa.Column("frequency", sa.Integer(), nullable=False),
        sa.Column("tfidf_score", sa.Float(), nullable=True),
        sa.Column("growth_rate", sa.Float(), nullable=True),
        sa.Column("time_window", sa.String(length=20), nullable=True),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("topic_id", sa.Uuid(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(["analysis_run_id"], ["analysis_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["topic_id"], ["topics.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_keyword_run", "keyword_snapshots", ["analysis_run_id"])
    op.create_index("idx_keyword_type", "keyword_snapshots", ["analysis_run_id", "keyword_type"])
    op.create_index(
        "idx_keyword_freq",
        "keyword_snapshots",
        ["analysis_run_id", "keyword_type", "frequency"],
    )


def downgrade() -> None:
    op.drop_index("idx_keyword_freq", table_name="keyword_snapshots")
    op.drop_index("idx_keyword_type", table_name="keyword_snapshots")
    op.drop_index("idx_keyword_run", table_name="keyword_snapshots")
    op.drop_table("keyword_snapshots")

    op.drop_index("idx_trend_score", table_name="trend_snapshots")
    op.drop_index("idx_trend_topic", table_name="trend_snapshots")
    op.drop_index("idx_trend_run", table_name="trend_snapshots")
    op.drop_table("trend_snapshots")

    op.drop_index("idx_post_entities_entity", table_name="post_entities")
    op.drop_index("idx_post_entities_post", table_name="post_entities")
    op.drop_table("post_entities")

    op.drop_index("idx_entities_run", table_name="entities")
    op.drop_table("entities")

    op.drop_index("idx_sentiment_label", table_name="sentiment_results")
    op.drop_index("idx_sentiment_run", table_name="sentiment_results")
    op.drop_index("idx_sentiment_post", table_name="sentiment_results")
    op.drop_table("sentiment_results")

    op.drop_index("idx_post_topics_topic", table_name="post_topics")
    op.drop_index("idx_post_topics_post", table_name="post_topics")
    op.drop_table("post_topics")

    op.drop_index("idx_topics_analysis_run", table_name="topics")
    op.drop_table("topics")

    op.drop_index("idx_analysis_runs_status", table_name="analysis_runs")
    op.drop_index("idx_analysis_runs_dataset_id", table_name="analysis_runs")
    op.drop_table("analysis_runs")
