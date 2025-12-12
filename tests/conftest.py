import mongomock
import pytest
from autonomous.db import connect, disconnect
from mongomock.gridfs import enable_gridfs_integration

from app import create_app
from autonomous import AutoModel

enable_gridfs_integration()


@pytest.fixture(scope="session")
def app():
    """Create and configure a new app instance for each test session."""
    # Use a testing config
    app = create_app({"TESTING": True, "MONGO_URI": "mongomock://localhost"})

    yield app


@pytest.fixture(scope="session")
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture(scope="session")
def runner(app):
    """A test runner for the app's click commands."""
    return app.test_cli_runner()


@pytest.fixture(scope="function")
def mock_db(app):
    """
    Fixture to mock MongoDB interactions.
    This uses mongomock to simulate a DB in memory.
    """
    # If your custom ORM connects globally, you might need to patch the connection here.
    # For example, if 'autonomous' has a global client:
    with mongomock.patch(servers=(("localhost", 27017),)):
        yield

    # If you need to clean up data after each test function:
    # db_client = ... get client ...
    # db_client.drop_database('test_db')


"""
### 5. Unit Tests (`tests/unit/`)

Unit tests should focus on your custom ORM logic and utility functions *without* spinning up the full Flask app or hitting a real database if possible.

**Example `tests/unit/test_models.py`:**

### 6. Integration Tests (`tests/integration/`)

These tests verify that your Flask routes work correctly, return the right templates/HTMX fragments, and interact with the (mocked) database as expected.

**Example `tests/integration/test_routes.py`:**

@pytest.mark.integration
def test_home_page(client):
    #Test that the home page loads
    response = client.get("/")
    assert response.status_code == 200
    assert b"Welcome" in response.data  # Check for content from your template

### 7. End-to-End (Frontend) Tests (`tests/e2e/`)

These test the full stack, including your Foundation styling and JavaScript interactions (like the recorder or Foundation toggles).

**Example `tests/e2e/test_frontend.py`:**


import threading
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By


@pytest.fixture(scope="module")
def driver():
    #Setup Chrome Driver
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in background
    chrome_options.add_argument("--no-sandbox")
    driver = webdriver.Chrome(options=chrome_options)
    yield driver
    driver.quit()


@pytest.fixture(scope="module")
def server(app):
    #Start a live server in a thread for E2E tests
    # Flask provides a live_server fixture with pytest-flask,
    # but manually starting allows more control if needed.
    # For simplicity, we assume app.run() is handled or use `live_server` fixture if available.
    pass


@pytest.mark.e2e
def test_audio_recorder_ui(driver, live_server):
    #Test that the audio recorder buttons appear.
    driver.get(live_server.url + "/episode/123/manage")  # Adjust URL

    # Find the Start Recording button
    start_btn = driver.find_element(By.ID, "record-btn")
    assert start_btn.is_displayed()

    # Check if Stop button is initially disabled
    stop_btn = driver.find_element(By.ID, "stop-btn")
    assert not stop_btn.is_enabled()
"""
