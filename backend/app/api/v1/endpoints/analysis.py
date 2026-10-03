"""API routes for analysis runs and sentiment results."""

import uuid
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.orm import Session

from app.database.engine import get_db
from app.schemas.analysis import (
    AnalysisRunCreate,
    AnalysisRunResponse,
    SentimentSummaryResponse,
)
from app.services.analysis_service import (
    create_analysis_run,
    execute_analysis_run,
    get_active_analysis_run,
    get_analysis_run,
    list_analysis_runs,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/run", response_model=AnalysisRunResponse, status_code=status.HTTP_201_CREATED)
def trigger_analysis_run(
    payload: AnalysisRunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> AnalysisRunResponse:
    """Create and enqueue an analysis run.

    Enforces 1 active analysis at a time. Returns HTTP 409 if another run is running/pending.
    """
    run = create_analysis_run(db, payload.dataset_id, payload.config)
    background_tasks.add_task(execute_analysis_run, run.id)
    return AnalysisRunResponse.model_validate(run)


@router.get("/active", response_model=Optional[AnalysisRunResponse])
def get_current_active_run(db: Session = Depends(get_db)) -> Optional[AnalysisRunResponse]:
    """Get the currently pending or running analysis run, if any."""
    active = get_active_analysis_run(db)
    if not active:
        return None
    return AnalysisRunResponse.model_validate(active)


@router.get("", response_model=List[AnalysisRunResponse])
def get_analysis_runs(
    dataset_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
) -> List[AnalysisRunResponse]:
    """List analysis runs, optionally filtered by dataset."""
    runs = list_analysis_runs(db, dataset_id=dataset_id)
    return [AnalysisRunResponse.model_validate(r) for r in runs]


@router.get("/{run_id}/status", response_model=AnalysisRunResponse)
def get_run_status(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> AnalysisRunResponse:
    """Check status, progress percentage, current step, and stats for a run."""
    run = get_analysis_run(db, run_id)
    return AnalysisRunResponse.model_validate(run)


@router.get("/{run_id}/sentiment", response_model=SentimentSummaryResponse)
def get_sentiment_summary(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> SentimentSummaryResponse:
    """Get aggregate sentiment statistics and evaluation metrics for a run."""
    run = get_analysis_run(db, run_id)
    sentiment_stats = (run.stats or {}).get("sentiment", {})
    total = sentiment_stats.get("total_posts", 0)
    pos = sentiment_stats.get("positive_count", 0)
    neu = sentiment_stats.get("neutral_count", 0)
    neg = sentiment_stats.get("negative_count", 0)

    return SentimentSummaryResponse(
        analysis_run_id=run.id,
        total_posts=total,
        positive_count=pos,
        neutral_count=neu,
        negative_count=neg,
        positive_pct=sentiment_stats.get("positive_pct", 0.0),
        neutral_pct=sentiment_stats.get("neutral_pct", 0.0),
        negative_pct=sentiment_stats.get("negative_pct", 0.0),
        evaluation_metrics=sentiment_stats.get("evaluation_metrics"),
    )
