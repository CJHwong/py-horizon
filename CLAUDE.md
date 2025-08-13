# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"py-horizon" is an offline-first macOS menu bar application that renders dynamic sky gradients using only local data (time + location) and deterministic heuristics. No API keys required for core functionality. The project follows Clean Architecture principles with strict layer separation and includes a sophisticated physical sky scattering simulation.

## Development Commands

### Core Commands (uv)

```bash
# Run the application (one-time computation, prints gradient colors)
uv run py-horizon-once

# Run the application (continuous menu bar mode)
uv run py-horizon

# Run tests
uv run pytest

# Linting and type checking
uv run ruff check .
uv run mypy src  # Note: Some type annotations need fixing

# Install dependencies (including dev tools)
uv sync --all-extras
```

### Testing

- Single test: `uv run pytest tests/test_<module>.py`
- Test with coverage: `uv run pytest --cov=src`
- All tests use pytest with `-q` flag (configured in pyproject.toml)

## Architecture Overview

The codebase strictly follows Clean Architecture with four layers:

### L1 Entities (`src/horizon/l1_entities/`)

Pure domain logic and mathematical computations, organized into sub-modules:

- `geo/sun.py`: Solar position calculations (NOAA algorithms)
- `color/colors.py`: Color space transformations and gradient generation
- `color/color_effects.py`: Color transformation and gradient effects
- `core/regimes.py`: Sky classification by sun altitude (DAY, LOW_SUN, CIVIL, NAUTICAL, ASTRONOMICAL, NIGHT)
- `atmospheric/heuristics.py`: Atmospheric parameter derivation (turbidity, overcast, light pollution)
- `atmospheric/atmospheric_scattering.py`: Physical single-scattering atmospheric simulation engine
- `core/models.py`: Core data structures (`SkySnapshot`, coordinate utilities)
- `exceptions.py`: Domain-specific exceptions

### L2 Use Cases (`src/horizon/l2_use_cases/`)

Application workflows and business rules:

- `compute_sky_use_case.py`: Main interactor orchestrating sky computation
- `boundaries/`: Protocol interfaces for external dependencies (location, weather, preferences, presenter)

### L3 Interface Adapters (`src/horizon/l3_interface_adapters/`)

Transform between use cases and external concerns:

- `presenters/sky_presenter.py`: Converts domain models to view models with hex colors
- `gateways/json_prefs_gateway.py`: JSON preferences file adapter
- `gateways/cached_location_gateway.py`: Location service with caching and privacy rounding
- `gateways/ip_location_gateway.py`: IP-based location fallback
- `gateways/open_meteo_weather_gateway.py`: Optional weather integration (no API key)

### L4 Frameworks & Drivers (`src/horizon/l4_frameworks_and_drivers/`)

Platform-specific implementations:

- `menu_app.py`: macOS menu bar UI using rumps/pyobjc
- `scheduler.py`: Dynamic timing for smooth twilight transitions

### Application Entry Points

- `src/horizon/main.py`: Application composition root and entry points
- `src/horizon/container.py`: Dependency injection container
- `src/horizon/app_orchestrator.py`: Application orchestration and lifecycle management

### Dependency Rule

Inner layers never import from outer layers. All dependencies point inward toward entities.

## Configuration

### Preferences (`prefs.json`)

Auto-created on first run. Key settings:

- `default_location`: Fallback coordinates when location unavailable
- `update_seconds`: Base refresh interval (dynamically adjusted during twilight)
- `location_precision_deg`: Privacy rounding granularity (minimum 0.25°)
- `influence_*`: Fine-grained toggles for atmospheric effects (overcast, turbidity, light_pollution, weather, air_quality)

## Key Patterns

### Physical Sky Simulation

The `atmospheric_scattering.py` module contains a complete single-scattering atmospheric simulation that computes realistic sky colors based on:

- Solar position and viewing angle
- Atmospheric turbidity and overcast conditions
- Rayleigh and Mie scattering physics
- Air quality and light pollution effects

### Weather Integration

Weather is optional and pluggable via `WeatherProviderGateway` protocol. When disabled, uses purely deterministic heuristics. Open-Meteo provides free API without keys.

### Location Privacy

- Coordinates rounded to configurable precision (default 0.25°)
- Never transmitted over network
- Cached locally with periodic refresh
- Fallback hierarchy: IP location → user default → hardcoded baseline

### Dynamic Scheduling

Update frequency automatically adjusts:

- Normal: 15 minutes (900s)
- Twilight periods: 90 seconds (for smooth color transitions)

### Testing Strategy

- Pure functions extensively tested with known inputs/outputs
- Integration tests verify full pipeline without external dependencies
- Physics accuracy tests validate solar calculations
- Comprehensive test coverage across all architectural layers

## Test Structure

```
tests/
├── unit/                        # Unit tests for individual components
│   ├── entities/
│   │   ├── test_atmospheric_scattering.py # Physical sky model testing
│   │   ├── test_heuristics.py            # Atmospheric parameter testing
│   │   ├── test_regimes.py               # Sky regime classification testing
│   │   ├── test_sun.py                   # Solar position testing
│   │   └── test_sun_accuracy.py          # Solar calculation accuracy testing
│   ├── adapters/
│   │   └── test_location_service.py      # Location service testing
│   ├── frameworks/               # Framework-specific unit tests
│   └── use_cases/                # Use case unit tests
└── integration/                  # Integration and end-to-end tests
    ├── test_influence_toggles.py # Feature toggle testing
    └── test_pipeline.py          # End-to-end integration testing
```

## Common Development Patterns

### Adding New Atmospheric Effects

1. Add computation to `src/horizon/l1_entities/atmospheric/heuristics.py` (pure function)
2. Wire through `SkySnapshot` model if persistent state needed
3. Update `src/horizon/l2_use_cases/compute_sky_use_case.py` interactor
4. Add influence toggle to preferences if configurable
5. Tests in `tests/unit/entities/test_heuristics.py`

### Adding New Data Sources

1. Define protocol in `src/horizon/l2_use_cases/boundaries/`
2. Implement concrete gateway in `src/horizon/l3_interface_adapters/gateways/`
3. Wire in `src/horizon/main.py` composition root via `src/horizon/container.py`
4. Add feature toggle to preferences if optional

### Color Space Work

All color math happens in linear RGB space (`src/horizon/l1_entities/color/colors.py`) with sRGB conversion only at display boundaries. This ensures proper gradient interpolation and atmospheric effect blending. Color effects and transformations are handled in `src/horizon/l1_entities/color/color_effects.py`.

### Physical Sky Modifications

The `src/horizon/l1_entities/atmospheric/atmospheric_scattering.py` module provides the core atmospheric physics. Modifications should:

1. Maintain physical accuracy of scattering equations
2. Preserve performance for real-time computation
3. Add comprehensive tests in `tests/unit/entities/test_atmospheric_scattering.py`
4. Document any new physical constants or approximations
