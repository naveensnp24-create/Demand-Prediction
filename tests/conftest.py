import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.core.database import get_db
from backend.app.models.database import Base
from backend.app.main import app
from generate_data import generate_dataset


@pytest.fixture
def client():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )

    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False)

    def override():
        with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture(scope="session")
def dataset():
    return generate_dataset(customers=20, products=16, days=120, seed=42, end_date="2025-06-30")


@pytest.fixture
def populated(client, dataset):
    files = {
        name: (f"{name}.csv", frame.to_csv(index=False), "text/csv")
        for name, frame in dataset.items()
    }
    response = client.post("/api/v1/upload", files=files)
    assert response.status_code == 200, response.text
    return client
