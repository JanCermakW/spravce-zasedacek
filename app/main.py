from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session
from app.database import create_db_and_tables, get_session
from app.models import Room, Booking
from app.services import BookingService

app = FastAPI(title="Rezervační Systém", version="1.0.0")

# Při startu aplikace vytvoříme tabulky (pokud neexistují)
@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# Endpoint pro vytvoření rezervace
@app.post("/bookings/")
def create_booking(booking: Booking, session: Session = Depends(get_session)):
    
    room = session.get(Room, booking.room_id)
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")

    try:
        BookingService.validate_capacity(room, booking.attendees)
        BookingService.validate_times(booking.start_time, booking.end_time)
        BookingService.check_availability(session, room.id, booking.start_time, booking.end_time)
        
        session.add(booking)
        session.commit()
        session.refresh(booking)
        return booking

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# Pomocný endpoint pro vytvoření místnosti (abychom měli co rezervovat)
@app.post("/rooms/")
def create_room(room: Room, session: Session = Depends(get_session)):
    session.add(room)
    session.commit()
    session.refresh(room)
    return room