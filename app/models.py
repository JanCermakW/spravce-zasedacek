from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

# === DB entity (tabulky) ===

class Room(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    capacity: int

class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="room.id")
    user_id: int = Field(foreign_key="user.id")
    start_time: datetime
    end_time: datetime
    attendees: int

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str

# === Request schémata (bez id – pro API vstup) ===

class RoomCreate(SQLModel):
    name: str
    capacity: int

class BookingCreate(SQLModel):
    room_id: int
    user_id: int
    start_time: datetime
    end_time: datetime
    attendees: int

class UserCreate(SQLModel):
    username: str
    email: str