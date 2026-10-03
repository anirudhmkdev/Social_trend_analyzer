import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, PortableJSON

if TYPE_CHECKING:
    from app.models.dataset import Dataset


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    dataset_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    cleaned_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sentiment_ready_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    platform: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    hashtags: Mapped[Optional[List[str]]] = mapped_column(PortableJSON, nullable=True)
    likes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comments: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    shares: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    author_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    mentions: Mapped[Optional[List[str]]] = mapped_column(PortableJSON, nullable=True)
    urls: Mapped[Optional[List[str]]] = mapped_column(PortableJSON, nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    preprocessing_meta: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        PortableJSON, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="posts")

    __table_args__ = (
        Index("idx_posts_dataset_id", "dataset_id"),
        Index("idx_posts_timestamp", "timestamp"),
        Index("idx_posts_platform", "platform"),
    )
