import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, PortableJSON

if TYPE_CHECKING:
    from app.models.dataset import Dataset
    from app.models.entity import Entity
    from app.models.keyword_snapshot import KeywordSnapshot
    from app.models.sentiment_result import SentimentResult
    from app.models.topic import Topic
    from app.models.trend_snapshot import TrendSnapshot


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="pending"
    )  # pending, running, completed, failed
    progress_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_step: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    config: Mapped[Dict[str, Any]] = mapped_column(PortableJSON, nullable=False, default=dict)
    model_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(PortableJSON, nullable=True)
    stats: Mapped[Optional[Dict[str, Any]]] = mapped_column(PortableJSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="analysis_runs")
    sentiment_results: Mapped[List["SentimentResult"]] = relationship(
        "SentimentResult", back_populates="analysis_run", cascade="all, delete-orphan"
    )
    topics: Mapped[List["Topic"]] = relationship(
        "Topic", back_populates="analysis_run", cascade="all, delete-orphan"
    )
    entities: Mapped[List["Entity"]] = relationship(
        "Entity", back_populates="analysis_run", cascade="all, delete-orphan"
    )
    trend_snapshots: Mapped[List["TrendSnapshot"]] = relationship(
        "TrendSnapshot", back_populates="analysis_run", cascade="all, delete-orphan"
    )
    keyword_snapshots: Mapped[List["KeywordSnapshot"]] = relationship(
        "KeywordSnapshot", back_populates="analysis_run", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_analysis_runs_dataset_id", "dataset_id"),
        Index("idx_analysis_runs_status", "status"),
    )
