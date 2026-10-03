import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun
    from app.models.post import Post


class SentimentResult(Base):
    __tablename__ = "sentiment_results"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    post_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    label: Mapped[str] = mapped_column(String(20), nullable=False)  # positive, neutral, negative
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    score_positive: Mapped[float] = mapped_column(Float, nullable=False)
    score_neutral: Mapped[float] = mapped_column(Float, nullable=False)
    score_negative: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    post: Mapped["Post"] = relationship("Post")
    analysis_run: Mapped["AnalysisRun"] = relationship(
        "AnalysisRun", back_populates="sentiment_results"
    )

    __table_args__ = (
        UniqueConstraint("post_id", "analysis_run_id", name="uq_sentiment_post_run"),
        Index("idx_sentiment_post", "post_id"),
        Index("idx_sentiment_run", "analysis_run_id"),
        Index("idx_sentiment_label", "analysis_run_id", "label"),
    )
