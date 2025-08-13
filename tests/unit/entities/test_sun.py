from datetime import UTC, datetime

from horizon.l1_entities import sun_position


def test_sun_basic() -> None:
    # At equator on equinox ~ noon UTC (approx) altitude should be high (~ near zenith)
    dt = datetime(2025, 3, 20, 12, 0, tzinfo=UTC)
    pos = sun_position(dt, 0.0, 0.0)
    assert pos.altitude_deg > 80
