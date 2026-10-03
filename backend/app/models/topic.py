import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, PortableJSON

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun
    from app.models.post import Post
    from app.models.trend_snapshot import TrendSnapshot


class Topic(Base):
    __tablename__ = "topics"

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
    topic_index: Mapped[int] = mapped_column(Integer, nullable=False)  # -1 = outlier
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    keywords: Mapped[List[Dict[str, Any]]] = mapped_column(
        PortableJSON, nullable=False, default=list
    )  # [{"word": str, "score": float}]
    representative_docs: Mapped[Optional[List[str]]] = mapped_column(PortableJSON, nullable=True)
    post_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_outlier: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="topics")
    post_topics: Mapped[List["PostTopic"]] = relationship(
        "PostTopic", back_populates="topic", cascade="all, delete-orphan"
    )
    trend_snapshots: Mapped[List["TrendSnapshot"]] = relationship(
        "TrendSnapshot", back_populates="topic", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_topics_analysis_run", "analysis_run_id"),
        UniqueConstraint("analysis_run_id", "topic_index", name="uq_topics_run_index"),
    )


class PostTopic(Base):
    __tablename__ = "post_topics"

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
    topic_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    probability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    post: Mapped["Post"] = relationship("Post")
    topic: Mapped["Topic"] = relationship("Topic", back_populates="post_topics")
    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun")

    __table_args__ = (
        Index("idx_post_topics_post", "post_id"),
        Index("idx_post_topics_topic", "topic_id"),
        UniqueConstraint("post_id", "topic_id", "analysis_run_id", name="uq_post_topics_composite"),
    )
