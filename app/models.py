from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class Room(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    capacity: int

class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    room_id: int = Field(foreign_key="room.id")
    user_name: str
    start_time: datetime
    end_time: datetime
    attendees: int