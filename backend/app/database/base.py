from sqlalchemy import JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase

# Portable JSON type: uses native PostgreSQL JSONB (binary JSON + GIN indexing support)
# on PostgreSQL, and standard JSON/TEXT on SQLite.
PortableJSON = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    pass
