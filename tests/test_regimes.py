from horizon.l1_entities.regimes import SkyRegime, classify_regime


def test_regime_thresholds():
    assert classify_regime(12) == SkyRegime.DAY
    assert classify_regime(2) == SkyRegime.LOW_SUN
    assert classify_regime(-3) == SkyRegime.CIVIL
    assert classify_regime(-8) == SkyRegime.NAUTICAL
    assert classify_regime(-15) == SkyRegime.ASTRONOMICAL
    assert classify_regime(-25) == SkyRegime.NIGHT
