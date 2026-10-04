"""One validated context for every dataset/run-scoped read."""

import uuid
from typing import Optional

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictException, EntityNotFoundException, ValidationException
from app.models.analysis_run import AnalysisRun
from app.models.dataset import Dataset


def resolve_run(
    db: Session,
    run_id: Optional[uuid.UUID],
    dataset_id: Optional[uuid.UUID] = None,
    require_completed: bool = True,
) -> Optional[AnalysisRun]:
    if dataset_id and db.get(Dataset, dataset_id) is None:
        raise EntityNotFoundException("Dataset", str(dataset_id))
    if run_id is None:
        return None  # Never infer a global dataset or run.
    run = db.get(AnalysisRun, run_id)
    if run is None:
        raise EntityNotFoundException("AnalysisRun", str(run_id))
    if dataset_id and run.dataset_id != dataset_id:
        raise ValidationException("The selected analysis run does not belong to this dataset.")
    if require_completed and run.status != "completed":
        raise ConflictException(f"Analysis is {run.status}; completed results are not available.")
    return run
