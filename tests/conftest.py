import os
import tempfile

import pytest

import app as flask_app


@pytest.fixture
def client():
    db_fd, db_path = tempfile.mkstemp()

    original_database = flask_app.DATABASE if hasattr(
        flask_app,
        "DATABASE"
    ) else None

    flask_app.DATABASE = db_path

    import database

    database.DATABASE = db_path

    flask_app.app.config["TESTING"] = True

    database.init_db()

    with flask_app.app.test_client() as client:
        yield client

    os.close(db_fd)

    if os.path.exists(db_path):
        os.unlink(db_path)

    if original_database is not None:
        flask_app.DATABASE = original_database