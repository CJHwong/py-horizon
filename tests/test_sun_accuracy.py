from datetime import UTC, datetime

from horizon.l1_entities.sun import sun_position


def test_sun_accuracy_equinox_noon_equator():
    dt = datetime(2025, 3, 20, 12, 0, tzinfo=UTC)
    pos = sun_position(dt, 0.0, 0.0)
    # Simplified algorithm ~<2.5° error acceptable; allow 3° tolerance
    assert abs(pos.altitude_deg - 90) < 3.0
