"""JSON implementation of preferences gateway."""

import json
from pathlib import Path
from typing import Any

from horizon.l2_use_cases.boundaries.prefs_gateway import Preferences, PreferencesGateway


class JsonPreferencesGateway(PreferencesGateway):
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> Preferences:
        if not self.path.exists():
            prefs = Preferences()
            self.save(prefs)
            return prefs
        with self.path.open('r', encoding='utf-8') as f:
            data = json.load(f)
        location = data.get('location')
        return Preferences(
            lat=location.get('lat') if location else None,
            lon=location.get('lon') if location else None,
            update_seconds=data.get('update_seconds', 900),
            location_precision_deg=data.get('location_precision_deg', 0.25),
            exact_time=data.get('exact_time'),
            influence_light_pollution=data.get('influence_light_pollution', True),
            influence_weather=data.get('influence_weather', True),
            influence_air_quality=data.get('influence_air_quality', True),
        )

    def save(self, prefs: Preferences) -> None:
        data: dict[str, Any] = {
            'update_seconds': prefs.update_seconds,
            'location_precision_deg': prefs.location_precision_deg,
            'influence_light_pollution': prefs.influence_light_pollution,
            'influence_weather': prefs.influence_weather,
            'influence_air_quality': prefs.influence_air_quality,
        }
        if prefs.exact_time is not None:
            data['exact_time'] = prefs.exact_time
        if prefs.lat is not None and prefs.lon is not None:
            data['location'] = {'lat': prefs.lat, 'lon': prefs.lon}
        self.path.write_text(json.dumps(data, indent=2), encoding='utf-8')
