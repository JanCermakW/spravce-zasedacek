import pytest
from app.models import Booking, Room
from datetime import datetime, timedelta
from app.services import BookingService
from unittest.mock import Mock

def test_cannot_book_room_exceeding_capacity():
    """
    Business Rule: Pokud je počet lidí > kapacita, vyhoď chybu.
    """
    small_room = Room(name="Kumbál", capacity=5)
    
    # Očekáváme, že volání služby vyhodí ValueError s textem "Capacity exceeded"
    with pytest.raises(ValueError, match="Capacity exceeded"):
        BookingService.validate_capacity(room=small_room, attendees=10)

def test_cannot_book_with_end_before_start():
    """
    Business Rule: Konec rezervace nesmí být před začátkem.
    """
    start = datetime(2025, 1, 1, 10, 0)
    end = datetime(2025, 1, 1, 9, 0) # Chyba: konec je dřív než začátek

    with pytest.raises(ValueError, match="End time must be after start time"):
        BookingService.validate_times(start, end)

def test_cannot_book_overlapping_times():
    """
    Business Rule: Rezervace se nesmí překrývat.
    Simulujeme situaci, kdy v DB už něco je.
    """
    room = Room(id=1, name="Zasedačka", capacity=10)
    
    new_start = datetime(2025, 1, 1, 10, 0)
    new_end = datetime(2025, 1, 1, 11, 0)

    mock_session = Mock()
    
   #simulace rezervace v DB, která se překrývá s novou rezervací
    mock_session.exec.return_value.first.return_value = Booking(
        room_id=1, 
        user_name="Pepa", 
        start_time=new_start, 
        end_time=new_end, 
        attendees=5
    )

    with pytest.raises(ValueError, match="Room is already booked"):
        BookingService.check_availability(mock_session, room.id, new_start, new_end)