import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import BigInteger, DateTime, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, PortableJSON

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun
    from app.models.post import Post


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    staged_filename: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    upload_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(PortableJSON, nullable=True)
    source_type: Mapped[str] = mapped_column(String(50), nullable=False, default="csv")
    file_size_bytes: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    valid_row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_mapping: Mapped[Optional[Dict[str, Any]]] = mapped_column(PortableJSON, nullable=True)
    validation_results: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        PortableJSON, nullable=True
    )
    preprocessing_version: Mapped[str] = mapped_column(String(20), nullable=False, default="1.0.0")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="uploaded")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    posts: Mapped[List["Post"]] = relationship(
        "Post",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    analysis_runs: Mapped[List["AnalysisRun"]] = relationship(
        "AnalysisRun", back_populates="dataset", cascade="all, delete-orphan"
    )
