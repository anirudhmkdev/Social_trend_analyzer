import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun
    from app.models.topic import Topic


class TrendSnapshot(Base):
    __tablename__ = "trend_snapshots"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    time_window: Mapped[str] = mapped_column(String(20), nullable=False)  # hourly, daily, weekly
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    trend_score: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # emerging, rising, stable, declining
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    volume_current: Mapped[int] = mapped_column(Integer, nullable=False)
    volume_previous: Mapped[int] = mapped_column(Integer, nullable=False)
    volume_growth_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    engagement_current: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    engagement_previous: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    engagement_growth_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    velocity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    burst_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    recency_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sentiment_positive_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sentiment_neutral_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sentiment_negative_pct: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    analysis_run: Mapped["AnalysisRun"] = relationship(
        "AnalysisRun", back_populates="trend_snapshots"
    )
    topic: Mapped["Topic"] = relationship("Topic", back_populates="trend_snapshots")

    __table_args__ = (
        Index("idx_trend_run", "analysis_run_id"),
        Index("idx_trend_topic", "topic_id"),
        Index("idx_trend_score", "analysis_run_id", "trend_score"),
        UniqueConstraint(
            "analysis_run_id",
            "topic_id",
            "time_window",
            "window_start",
            name="uq_trend_snapshots_run_topic_window",
        ),
    )
