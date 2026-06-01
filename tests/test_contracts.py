import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session
from app.models.user import User
from app.services.auth import hash_password


# --- Test database setup ---

@pytest.fixture(name="session")
def session_fixture():
    """Creates a fresh in-memory SQLite DB for each test."""
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    """Override the DB dependency to use the test DB."""
    def override_get_session():
        yield session

    app.dependency_overrides[get_session] = override_get_session
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient, session: Session):
    """Create a user and return auth headers."""
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hash_password("testpass123"),
    )
    session.add(user)
    session.commit()

    response = client.post(
        "/users/login",
        data={"username": "test@example.com", "password": "testpass123"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# --- Tests ---

def test_health(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_user(client: TestClient):
    response = client.post("/users/register", json={
        "email": "new@example.com",
        "full_name": "New User",
        "password": "securepass",
    })
    assert response.status_code == 200
    assert response.json()["email"] == "new@example.com"
    assert "hashed_password" not in response.json()  # never leak this


def test_create_contract(client: TestClient, auth_headers: dict):
    response = client.post("/contracts/", json={
        "title": "Service Agreement",
        "content": "This agreement is between Party A and Party B for software services.",
        "status": "draft",
    }, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Service Agreement"
    assert data["owner_id"] is not None


def test_list_contracts_filtered(client: TestClient, auth_headers: dict):
    # Create two contracts with different statuses
    client.post("/contracts/", json={"title": "Draft One", "content": "Content here for draft contract one", "status": "draft"}, headers=auth_headers)
    client.post("/contracts/", json={"title": "Active One", "content": "Content here for active contract one", "status": "active"}, headers=auth_headers)

    response = client.get("/contracts/?status=draft", headers=auth_headers)
    assert response.status_code == 200
    results = response.json()
    assert all(c["status"] == "draft" for c in results)


def test_update_contract(client: TestClient, auth_headers: dict):
    create = client.post("/contracts/", json={
        "title": "Old Title", "content": "Some contract content here.", "status": "draft"
    }, headers=auth_headers)
    contract_id = create.json()["id"]

    response = client.patch(f"/contracts/{contract_id}", json={"title": "New Title"}, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["status"] == "draft"  # unchanged


def test_cannot_access_others_contract(client: TestClient, session: Session, auth_headers: dict):
    # Create a second user and their contract
    other_user = User(email="other@example.com", full_name="Other", hashed_password=hash_password("pass"))
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    from app.models.contract import Contract
    contract = Contract(title="Private", content="Secret content", owner_id=other_user.id)
    session.add(contract)
    session.commit()
    session.refresh(contract)

    response = client.get(f"/contracts/{contract.id}", headers=auth_headers)
    assert response.status_code == 404  # not 403 — don't leak existence