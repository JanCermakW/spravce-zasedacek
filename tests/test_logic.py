import pytest
from app.models import Booking, Room
from datetime import datetime, timedelta
from app.services import BookingService
from unittest.mock import Mock

# ===== validate_capacity =====

def test_cannot_book_room_exceeding_capacity():
    """
    Business Rule: Pokud je počet lidí > kapacita, vyhoď chybu.
    """
    small_room = Room(name="Kumbál", capacity=5)
    
    # Očekáváme, že volání služby vyhodí ValueError s textem "Capacity exceeded"
    with pytest.raises(ValueError, match="Capacity exceeded"):
        BookingService.validate_capacity(room=small_room, attendees=10)

def test_can_book_room_within_capacity():
    """
    Pokud je počet lidí <= kapacita, validace projde.
    """
    room = Room(name="Velká", capacity=10)
    assert BookingService.validate_capacity(room=room, attendees=5) is True

def test_can_book_room_at_exact_capacity():
    """
    Hraniční případ: počet lidí == kapacita – mělo by projít.
    """
    room = Room(name="Přesná", capacity=5)
    assert BookingService.validate_capacity(room=room, attendees=5) is True

# ===== validate_times =====

def test_cannot_book_with_end_before_start():
    """
    Business Rule: Konec rezervace nesmí být před začátkem.
    """
    start = datetime(2025, 1, 1, 10, 0)
    end = datetime(2025, 1, 1, 9, 0) # Chyba: konec je dřív než začátek

    with pytest.raises(ValueError, match="End time must be after start time"):
        BookingService.validate_times(start, end)

def test_cannot_book_with_end_equal_to_start():
    """
    Hraniční případ: konec == začátek – nulová délka, neplatné.
    """
    start = datetime(2025, 1, 1, 10, 0)
    end = datetime(2025, 1, 1, 10, 0)

    with pytest.raises(ValueError, match="End time must be after start time"):
        BookingService.validate_times(start, end)

def test_can_book_with_valid_times():
    """
    Pokud je end_time > start_time, validace projde.
    """
    start = datetime(2025, 1, 1, 10, 0)
    end = datetime(2025, 1, 1, 11, 0)
    assert BookingService.validate_times(start, end) is True

# ===== check_availability =====

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

def test_can_book_when_room_is_free():
    """
    Pokud žádná překrývající se rezervace neexistuje, validace projde.
    """
    mock_session = Mock()
    mock_session.exec.return_value.first.return_value = None

    result = BookingService.check_availability(
        mock_session, room_id=1,
        start_time=datetime(2025, 1, 1, 10, 0),
        end_time=datetime(2025, 1, 1, 11, 0)
    )
    assert result is True

def test_can_book_adjacent_slot():
    """
    Rezervace hned po skončení jiné – nesmí kolidovat.
    Existující: 10:00–11:00, nová: 11:00–12:00.
    """
    mock_session = Mock()
    # DB nevrátí kolizi, protože Booking.end_time (11:00) > start_time (11:00) je false
    mock_session.exec.return_value.first.return_value = None

    result = BookingService.check_availability(
        mock_session, room_id=1,
        start_time=datetime(2025, 1, 1, 11, 0),
        end_time=datetime(2025, 1, 1, 12, 0)
    )
    assert result is True

# ===== validate_working_days =====

def test_cannot_book_on_saturday():
    """Sobota (weekday=5) = ValueError."""
    saturday = datetime(2025, 1, 4, 10, 0)  # Sobota
    with pytest.raises(ValueError, match="weekends"):
        BookingService.validate_working_days(saturday)

def test_cannot_book_on_sunday():
    """Neděle (weekday=6) = ValueError."""
    sunday = datetime(2025, 1, 5, 10, 0)  # Neděle
    with pytest.raises(ValueError, match="weekends"):
        BookingService.validate_working_days(sunday)

def test_can_book_on_monday():
    """Pondělí (weekday=0) = OK."""
    monday = datetime(2025, 1, 6, 10, 0)
    assert BookingService.validate_working_days(monday) is True

def test_can_book_on_friday():
    """Pátek (weekday=4) = OK."""
    friday = datetime(2025, 1, 3, 10, 0)
    assert BookingService.validate_working_days(friday) is True

# ===== validate_user_limit =====

def test_user_limit_exceeded():
    """Uživatel má 2 budoucí rezervace = ValueError."""
    mock_session = Mock()
    mock_session.exec.return_value.one.return_value = 2

    with pytest.raises(ValueError, match="too many bookings"):
        BookingService.validate_user_limit(mock_session, user_id=1)

def test_user_limit_exceeded_more_than_two():
    """Uživatel má 3 budoucí rezervace = ValueError."""
    mock_session = Mock()
    mock_session.exec.return_value.one.return_value = 3

    with pytest.raises(ValueError, match="too many bookings"):
        BookingService.validate_user_limit(mock_session, user_id=1)

def test_user_limit_ok_with_one_booking():
    """Uživatel má 1 budoucí rezervaci = OK."""
    mock_session = Mock()
    mock_session.exec.return_value.one.return_value = 1

    assert BookingService.validate_user_limit(mock_session, user_id=1) is True

def test_user_limit_ok_with_zero_bookings():
    """Uživatel nemá žádné budoucí rezervace = OK."""
    mock_session = Mock()
    mock_session.exec.return_value.one.return_value = 0

    assert BookingService.validate_user_limit(mock_session, user_id=1) is True