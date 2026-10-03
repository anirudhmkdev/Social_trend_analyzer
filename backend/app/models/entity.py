import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.analysis_run import AnalysisRun
    from app.models.post import Post


class Entity(Base):
    __tablename__ = "entities"

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
    text: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_text: Mapped[str] = mapped_column(String(255), nullable=False)
    label: Mapped[str] = mapped_column(String(50), nullable=False)
    frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun", back_populates="entities")
    post_entities: Mapped[List["PostEntity"]] = relationship(
        "PostEntity", back_populates="entity", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_entities_run", "analysis_run_id"),
        UniqueConstraint(
            "analysis_run_id", "normalized_text", "label", name="uq_entities_run_text_label"
        ),
    )


class PostEntity(Base):
    __tablename__ = "post_entities"

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
    entity_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("entities.id", ondelete="CASCADE"),
        nullable=False,
    )
    analysis_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("analysis_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    start_char: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_char: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    post: Mapped["Post"] = relationship("Post")
    entity: Mapped["Entity"] = relationship("Entity", back_populates="post_entities")
    analysis_run: Mapped["AnalysisRun"] = relationship("AnalysisRun")

    __table_args__ = (
        Index("idx_post_entities_post", "post_id"),
        Index("idx_post_entities_entity", "entity_id"),
    )
