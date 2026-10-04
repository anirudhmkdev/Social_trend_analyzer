"""Disclose unknown model provenance on historical completed analyses."""

import sqlalchemy as sa
from alembic import op

revision = "005_legacy_provenance"
down_revision = "004_topic_provenance"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    runs = sa.Table("analysis_runs", sa.MetaData(), autoload_with=bind)
    for row in bind.execute(
        sa.select(runs.c.id, runs.c.model_info).where(runs.c.status == "completed")
    ):
        info = dict(row.model_info or {})
        if "ner" not in info or "topic_parameters" not in info:
            info["legacy_unverified"] = True
            bind.execute(runs.update().where(runs.c.id == row.id).values(model_info=info))


def downgrade() -> None:
    bind = op.get_bind()
    runs = sa.Table("analysis_runs", sa.MetaData(), autoload_with=bind)
    for row in bind.execute(sa.select(runs.c.id, runs.c.model_info)):
        info = dict(row.model_info or {})
        if "legacy_unverified" in info:
            info.pop("legacy_unverified")
            bind.execute(runs.update().where(runs.c.id == row.id).values(model_info=info))
