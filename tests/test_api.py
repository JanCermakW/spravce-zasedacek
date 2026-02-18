import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.main import app, get_session
from app.models import Room, User
from datetime import datetime

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
    user = User(username="Tester", email="tester@test.cz")
    session.add(user)
    session.commit()
    session.refresh(user)

    room = Room(name="Test Room", capacity=5)
    session.add(room)
    session.commit()
    session.refresh(room)

    payload = {
        "room_id": room.id,
        "user_id": user.id,
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T11:00:00",
        "attendees": 3
    }
    response = client.post("/bookings/", json=payload)
    assert response.status_code == 200
    assert response.json()["user_id"] == user.id

def test_create_booking_fail_capacity(session: Session):
    # Místnost s kapacitou 2
    room = Room(name="Malá", capacity=2)
    session.add(room)
    session.commit()
    session.refresh(room)

    #Vytvoření uživatele
    user = User(username="pepa", email="pepa@test.cz")
    session.add(user)
    session.commit()

    # Zkusíme 5 lidí
    payload = {
        "room_id": room.id,
        "user_id": user.id,
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T11:00:00",
        "attendees": 5 
    }
    response = client.post("/bookings/", json=payload)
    
    # Očekáváme 400 Bad Request
    assert response.status_code == 400
    assert "Capacity exceeded" in response.json()["detail"]

def test_full_booking_flow(session: Session):
    # Vytvoření místnosti
    room = Room(name="Velká", capacity=10)
    session.add(room)
    
    #Vytvoření uživatele
    user = User(username="pepa", email="pepa@test.cz")
    session.add(user)
    session.commit()

    #Vytvoření rezervace
    start_dt = datetime(2025, 1, 1, 10, 0)
    end_dt = datetime(2025, 1, 1, 11, 0)
    
    payload = {
        "room_id": room.id,
        "user_id": user.id,
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        "attendees": 5
    }
    response = client.post("/bookings/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == user.id

def test_booking_weekend_fail(session: Session):
    """Pravidlo: Nelze o víkendu."""
    room = Room(name="Relax", capacity=5)
    user = User(username="vikendar", email="v@v.cz")
    session.add(room)
    session.add(user)
    session.commit()

    # Sobota 4.1.2025
    start_dt = datetime(2025, 1, 4, 10, 0) 
    end_dt = datetime(2025, 1, 4, 11, 0)

    payload = {
        "room_id": room.id,
        "user_id": user.id,
        "start_time": start_dt.isoformat(),
        "end_time": end_dt.isoformat(),
        "attendees": 2
    }
    response = client.post("/bookings/", json=payload)
    assert response.status_code == 400
    assert "weekends" in response.json()["detail"]

def test_create_booking_fail_end_before_start(session: Session):
    """API test: end_time < start_time → 400."""
    room = Room(name="Časová", capacity=10)
    user = User(username="casovac", email="c@c.cz")
    session.add(room)
    session.add(user)
    session.commit()

    payload = {
        "room_id": room.id,
        "user_id": user.id,
        "start_time": "2025-01-01T11:00:00",
        "end_time": "2025-01-01T10:00:00",
        "attendees": 2
    }
    response = client.post("/bookings/", json=payload)
    assert response.status_code == 400
    assert "End time must be after start time" in response.json()["detail"]

def test_create_booking_fail_room_not_found(session: Session):
    """API test: neexistující místnost → 404."""
    user = User(username="ghost", email="g@g.cz")
    session.add(user)
    session.commit()

    payload = {
        "room_id": 9999,
        "user_id": user.id,
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T11:00:00",
        "attendees": 1
    }
    response = client.post("/bookings/", json=payload)
    assert response.status_code == 404
    assert "Room not found" in response.json()["detail"]

def test_create_booking_fail_user_not_found(session: Session):
    """API test: neexistující uživatel → 404."""
    room = Room(name="Existující", capacity=5)
    session.add(room)
    session.commit()

    payload = {
        "room_id": room.id,
        "user_id": 9999,
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T11:00:00",
        "attendees": 1
    }
    response = client.post("/bookings/", json=payload)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_create_booking_fail_overlap(session: Session):
    """API test: překrývající se rezervace → 400."""
    room = Room(name="Obsazená", capacity=10)
    user = User(username="prvni", email="p@p.cz")
    session.add(room)
    session.add(user)
    session.commit()

    # První rezervace – úspěšná
    payload1 = {
        "room_id": room.id,
        "user_id": user.id,
        "start_time": "2025-01-01T10:00:00",
        "end_time": "2025-01-01T11:00:00",
        "attendees": 2
    }
    resp1 = client.post("/bookings/", json=payload1)
    assert resp1.status_code == 200

    # Druhá rezervace – stejný čas, stejná místnost = kolize
    user2 = User(username="druhy", email="d@d.cz")
    session.add(user2)
    session.commit()

    payload2 = {
        "room_id": room.id,
        "user_id": user2.id,
        "start_time": "2025-01-01T10:30:00",
        "end_time": "2025-01-01T11:30:00",
        "attendees": 2
    }
    resp2 = client.post("/bookings/", json=payload2)
    assert resp2.status_code == 400
    assert "Room is already booked" in resp2.json()["detail"]

def test_create_booking_fail_user_limit(session: Session):
    """API test: uživatel s 2 budoucími rezervacemi nemůže vytvořit 3."""
    room1 = Room(name="Místnost 1", capacity=10)
    room2 = Room(name="Místnost 2", capacity=10)
    room3 = Room(name="Místnost 3", capacity=10)
    user = User(username="limitovany", email="limit@test.cz")
    session.add_all([room1, room2, room3, user])
    session.commit()

    # 1. budoucí rezervace – OK
    payload1 = {
        "room_id": room1.id,
        "user_id": user.id,
        "start_time": "2099-06-01T10:00:00",
        "end_time": "2099-06-01T11:00:00",
        "attendees": 2
    }
    resp1 = client.post("/bookings/", json=payload1)
    assert resp1.status_code == 200

    # 2. budoucí rezervace – OK
    payload2 = {
        "room_id": room2.id,
        "user_id": user.id,
        "start_time": "2099-06-02T10:00:00",
        "end_time": "2099-06-02T11:00:00",
        "attendees": 2
    }
    resp2 = client.post("/bookings/", json=payload2)
    assert resp2.status_code == 200

    # 3. budoucí rezervace – FAIL (limit 2)
    payload3 = {
        "room_id": room3.id,
        "user_id": user.id,
        "start_time": "2099-06-03T10:00:00",
        "end_time": "2099-06-03T11:00:00",
        "attendees": 2
    }
    resp3 = client.post("/bookings/", json=payload3)
    assert resp3.status_code == 400
    assert "too many bookings" in resp3.json()["detail"]