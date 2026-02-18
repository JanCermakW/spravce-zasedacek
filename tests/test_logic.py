import pytest
from app.models import Room
# Tuto službu za chvíli vytvoříme, zatím neexistuje, ale test už ji očekává
from app.services import BookingService 

def test_cannot_book_room_exceeding_capacity():
    """
    Business Rule: Pokud je počet lidí > kapacita, vyhoď chybu.
    """
    small_room = Room(name="Kumbál", capacity=5)
    
    # Očekáváme, že volání služby vyhodí ValueError s textem "Capacity exceeded"
    with pytest.raises(ValueError, match="Capacity exceeded"):
        BookingService.validate_capacity(room=small_room, attendees=10)