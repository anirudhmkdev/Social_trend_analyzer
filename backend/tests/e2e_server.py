"""Real API for deterministic browser integration; only inference is fixture-injected."""

from pathlib import Path

import uvicorn
from alembic import command
from alembic.config import Config

from tests.model_fixtures import install_model_fixtures

if __name__ == "__main__":
    Path("../.verification").mkdir(exist_ok=True)
    command.upgrade(Config("alembic.ini"), "head")
    install_model_fixtures()
    uvicorn.run("app.main:app", host="127.0.0.1", port=8001)
