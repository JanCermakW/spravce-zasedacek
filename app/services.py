from datetime import datetime
from app.models import Room, Booking
from sqlmodel import Session, select, func

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
    
    @staticmethod
    def check_availability(session: Session, room_id: int, start_time: datetime, end_time: datetime):
        """
        Ověří, zda je místnost v daném čase volná.
        Hledáme jakoukoli rezervaci, která se překrývá s požadovaným časem.
        """
        statement = select(Booking).where(
            Booking.room_id == room_id,
            Booking.start_time < end_time,  
            Booking.end_time > start_time 
        )
        
        results = session.exec(statement)
        #pokud toto něco vrátí, máme kolizi
        existing_booking = results.first()

        if existing_booking:
            raise ValueError("Room is already booked")
        
        return True
    
    @staticmethod
    def validate_working_days(start_time: datetime):
        """Rezervace jsou možné jen Po-Pá (0-4)."""
        if start_time.weekday() >= 5:  # 5=Sobota, 6=Neděle
            raise ValueError("Bookings not allowed on weekends")
        return True

    @staticmethod
    def validate_user_limit(session: Session, user_id: int):
        """Uživatel nesmí mít více než 2 budoucí rezervace."""
        pass