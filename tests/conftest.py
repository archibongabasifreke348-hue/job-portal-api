import os
import tempfile
import pytest

import app as flask_app


@pytest.fixture
def client():
    # Create a temporary database
    db_fd, db_path = tempfile.mkstemp()

    # Tell the application to use the temporary database
    flask_app.DATABASE = db_path
    flask_app.app.config["TESTING"] = True

    # Create the tables in the temporary database
    flask_app.init_db()

    with flask_app.app.test_client() as client:
        yield client

    # Close and delete the temporary database
    os.close(db_fd)

    if os.path.exists(db_path):
        os.unlink(db_path)