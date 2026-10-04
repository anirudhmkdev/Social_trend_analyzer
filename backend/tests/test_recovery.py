from datetime import datetime, timezone

from app.models.dataset import Dataset
from app.models.post import Post
from app.nlp.enrichment.ner import EntityRecognizer
from app.services.analysis_service import (
    create_analysis_run,
    execute_analysis_run,
    recover_interrupted_runs,
)


def imported_dataset(db):
    dataset = Dataset(name="Recovery", filename="fixture.csv", source_type="csv", status="imported")
    db.add(dataset)
    db.flush()
    db.add(
        Post(
            dataset_id=dataset.id,
            original_text="A valid post about OpenAI models.",
            timestamp=datetime.now(timezone.utc),
        )
    )
    db.commit()
    return dataset


def test_optional_ner_failure_keeps_completed_run_transparent(db_session):
    dataset = imported_dataset(db_session)
    ner = EntityRecognizer.get_instance()
    ner._nlp = None
    ner.status = "unavailable"
    ner.error = "NER omitted: model weights unavailable."
    run = create_analysis_run(db_session, dataset.id)
    execute_analysis_run(run.id, db_session)
    assert run.status == "completed"
    assert run.model_info["degraded"] is True
    assert run.model_info["ner"]["status"] == "unavailable"
    assert run.model_info["warnings"] == [ner.error]


def test_server_restart_releases_interrupted_run(db_session):
    dataset = imported_dataset(db_session)
    run = create_analysis_run(db_session, dataset.id)
    recover_interrupted_runs(db_session)
    assert run.status == "failed" and "restart" in run.error_message
    assert create_analysis_run(db_session, dataset.id).status == "pending"
