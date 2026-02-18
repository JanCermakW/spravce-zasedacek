from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import Session, select
from datetime import datetime
from app.database import create_db_and_tables, get_session
from app.models import Room, Booking, User, RoomCreate, BookingCreate, UserCreate
from app.services import BookingService

app = FastAPI(title="Rezervační Systém", version="1.0.0")

# Při startu aplikace vytvoříme tabulky (pokud neexistují)
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(title="Rezervační Systém", version="1.0.0", lifespan=lifespan)

# Endpoint pro vytvoření rezervace
@app.post("/bookings/")
def create_booking(data: BookingCreate, session: Session = Depends(get_session)):
    room = session.get(Room, data.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    user = session.get(User, data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        BookingService.validate_booking_attendees(data.attendees)        # Pravidlo 0 (vstup)
        BookingService.validate_capacity(room, data.attendees)           # Pravidlo 1
        BookingService.validate_times(data.start_time, data.end_time)    # Pravidlo 2
        BookingService.validate_working_days(data.start_time)            # Pravidlo 3 (Víkend)
        BookingService.validate_user_limit(session, data.user_id)        # Pravidlo 4 (Limit)
        BookingService.check_availability(session, room.id, data.start_time, data.end_time) # Pravidlo 5 (Kolize)
        
        booking = Booking(**data.model_dump())
        session.add(booking)
        session.commit()
        session.refresh(booking)
        return booking

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint pro vytvoření místnosti
@app.post("/rooms/")
def create_room(data: RoomCreate, session: Session = Depends(get_session)):
    try:
        BookingService.validate_room_data(data.name, data.capacity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    room = Room(**data.model_dump())
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


# Endpoint pro vytvoření uživatele
@app.post("/users/")
def create_user(data: UserCreate, session: Session = Depends(get_session)):
    # Kontrola duplicitního emailu
    existing = session.exec(select(User).where(User.email == data.email)).first()
    if existing:
        raise HTTPException(status_code=409, detail="User with this email already exists")
    user = User(**data.model_dump())
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


# === GET endpointy (výpis záznamů) ===

@app.get("/rooms/")
def list_rooms(session: Session = Depends(get_session)):
    """Vrátí seznam všech místností."""
    return session.exec(select(Room)).all()

@app.get("/users/")
def list_users(session: Session = Depends(get_session)):
    """Vrátí seznam všech uživatelů."""
    return session.exec(select(User)).all()

@app.get("/bookings/")
def list_bookings(session: Session = Depends(get_session)):
    """Vrátí seznam všech rezervací."""
    return session.exec(select(Booking)).all()