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