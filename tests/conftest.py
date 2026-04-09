"""Shared pytest fixtures for the test suite."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db
from src.main import app

TEST_DATABASE_URL = "sqlite:///./test_mood_tracker.db"


@pytest.fixture(scope="session")
def engine():
    """Create an in-process SQLite engine for the test session."""
    test_engine = create_engine(
        TEST_DATABASE_URL, connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=test_engine)
    yield test_engine
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db(engine):
    """Provide a transactional database session that rolls back after each test."""
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """Return a FastAPI TestClient wired to the test database session."""

    def override_get_db():
        """Yield the test session instead of the production one."""
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
