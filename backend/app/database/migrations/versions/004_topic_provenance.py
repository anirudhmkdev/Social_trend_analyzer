"""Preserve raw topic identity/keywords separately from concise display labels."""

import sqlalchemy as sa
from alembic import op

from app.database.base import PortableJSON

revision = "004_topic_provenance"
down_revision = "003_staged_uploads"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("topics", sa.Column("model_metadata", PortableJSON, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("topics") as batch:
        batch.drop_column("model_metadata")
