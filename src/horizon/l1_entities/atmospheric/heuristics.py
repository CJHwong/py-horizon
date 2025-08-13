"""Deterministic offline heuristics for turbidity, overcast, light pollution."""

import hashlib
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Heuristics:
    turbidity: float
    overcast: float  # 0 clear .. 1 overcast
    light_pollution: float  # 0 rural .. 1 bright urban


def _seed_value(lat_round: float, lon_round: float, date: datetime) -> float:
    key = f'{date.date().isoformat()}|{lat_round:.2f}|{lon_round:.2f}'.encode()
    h = hashlib.sha256(key).digest()
    # Take first 8 bytes as integer and scale to 0..1
    n = int.from_bytes(h[:8], 'big') / 2**64
    return n


def derive(lat_round: float, lon_round: float, now: datetime) -> Heuristics:
    base = _seed_value(lat_round=lat_round, lon_round=lon_round, date=now)
    turbidity = 2.2 + (base % 0.8)  # 2.2 - 3.0
    overcast = (base * 1.37) % 1.0
    light_pollution = 0.35 + ((base * 0.73) % 0.3)  # 0.35 - 0.65
    return Heuristics(turbidity=turbidity, overcast=overcast, light_pollution=light_pollution)
