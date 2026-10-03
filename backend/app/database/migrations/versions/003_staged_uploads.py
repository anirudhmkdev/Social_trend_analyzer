"""Track local staged CSV uploads without exposing filesystem paths.

Revision ID: 003_staged_uploads
Revises: 002_nlp_and_trends
"""

import sqlalchemy as sa
from alembic import op

from app.database.base import PortableJSON

revision = "003_staged_uploads"
down_revision = "002_nlp_and_trends"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("datasets", sa.Column("staged_filename", sa.String(50), nullable=True))
    op.add_column("datasets", sa.Column("upload_metadata", PortableJSON, nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("datasets") as batch:
        batch.drop_column("upload_metadata")
        batch.drop_column("staged_filename")
