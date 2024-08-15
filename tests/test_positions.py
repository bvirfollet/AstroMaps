import pytest
import datetime
import pytz
import json

import AstroMaps  # Import your function

def test_celestial_positions_paris_now():
    # Test with default values (Paris, current time)
    positions = Positions.celestial_positions(datetime.datetime.now(pytz.utc), 48.8566, 2.3522)
    # Add assertions to check the calculated positions
    assert positions is not None

def test_celestial_positions_specific_date_time():
    # Test with a specific date and time
    date_time = datetime.datetime(2024, 12, 25, 0, 0, 0, tzinfo=pytz.utc)
    assert date_time is not None
    positions = celestial_positions(date_time, 40.7128, -74.0060)  # New York
    # Add assertions to check the calculated positions
    assert positions is not None