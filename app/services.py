from datetime import datetime
from app.models import Room

class BookingService:
    
    @staticmethod
    def validate_capacity(room: Room, attendees: int):
        """
        Ověří, zda se účastníci vejdou do místnosti.
        """
        if attendees > room.capacity:
            raise ValueError("Capacity exceeded")
        return True

    @staticmethod
    def validate_times(start_time: datetime, end_time: datetime):
        """
        Ověří, že čas konce je až po čase začátku.
        """
        if end_time <= start_time:
            raise ValueError("End time must be after start time")
        return True