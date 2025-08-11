from datetime import UTC, datetime

from horizon.l1_entities.heuristics import derive


def test_heuristics_deterministic():
    dt = datetime(2025, 8, 11, tzinfo=UTC)
    h1 = derive(40.0, -100.0, dt)
    h2 = derive(40.0, -100.0, dt)
    assert h1 == h2
    assert 2.2 <= h1.turbidity <= 3.0
    assert 0 <= h1.overcast <= 1
    assert 0.35 <= h1.light_pollution <= 0.65
