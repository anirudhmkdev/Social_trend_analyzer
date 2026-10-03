"""Exercise committed migrations, downgrade, constraints and metadata drift."""

from alembic import command
from alembic.config import Config
from sqlalchemy import MetaData, Table, create_engine, inspect, select

from app.config import settings


def test_sqlite_migration_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DATABASE_URL", "sqlite:///" + str(tmp_path / "migration.db"))
    config = Config("alembic.ini")
    command.upgrade(config, "002_nlp_and_trends")
    engine = create_engine(settings.DATABASE_URL)
    # Preserve existing data while adding fields and disclosing unverifiable old runs.
    metadata = MetaData()
    datasets = Table("datasets", metadata, autoload_with=engine)
    runs = Table("analysis_runs", metadata, autoload_with=engine)
    dataset_id = "1" * 32
    legacy_id = "2" * 32
    verified_id = "3" * 32
    with engine.begin() as connection:
        connection.execute(
            datasets.insert().values(id=dataset_id, name="Legacy", filename="old.csv")
        )
        connection.execute(
            runs.insert().values(
                id=legacy_id,
                dataset_id=dataset_id,
                status="completed",
                config={},
                model_info={"sentiment_model": "original-model-name"},
            )
        )
        connection.execute(
            runs.insert().values(
                id=verified_id,
                dataset_id=dataset_id,
                status="completed",
                config={},
                model_info={
                    "ner": {"status": "loaded"},
                    "topic_parameters": {"method": "bertopic"},
                },
            )
        )
    command.upgrade(config, "head")
    with engine.connect() as connection:
        info = connection.execute(
            select(runs.c.model_info).where(runs.c.id == legacy_id)
        ).scalar_one()
        assert info == {"sentiment_model": "original-model-name", "legacy_unverified": True}
        verified = connection.execute(
            select(runs.c.model_info).where(runs.c.id == verified_id)
        ).scalar_one()
        assert "legacy_unverified" not in verified
        assert connection.execute(select(datasets.c.name)).scalar_one() == "Legacy"
    assert "staged_filename" in {c["name"] for c in inspect(engine).get_columns("datasets")}
    assert "model_metadata" in {c["name"] for c in inspect(engine).get_columns("topics")}
    command.check(config)
    command.downgrade(config, "base")
    assert inspect(engine).get_table_names() == ["alembic_version"]
    command.upgrade(config, "head")
    assert "post_topics" in inspect(engine).get_table_names()
    engine.dispose()
