from __future__ import annotations

from pathlib import Path
from flask import Flask

from .extensions import db
from .routes import api


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)

    repo_root = Path(__file__).resolve().parents[2]
    data_dir = repo_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    default_db_path = data_dir / "exercises.db"

    app.config.from_mapping(
        TESTING=False,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{default_db_path}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )

    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    app.register_blueprint(api)
    return app

