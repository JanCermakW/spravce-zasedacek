import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.main import app, get_session
from app.models import Room

# Nastavení testovací in-memory databáze (aby se data neukládala do souboru)
sqlite_url = "sqlite://" 
engine = create_engine(
    sqlite_url, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool  # <--- TOTO JE KLÍČOVÁ OPRAVA
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_test_session():
    with Session(engine) as session:
        yield session

# Přepsání závislosti (Dependency Override)
app.dependency_overrides[get_session] = get_test_session

# Vytvoření testovacího klienta
client = TestClient(app)

# Fixture, která před každým testem vyčistí/vytvoří DB
@pytest.fixture(name="session")
def session_fixture():
    create_db_and_tables()
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def test_create_room(session: Session):
    response = client.post("/rooms/", json={"name": "Zasedačka A", "capacity": 10})
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Zasedačka A"
    assert data["id"] is not None

def test_create_booking_success(session: Session):
    
    room = Room(name="Test Room", capacity=5)
    session.add(room)
    session.commit()
    session.refresh(room)

    payload = {
        "room_id": room.id,
        "user_name": "Tester",
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T11:00:00",
        "attendees": 3
    }
    response = client.post("/bookings/", json=payload)
    assert response.status_code == 200
    assert response.json()["user_name"] == "Tester"

def test_create_booking_fail_capacity(session: Session):
    # Místnost s kapacitou 2
    room = Room(name="Malá", capacity=2)
    session.add(room)
    session.commit()
    session.refresh(room)

    # Zkusíme 5 lidí
    payload = {
        "room_id": room.id,
        "user_name": "Tester",
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T11:00:00",
        "attendees": 5 
    }
    response = client.post("/bookings/", json=payload)
    
    # Očekáváme 400 Bad Request
    assert response.status_code == 400
    assert "Capacity exceeded" in response.json()["detail"]