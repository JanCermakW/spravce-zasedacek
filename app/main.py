from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel import Session
from datetime import datetime
from app.database import create_db_and_tables, get_session
from app.models import Room, Booking, User
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
def create_booking(booking: Booking, session: Session = Depends(get_session)):
    if isinstance(booking.start_time, str):
        booking.start_time = datetime.fromisoformat(booking.start_time)
    if isinstance(booking.end_time, str):
        booking.end_time = datetime.fromisoformat(booking.end_time)
    
    room = session.get(Room, booking.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    user = session.get(User, booking.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        BookingService.validate_booking_attendees(booking.attendees)        # Pravidlo 0 (vstup)
        BookingService.validate_capacity(room, booking.attendees)           # Pravidlo 1
        BookingService.validate_times(booking.start_time, booking.end_time) # Pravidlo 2
        BookingService.validate_working_days(booking.start_time)            # Pravidlo 3 (Víkend)
        BookingService.validate_user_limit(session, booking.user_id)        # Pravidlo 4 (Limit)
        BookingService.check_availability(session, room.id, booking.start_time, booking.end_time) # Pravidlo 5 (Kolize)
        
        session.add(booking)
        session.commit()
        session.refresh(booking)
        return booking

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Pomocný endpoint pro vytvoření místnosti (abychom měli co rezervovat)
@app.post("/rooms/")
def create_room(room: Room, session: Session = Depends(get_session)):
    try:
        BookingService.validate_room_data(room.name, room.capacity)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    session.add(room)
    session.commit()
    session.refresh(room)
    return room


# Pomocný endpoint pro vytvoření uživatele
@app.post("/users/")
def create_user(user: User, session: Session = Depends(get_session)):
    session.add(user)
    session.commit()
    session.refresh(user)
    return user