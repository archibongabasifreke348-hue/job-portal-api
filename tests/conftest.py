import os
import tempfile
import pytest

from app import app


@pytest.fixture
def client():
    # Create a temporary database for testing
    db_fd, db_path = tempfile.mkstemp()

    # Tell Flask to use the temporary database
    app.config["TESTING"] = True

    original_database = app.config.get("DATABASE")

    # Change the database used by the application
    import app as flask_app
    flask_app.DATABASE = db_path

    # Create the tables in the temporary database
    flask_app.init_db()

    with app.test_client() as client:
        yield client

    # Close and delete temporary database
    os.close(db_fd)

    if os.path.exists(db_path):
        os.unlink(db_path)

    # Restore original database setting
    if original_database is not None:
        flask_app.DATABASE = original_database