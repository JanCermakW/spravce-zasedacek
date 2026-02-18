import pytest
from app.models import Room
from datetime import datetime, timedelta
from app.services import BookingService 

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