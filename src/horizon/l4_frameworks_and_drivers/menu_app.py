"""Menu bar app wrapper (optional).

`MenuApp.update(vm)` expects a SkyViewModel. If rumps/Cocoa is unavailable
it becomes a no-op collector used in tests or CLI mode.

Implements a gradient icon (horizon→zenith) inside the first menu item using
an NSImage generated on the fly. Status bar title remains simple text 'Sky'.
"""

import re
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import rumps  # type: ignore
from AppKit import (  # type: ignore
    NSBezierPath,
    NSBitmapImageRep,
    NSColor,
    NSGradient,
    NSImage,
    NSMakeRect,
    NSPNGFileType,
)
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from horizon.l2_use_cases.boundaries.prefs_gateway import PreferencesGateway
from horizon.l3_interface_adapters.presenters.sky_presenter import SkyViewModel


class _PrefsFileWatcher(FileSystemEventHandler):
    """Watches prefs.json for changes and triggers callbacks."""

    def __init__(self, prefs_path: Path, on_change: Callable[[], None]):
        self.prefs_path = prefs_path
        self.on_change = on_change

    def on_modified(self, event):
        if not event.is_directory and Path(event.src_path).name == self.prefs_path.name:
            self.on_change()


@dataclass
class _State:
    last_vm: object | None = None  # store latest view model for menu population
    last_grad_key: tuple[str, str] | None = None  # (horizon_hex, zenith_hex)
    grad_path: Path | None = None
    statusbar_grad_path: Path | None = None  # separate path for status bar icon
    last_statusbar_grad_key: tuple[str, str] | None = None  # separate key for status bar
    large: bool = True  # always large per feedback
    file_observer: Observer | None = None  # watchdog observer for prefs.json changes


class MenuApp(rumps.App):
    def __init__(
        self,
        *,
        prefs_gateway: PreferencesGateway | None = None,
        on_prefs_changed: Callable[[], None] | None = None,
        prefs_file_path: Path | None = None,
    ) -> None:
        super().__init__('', title=None)  # No title, will use icon instead
        self._state = _State()
        self._prefs_gateway = prefs_gateway
        self._on_prefs_changed = on_prefs_changed
        self._prefs_file_path = prefs_file_path
        self._influence_items: dict[str, rumps.MenuItem] = {}
        # Primary info items
        self._gradient_item = rumps.MenuItem('')  # icon only
        self._regime_item = rumps.MenuItem('Sky Phase: …')
        self._loc_item = rumps.MenuItem('Location: …')
        self._overcast_item = rumps.MenuItem('Overcast: …')
        self._turbidity_item = rumps.MenuItem('Turbidity: …')
        self._light_pollution_item = rumps.MenuItem('Light Pollution: …')
        self._weather_item = rumps.MenuItem('Weather: No data')
        # Settings submenu (dictionary form)
        quit_item = rumps.MenuItem('Quit', callback=self._on_quit)
        self.menu = [
            self._gradient_item,
            None,
            self._regime_item,
            self._loc_item,
            self._overcast_item,
            self._turbidity_item,
            self._light_pollution_item,
            self._weather_item,
            None,
            *self._build_settings_menu(),
            None,
            quit_item,
        ]

    def _build_settings_menu(self) -> list[rumps.MenuItem | None]:
        if not self._prefs_gateway:
            return []
        p = self._prefs_gateway.load()
        entries = [
            ('Enable Weather Effects', 'influence_weather'),
            ('Enable Air Quality Effects', 'influence_air_quality'),
            ('Enable Light Pollution Effects', 'influence_light_pollution'),
        ]
        items: list[rumps.MenuItem | None] = []
        for label, attr in entries:
            item = rumps.MenuItem(label, callback=self._toggle_attr)
            item.state = 1 if getattr(p, attr, False) else 0
            item._prefs_attr = attr
            items.append(item)
            self._influence_items[attr] = item
        return items

    def _toggle_attr(self, sender: Any) -> None:
        if not self._prefs_gateway:
            return
        p = self._prefs_gateway.load()
        attr = getattr(sender, '_prefs_attr', None)
        if not attr:
            return
        current = bool(getattr(p, attr, False))
        setattr(p, attr, not current)
        self._prefs_gateway.save(p)
        sender.state = 1 if not current else 0
        if self._on_prefs_changed:
            self._on_prefs_changed()

    # --- file watching ---
    def _start_file_watching(self) -> None:
        """Start watching prefs.json for changes."""
        if not self._prefs_file_path or not self._on_prefs_changed:
            return

        if not self._prefs_file_path.exists():
            return

        # Set up file watcher
        event_handler = _PrefsFileWatcher(self._prefs_file_path, self._on_prefs_changed)
        observer = Observer()
        observer.schedule(event_handler, str(self._prefs_file_path.parent), recursive=False)
        observer.start()
        self._state.file_observer = observer

    def _stop_file_watching(self) -> None:
        """Stop file watching."""
        if self._state.file_observer:
            self._state.file_observer.stop()
            self._state.file_observer.join()
            self._state.file_observer = None

    # --- callbacks ---
    def _on_quit(self, _: Any) -> None:
        self._stop_file_watching()
        rumps.quit_application()

    # --- public ---
    def update(self, vm: SkyViewModel) -> None:
        self._state.last_vm = vm
        # Titles
        self._regime_item.title = f'Sky Phase: {vm.regime.title()}'
        self._loc_item.title = f'Location: {vm.lat_deg:.2f}°, {vm.lon_deg:.2f}°'
        self._overcast_item.title = f'Overcast: {vm.overcast:.2f}'
        self._turbidity_item.title = f'Turbidity: {vm.turbidity:.2f}'
        self._light_pollution_item.title = f'Light Pollution: {vm.light_pollution:.2f}'
        weather_bits: list[str] = []
        if getattr(vm, 'temperature_c', None) is not None:
            weather_bits.append(f'{vm.temperature_c:.1f}°C')
        if getattr(vm, 'weather_summary', None):
            weather_bits.append(str(vm.weather_summary))
        if getattr(vm, 'air_quality_index', None) is not None:
            weather_bits.append(f'AQI {vm.air_quality_index}')
        self._weather_item.title = 'Weather: ' + (' • '.join(weather_bits) if weather_bits else 'No data')
        # Gradient icon for menu item
        try:
            key = (vm.horizon_hex, vm.zenith_hex)
            if self._state.last_grad_key != key:
                path = _render_gradient_icon(
                    vm.horizon_hex,
                    vm.zenith_hex,
                    self._state.grad_path,
                    large=True,
                )
                self._state.grad_path = path
                self._state.last_grad_key = key
                dims = (256, 96)
                self._gradient_item.set_icon(str(path), dimensions=dims)
        except Exception:  # pragma: no cover
            pass

        # Status bar gradient icon
        try:
            statusbar_key = (vm.horizon_hex, vm.zenith_hex)
            if self._state.last_statusbar_grad_key != statusbar_key:
                statusbar_path = _render_gradient_icon(
                    vm.horizon_hex,
                    vm.zenith_hex,
                    self._state.statusbar_grad_path,
                    large=False,  # Small for status bar
                )
                self._state.statusbar_grad_path = statusbar_path
                self._state.last_statusbar_grad_key = statusbar_key
                # Set the status bar icon (dimensions for status bar should be small)
                self.icon = str(statusbar_path)
        except Exception:  # pragma: no cover
            pass

    def run(self) -> None:
        self._start_file_watching()
        super().run()


def _hex_to_rgb_f(hex_str: str) -> tuple[float, float, float]:
    m = re.fullmatch(r'#?([0-9a-fA-F]{6})', hex_str.strip())
    if not m:
        return 0.5, 0.5, 0.5
    v = m.group(1)
    r = int(v[0:2], 16) / 255.0
    g = int(v[2:4], 16) / 255.0
    b = int(v[4:6], 16) / 255.0
    return r, g, b


def _render_gradient_icon(
    h_hex: str,
    z_hex: str,
    previous: Path | None,
    *,
    large: bool = False,
) -> Path:  # pragma: no cover - UI specific
    """Render (or reuse) a gradient icon from horizon to zenith.

    large toggles a bigger resolution used when the user clicks the item.
    We include size in the cache key so both sizes can coexist.
    """
    r1, g1, b1 = _hex_to_rgb_f(h_hex)
    r2, g2, b2 = _hex_to_rgb_f(z_hex)
    c1 = NSColor.colorWithCalibratedRed_green_blue_alpha_(r1, g1, b1, 1.0)
    c2 = NSColor.colorWithCalibratedRed_green_blue_alpha_(r2, g2, b2, 1.0)
    grad = NSGradient.alloc().initWithStartingColor_endingColor_(c1, c2)

    # Choose dimensions (match those passed to set_icon for crisp display)
    if large:
        width, height = 256, 96
        padding = 0
        corner_radius = 8
    else:
        width, height = 22, 22  # Square for status bar
        padding = 2
        corner_radius = 4

    img = NSImage.alloc().initWithSize_((width, height))
    img.lockFocus()

    # Create rounded rectangle path with padding
    rect = NSMakeRect(padding, padding, width - 2 * padding, height - 2 * padding)
    path = NSBezierPath.bezierPathWithRoundedRect_xRadius_yRadius_(rect, corner_radius, corner_radius)

    # Clip to the rounded rectangle
    path.addClip()

    # Draw gradient within the clipped area
    grad.drawInRect_angle_(rect, 90.0)

    img.unlockFocus()
    tiff = img.TIFFRepresentation()
    rep = NSBitmapImageRep.imageRepWithData_(tiff)
    png_data = rep.representationUsingType_properties_(NSPNGFileType, None)
    out_path = (
        Path(tempfile.gettempdir()) / f'sky_grad_{"L" if large else "S"}_{abs(hash((h_hex, z_hex))) & 0xFFFFF}.png'
    )
    png_data.writeToFile_atomically_(str(out_path), True)
    return out_path
