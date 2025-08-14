# py-horizon

A macOS menu bar application that renders dynamic sky gradients using only local data (time + location) and deterministic heuristics.

![horizon_screenshot](https://github.com/user-attachments/assets/3d53a1e2-7d55-4dcf-83e3-6973b85db956)

## Features

- **🌅 Physics-based sky simulation**: Complete single-scattering atmospheric model with realistic color rendering
- **🎨 Real-time gradients**: Smooth color transitions during twilight periods with dynamic scheduling
- **⚙️ Highly configurable**: Fine-grained control over atmospheric effects and update intervals
- **🏗️ Clean Architecture**: Strict layer separation following Clean Architecture principles

## Quick Start

### Installation

#### Using uvx (recommended)

```bash
# Run directly without cloning (one-time computation)
uvx --from git+https://github.com/CJHwong/py-horizon.git py-horizon-once

# Run menu bar app directly
uvx --from git+https://github.com/CJHwong/py-horizon.git py-horizon

# Run menu bar app in background (detached from terminal)
uvx --from git+https://github.com/CJHwong/py-horizon.git py-horizon &

# Or use nohup to run in background and survive terminal close
nohup uvx --from git+https://github.com/CJHwong/py-horizon.git py-horizon > /dev/null 2>&1 &
```

#### Using uv (for development)

```bash
# Clone the repository
git clone https://github.com/CJHwong/py-horizon.git
cd py-horizon

# Install dependencies
uv sync --all-extras

# Run once (prints gradient colors to console)
uv run python -c "import src.main; src.main.run_once()"

# Run menu bar app
uv run python -c "import src.main; src.main.run_loop()"
```

#### Using pip

```bash
# Install for development
pip install -e ".[dev]"

# Run the application
python -c "import src.main; src.main.run_once()"
```

### First Run

On first launch, `py-horizon` will:

1. Create a `prefs.json` configuration file with sensible defaults
2. Detect your approximate location (rounded for privacy)
3. Start computing sky gradients based on current time and solar position

The menu bar will show a colored icon representing the current sky gradient, which updates automatically.

## Usage

### Command Line Scripts

After installation, two console scripts are available:

```bash
# One-time computation (prints colors and exits)
py-horizon-once

# Continuous menu bar mode
py-horizon
```

### Menu Bar Interface

- **Left click**: View current gradient details and regime (DAY, TWILIGHT, NIGHT, etc.)
- **Right click**: Access preferences and quit option
- **Color changes**: Automatic based on solar position and atmospheric conditions

## Configuration

Configuration is stored in `prefs.json` (auto-created on first run):

```json
{
  "update_seconds": 900,
  "location_precision_deg": 0.25,
  "influence_weather": false,
  "influence_air_quality": false
  "influence_light_pollution": false,
}
```

### Key Settings

- **`update_seconds`**: Base refresh interval (automatically reduced to 90s during twilight)
- **`location_precision_deg`**: Privacy rounding granularity (minimum 0.25°)
- **`influence_*`**: Toggle individual atmospheric effects on/off

## Sky Regimes

The application classifies sky conditions into distinct regimes based on solar altitude:

- **DAY**: Sun above 6° altitude - bright blue sky
- **LOW_SUN**: Sun between 0-6° - golden hour colors
- **CIVIL**: Sun 0° to -6° - orange/pink twilight
- **NAUTICAL**: Sun -6° to -12° - deep blue twilight
- **ASTRONOMICAL**: Sun -12° to -18° - dark blue to purple
- **NIGHT**: Sun below -18° - dark sky with possible light pollution

## Architecture

`py-horizon` follows Clean Architecture with strict dependency rules:

### Layer Structure

```text
src/
├── l1_entities/                # Pure domain logic (innermost)
│   ├── sun.py                  # Solar position calculations
│   ├── colors.py               # Color space transformations
│   ├── atmospheric_scattering.py # Physical sky scattering simulation
│   ├── color_effects.py        # Atmospheric effect filters
│   ├── regimes.py              # Sky classification
│   ├── heuristics.py           # Atmospheric parameter derivation
│   └── models.py               # Core data structures
├── l2_use_cases/               # Application workflows
│   ├── compute_sky_use_case.py
│   └── boundaries/             # Protocol interfaces
├── l3_interface_adapters/      # External system adapters
│   ├── gateways/               # Data access implementations
│   └── presenters/             # View model conversion
└── l4_frameworks_and_drivers/  # Platform-specific (outermost)
    ├── menu_app.py             # macOS menu bar UI
    └── scheduler.py            # Dynamic timing system
```

### Dependency Rule

All dependencies point inward. Inner layers never import from outer layers.

## Development

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test
uv run pytest tests/test_atmospheric_scattering.py
```

### Code Quality

```bash
# Linting
uv run ruff check .

# Type checking
uv run mypy src

# Auto-format
uv run ruff check . --fix
```

### Development Setup

The project uses:

- **Python 3.11+**: Required for latest typing features
- **uv**: Fast Python package management
- **pytest**: Testing framework with quiet mode enabled
- **ruff**: Lightning-fast linting and formatting
- **mypy**: Static type checking with strict settings

## Platform Requirements

### macOS

- **rumps**: Required for menu bar functionality
- **pyobjc**: Native macOS integration (installed with rumps)

### Other Platforms

The core sky computation engine works on any platform. Without rumps, the application falls back to CLI mode.

## Inspiration

This project was inspired by [@dnlzro](https://github.com/dnlzro)'s elegant [horizon](https://github.com/dnlzro/horizon) website, originally shared on [Hacker News](https://news.ycombinator.com/item?id=44846281).
