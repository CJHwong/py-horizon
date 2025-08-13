from horizon.l1_entities import atmospheric_sky_colors


def test_atmospheric_sky_colors_no_overflow_and_in_range() -> None:
    # Sample a range of solar altitudes including extreme twilight values
    for alt in (-90, -30, -10, 0, 10, 30, 60, 85):
        horizon, zenith = atmospheric_sky_colors(alt)
        for c in (horizon, zenith):
            assert 0.0 <= c.r <= 1.0
            assert 0.0 <= c.g <= 1.0
            assert 0.0 <= c.b <= 1.0
