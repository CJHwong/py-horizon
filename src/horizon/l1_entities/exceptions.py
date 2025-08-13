"""Domain-specific exception hierarchy."""


class DomainError(Exception):
    """Base exception for all domain-related errors."""

    pass


class InvalidCoordinatesError(DomainError):
    """Raised when geographic coordinates are invalid or out of range."""

    pass


class AtmosphericCalculationError(DomainError):
    """Raised when atmospheric physics calculations fail."""

    pass


class ColorSpaceError(DomainError):
    """Raised when color space conversions or calculations fail."""

    pass


class SunPositionError(DomainError):
    """Raised when solar position calculations fail."""

    pass


class PreferencesError(DomainError):
    """Raised when preference values are invalid or inconsistent."""

    pass


class WeatherDataError(DomainError):
    """Raised when weather data is invalid or unavailable."""

    pass
