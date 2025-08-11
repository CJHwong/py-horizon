"""Color data structures & helpers (linear RGB ops)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Color:
    r: float
    g: float
    b: float

    def clamp(self) -> Color:
        return Color(*(max(0.0, min(1.0, c)) for c in (self.r, self.g, self.b)))

    def lerp(self, other: Color, t: float) -> Color:
        return Color(
            self.r + (other.r - self.r) * t,
            self.g + (other.g - self.g) * t,
            self.b + (other.b - self.b) * t,
        )

    def desaturate(self, factor: float) -> Color:
        # simple luminance-based desaturation
        lum = 0.2126 * self.r + 0.7152 * self.g + 0.0722 * self.b
        return Color(
            self.r + (lum - self.r) * factor,
            self.g + (lum - self.g) * factor,
            self.b + (lum - self.b) * factor,
        )

    def to_srgb_hex(self) -> str:
        def conv(x: float) -> int:
            # simple gamma 2.2 approximation
            g = max(0.0, min(1.0, x)) ** (1 / 2.2)
            return int(round(g * 255))

        return f'#{conv(self.r):02X}{conv(self.g):02X}{conv(self.b):02X}'


def hex_color(r: int, g: int, b: int) -> Color:
    return Color(r / 255.0, g / 255.0, b / 255.0)
