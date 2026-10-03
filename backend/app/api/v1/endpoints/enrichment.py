"""API routes for enrichment: entities, keywords, hashtags."""

import uuid
from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.models.analysis_run import AnalysisRun
from app.models.entity import Entity
from app.models.keyword_snapshot import KeywordSnapshot
from app.schemas.enrichment import (
    EntityListResponse,
    EntityResponse,
    HashtagListResponse,
    HashtagResponse,
    KeywordListResponse,
    KeywordResponse,
)

router = APIRouter(prefix="/enrichment", tags=["enrichment"])


def _resolve_run_id(db: Session, run_id: Optional[uuid.UUID]) -> Optional[uuid.UUID]:
    if run_id is not None:
        return run_id
    latest = db.execute(
        select(AnalysisRun)
        .where(AnalysisRun.status == "completed")
        .order_by(AnalysisRun.completed_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    return latest.id if latest else None


@router.get("/entities", response_model=EntityListResponse)
def get_entities(
    analysis_run_id: Optional[uuid.UUID] = None,
    label: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> EntityListResponse:
    """Retrieve named entities aggregated across posts for a run."""
    run_id = _resolve_run_id(db, analysis_run_id)
    if not run_id:
        return EntityListResponse(entities=[], total_entities=0, by_type={})

    stmt = select(Entity).where(Entity.analysis_run_id == run_id)
    if label:
        stmt = stmt.where(Entity.label == label.upper())
    stmt = stmt.order_by(desc(Entity.frequency)).limit(limit)

    entities = list(db.execute(stmt).scalars().all())

    # Calculate type counts
    by_type: Dict[str, int] = {}
    all_ents = db.execute(
        select(Entity.label, Entity.frequency).where(Entity.analysis_run_id == run_id)
    ).all()
    for ent_label, freq in all_ents:
        by_type[ent_label] = by_type.get(ent_label, 0) + freq

    return EntityListResponse(
        entities=[EntityResponse.model_validate(e) for e in entities],
        total_entities=len(entities),
        by_type=by_type,
    )


@router.get("/keywords", response_model=KeywordListResponse)
def get_keywords(
    analysis_run_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> KeywordListResponse:
    """Retrieve TF-IDF keywords and n-grams for an analysis run."""
    run_id = _resolve_run_id(db, analysis_run_id)
    if not run_id:
        return KeywordListResponse(items=[], total=0)

    stmt = (
        select(KeywordSnapshot)
        .where(
            KeywordSnapshot.analysis_run_id == run_id,
            KeywordSnapshot.keyword_type.in_(["keyword", "ngram"]),
        )
        .order_by(desc(KeywordSnapshot.tfidf_score))
        .limit(limit)
    )
    items = list(db.execute(stmt).scalars().all())

    return KeywordListResponse(
        items=[
            KeywordResponse(
                keyword=k.keyword,
                keyword_type=k.keyword_type,
                frequency=k.frequency,
                tfidf_score=k.tfidf_score,
                growth_rate=k.growth_rate,
            )
            for k in items
        ],
        total=len(items),
    )


@router.get("/hashtags", response_model=HashtagListResponse)
def get_hashtags(
    analysis_run_id: Optional[uuid.UUID] = None,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> HashtagListResponse:
    """Retrieve hashtags and growth metrics for an analysis run."""
    run_id = _resolve_run_id(db, analysis_run_id)
    if not run_id:
        return HashtagListResponse(hashtags=[], total=0)

    stmt = (
        select(KeywordSnapshot)
        .where(
            KeywordSnapshot.analysis_run_id == run_id,
            KeywordSnapshot.keyword_type == "hashtag",
        )
        .order_by(desc(KeywordSnapshot.frequency))
        .limit(limit)
    )
    items = list(db.execute(stmt).scalars().all())

    return HashtagListResponse(
        hashtags=[
            HashtagResponse(
                hashtag=h.keyword,
                frequency=h.frequency,
                growth_rate=h.growth_rate,
            )
            for h in items
        ],
        total=len(items),
    )
