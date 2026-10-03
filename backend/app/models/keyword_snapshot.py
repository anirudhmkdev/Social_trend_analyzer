import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun
    from app.models.topic import Topic


class KeywordSnapshot(Base):
    __tablename__ = "keyword_snapshots"

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
    keyword: Mapped[str] = mapped_column(String(255), nullable=False)
    keyword_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # keyword, hashtag, ngram
    frequency: Mapped[int] = mapped_column(Integer, nullable=False)
    tfidf_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    growth_rate: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    time_window: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    window_start: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    topic_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("topics.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    analysis_run: Mapped["AnalysisRun"] = relationship(
        "AnalysisRun", back_populates="keyword_snapshots"
    )
    topic: Mapped[Optional["Topic"]] = relationship("Topic")

    __table_args__ = (
        Index("idx_keyword_run", "analysis_run_id"),
        Index("idx_keyword_type", "analysis_run_id", "keyword_type"),
        Index("idx_keyword_freq", "analysis_run_id", "keyword_type", "frequency"),
    )
