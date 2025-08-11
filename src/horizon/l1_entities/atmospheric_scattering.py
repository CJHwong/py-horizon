"""Atmosphere gradient renderer (single scattering) using Python

Physical model and parameter choices derived from "A Scalable and Production
Ready Sky and Atmosphere Rendering Technique" (Sébastien Hillaire).

Implementation derived from "Production Sky Rendering" (Andrew Helmer).
Source: https://www.shadertoy.com/view/slSXRW)
"""

import math

from .colors import Color

# Type alias for Vec3
Vec3 = tuple[float, float, float]

PI = math.pi

# Coefficients of media components (m^-1)
RAYLEIGH_SCATTER = [5.802e-6, 13.558e-6, 33.1e-6]
MIE_SCATTER = 3.996e-6
MIE_ABSORB = 4.44e-6
OZONE_ABSORB = [0.65e-6, 1.881e-6, 0.085e-6]

# Altitude density distribution metrics
RAYLEIGH_SCALE_HEIGHT = 8e3
MIE_SCALE_HEIGHT = 1.2e3

# Additional parameters
GROUND_RADIUS = 6_360e3
TOP_RADIUS = 6_460e3
SUN_INTENSITY = 1.0

# Rendering
SAMPLES = 32  # used for gradient stops and integration steps
FOV_DEG = 75

# Post-processing
EXPOSURE = 25.0
GAMMA = 2.2
SUNSET_BIAS_STRENGTH = 0.1


def clamp(x: float, min_val: float, max_val: float) -> float:
    return max(min_val, min(max_val, x))


def dot(v1: Vec3, v2: Vec3) -> float:
    return v1[0] * v2[0] + v1[1] * v2[1] + v1[2] * v2[2]


def length(v: Vec3) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def norm(v: Vec3) -> Vec3:
    len_val = length(v) or 1.0
    return (v[0] / len_val, v[1] / len_val, v[2] / len_val)


def add(v1: Vec3, v2: Vec3) -> Vec3:
    return (v1[0] + v2[0], v1[1] + v2[1], v1[2] + v2[2])


def scale(v: Vec3, s: float) -> Vec3:
    return (v[0] * s, v[1] * s, v[2] * s)


def exp_vec(v: Vec3) -> Vec3:
    return (math.exp(v[0]), math.exp(v[1]), math.exp(v[2]))


def intersect_sphere(p: Vec3, d: Vec3, r: float) -> float | None:
    """From "5.3.2 Intersecting Ray or Segment Against Sphere" (Real-Time Collision Detection)"""
    # Sphere center is at origin, so M = P - C = P
    m = p
    b = dot(m, d)
    c = dot(m, m) - r * r
    discr = b * b - c
    if discr < 0:
        # Ray misses sphere
        return None
    t = -b - math.sqrt(discr)
    if t < 0:
        # Ray inside sphere; Use far discriminant
        return -b + math.sqrt(discr)
    return t


def compute_transmittance(height: float, angle: float) -> Vec3:
    """Optical depth approximation"""
    ray_origin: Vec3 = (0, GROUND_RADIUS + height, 0)
    ray_direction: Vec3 = (math.sin(angle), math.cos(angle), 0)

    distance = intersect_sphere(ray_origin, ray_direction, TOP_RADIUS)
    if distance is None:
        return (1, 1, 1)

    # March along the ray using a fixed step size
    segment_length = distance / SAMPLES
    t = 0.5 * segment_length

    # Accumulate path-integrated densities
    od_rayleigh = 0.0  # molecules (Rayleigh)
    od_mie = 0.0  # aerosols (Mie)
    od_ozone = 0.0  # ozone (absorption only)

    for i in range(SAMPLES):
        # Position along the ray and its altitude above ground
        pos = add(ray_origin, scale(ray_direction, t))
        h = length(pos) - GROUND_RADIUS

        # Exponential falloff with altitude for Rayleigh and Mie densities
        try:
            d_r = math.exp(-h / RAYLEIGH_SCALE_HEIGHT)
        except OverflowError:
            d_r = 0.0
        try:
            d_m = math.exp(-h / MIE_SCALE_HEIGHT)
        except OverflowError:
            d_m = 0.0

        # Integrate (density × path length)
        od_rayleigh += d_r * segment_length

        # Simple ozone layer: triangular profile centered at 25 km, width 30 km
        ozone_density = 1.0 - min(abs(h - 25e3) / 15e3, 1.0)
        od_ozone += ozone_density * segment_length

        od_mie += d_m * segment_length
        t += segment_length

    # Convert integrated densities into per-channel optical depth (Beer-Lambert)
    tau_r = (
        RAYLEIGH_SCATTER[0] * od_rayleigh,
        RAYLEIGH_SCATTER[1] * od_rayleigh,
        RAYLEIGH_SCATTER[2] * od_rayleigh,
    )
    tau_m = (MIE_ABSORB * od_mie, MIE_ABSORB * od_mie, MIE_ABSORB * od_mie)
    tau_o = (
        OZONE_ABSORB[0] * od_ozone,
        OZONE_ABSORB[1] * od_ozone,
        OZONE_ABSORB[2] * od_ozone,
    )

    # Total optical depth: transmittance T = exp(-tau)
    tau = (
        -(tau_r[0] + tau_m[0] + tau_o[0]),
        -(tau_r[1] + tau_m[1] + tau_o[1]),
        -(tau_r[2] + tau_m[2] + tau_o[2]),
    )
    return exp_vec(tau)


def rayleigh_phase(angle: float) -> float:
    return (3 * (1 + math.cos(angle) ** 2)) / (16 * PI)


def mie_phase(angle: float) -> float:
    g = 0.8
    scale = 3 / (8 * PI)
    num = (1 - g**2) * (1 + math.cos(angle) ** 2)
    denom = (2 + g**2) * (1 + g**2 - 2 * g * math.cos(angle)) ** (3 / 2)
    return (scale * num) / denom


def apply_sunset_bias(color: Vec3) -> Vec3:
    """Enhance sunset hues (i.e., make warmer)"""
    r, g, b = color
    # Relative luminance (sRGB)
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    # Weight is higher for darker sky (near horizon/twilight), lower midday
    w = 1.0 / (1.0 + 2.0 * lum)
    k = SUNSET_BIAS_STRENGTH  # overall strength
    rb = 1.0 + 0.5 * k * w  # boost red
    gb = 1.0 - 0.5 * k * w  # suppress green
    bb = 1.0 + 1.0 * k * w  # boost blue
    return (max(0, r * rb), max(0, g * gb), max(0, b * bb))


def aces(color: Vec3) -> Vec3:
    """ACES tonemapper (Knarkowicz)"""
    result = []
    for c in color:
        n = c * (2.51 * c + 0.03)
        d = c * (2.43 * c + 0.59) + 0.14
        result.append(max(0, min(1, n / d)))
    return (result[0], result[1], result[2])


def render_gradient(altitude: float) -> tuple[str, Vec3, Vec3]:
    """Render sky at given solar elevation"""
    camera_position: Vec3 = (0, GROUND_RADIUS, 0)
    sun_direction: Vec3 = norm((math.cos(altitude), math.sin(altitude), 0))

    # Projection constant (used to tilt rays upward)
    focal_z = 1.0 / math.tan((FOV_DEG * 0.5 * PI) / 180.0)

    stops: list[tuple[float, Vec3]] = []  # (percent, rgb)

    for i in range(SAMPLES):
        s = i / (SAMPLES - 1)

        view_direction = norm((0, s, focal_z))

        inscattered: Vec3 = (0, 0, 0)

        t_exit_top = intersect_sphere(camera_position, view_direction, TOP_RADIUS)
        if t_exit_top is not None and t_exit_top > 0:
            ray_origin = camera_position

            # Fixed-step integration along the valid path segment
            segment_length = t_exit_top / SAMPLES
            t_ray = segment_length * 0.5

            # Precompute camera-to-space transmittance and the direction polarity
            ray_origin_radius = length(ray_origin)
            is_ray_pointing_downward_at_start = dot(ray_origin, view_direction) / ray_origin_radius < 0.0
            start_height = ray_origin_radius - GROUND_RADIUS
            start_ray_cos = clamp(
                dot(
                    (
                        ray_origin[0] / ray_origin_radius,
                        ray_origin[1] / ray_origin_radius,
                        ray_origin[2] / ray_origin_radius,
                    ),
                    view_direction,
                ),
                -1,
                1,
            )
            start_ray_angle = math.acos(abs(start_ray_cos))
            transmittance_camera_to_space = compute_transmittance(start_height, start_ray_angle)

            for j in range(SAMPLES):
                # Position and local frame
                sample_pos = add(ray_origin, scale(view_direction, t_ray))
                sample_radius = length(sample_pos)
                up_unit: Vec3 = (
                    sample_pos[0] / sample_radius,
                    sample_pos[1] / sample_radius,
                    sample_pos[2] / sample_radius,
                )
                sample_height = sample_radius - GROUND_RADIUS

                # Angles for view ray and sun relative to local up
                view_cos = clamp(dot(up_unit, view_direction), -1, 1)
                sun_cos = clamp(dot(up_unit, sun_direction), -1, 1)
                view_angle = math.acos(abs(view_cos))
                sun_angle = math.acos(sun_cos)

                # Transmittance camera→sample and sample→space
                transmittance_to_space = compute_transmittance(sample_height, view_angle)
                transmittance_camera_to_sample = [0.0, 0.0, 0.0]
                for k in range(3):
                    if is_ray_pointing_downward_at_start:
                        transmittance_camera_to_sample[k] = transmittance_to_space[k] / transmittance_camera_to_space[k]
                    else:
                        transmittance_camera_to_sample[k] = transmittance_camera_to_space[k] / transmittance_to_space[k]

                # Transmittance from sample toward the sun
                transmittance_light = compute_transmittance(sample_height, sun_angle)

                # Local densities and phase functions
                try:
                    optical_density_ray = math.exp(-sample_height / RAYLEIGH_SCALE_HEIGHT)
                except OverflowError:
                    optical_density_ray = 0.0
                try:
                    optical_density_mie = math.exp(-sample_height / MIE_SCALE_HEIGHT)
                except OverflowError:
                    optical_density_mie = 0.0
                sun_view_cos = clamp(dot(sun_direction, view_direction), -1, 1)
                sun_view_angle = math.acos(sun_view_cos)
                phase_r = rayleigh_phase(sun_view_angle)
                phase_m = mie_phase(sun_view_angle)

                # Single-scattering contribution
                scattered_rgb = [0.0, 0.0, 0.0]
                for k in range(3):
                    rayleigh_term = RAYLEIGH_SCATTER[k] * optical_density_ray * phase_r
                    mie_term = MIE_SCATTER * optical_density_mie * phase_m
                    scattered_rgb[k] = transmittance_light[k] * (rayleigh_term + mie_term)

                # Accumulate along the ray
                inscattered_list = list(inscattered)
                for k in range(3):
                    inscattered_list[k] += transmittance_camera_to_sample[k] * scattered_rgb[k] * segment_length
                inscattered = (inscattered_list[0], inscattered_list[1], inscattered_list[2])
                t_ray += segment_length

            inscattered = scale(inscattered, SUN_INTENSITY)

        # Post-process: exposure → gentle sunset bias → ACES tonemap → gamma → 8-bit RGB
        color = inscattered
        color = scale(color, EXPOSURE)
        color = apply_sunset_bias(color)
        color = aces(color)
        color = (color[0] ** (1.0 / GAMMA), color[1] ** (1.0 / GAMMA), color[2] ** (1.0 / GAMMA))
        rgb = (
            round(clamp(color[0], 0, 1) * 255),
            round(clamp(color[1], 0, 1) * 255),
            round(clamp(color[2], 0, 1) * 255),
        )

        # 0% at zenith (top), 100% at horizon (bottom)
        percent = (1 - s) * 100
        stops.append((percent, rgb))

    # Compose CSS gradient string from the ordered stops
    stops.sort(key=lambda x: x[0])
    color_stops = ', '.join(
        f'rgb({rgb[0]}, {rgb[1]}, {rgb[2]}) {round(percent * 100) / 100}%' for percent, rgb in stops
    )

    return (
        f'linear-gradient(to bottom, {color_stops})',
        stops[0][1],
        stops[len(stops) - 1][1],
    )


def atmospheric_sky_colors(sun_altitude_deg: float) -> tuple[Color, Color]:
    """Return (horizon_color, zenith_color) using atmospheric scattering.

    Colors are linear RGB (0..1) to integrate with existing pipeline.
    """
    alt_rad = math.radians(sun_altitude_deg)
    gradient_css, zenith_rgb, horizon_rgb = render_gradient(alt_rad)

    # Convert from 8-bit RGB to linear RGB (0..1)
    horizon_linear = (horizon_rgb[0] / 255.0, horizon_rgb[1] / 255.0, horizon_rgb[2] / 255.0)
    zenith_linear = (zenith_rgb[0] / 255.0, zenith_rgb[1] / 255.0, zenith_rgb[2] / 255.0)

    # Apply gamma correction to get linear RGB
    horizon_linear = (horizon_linear[0] ** GAMMA, horizon_linear[1] ** GAMMA, horizon_linear[2] ** GAMMA)
    zenith_linear = (zenith_linear[0] ** GAMMA, zenith_linear[1] ** GAMMA, zenith_linear[2] ** GAMMA)

    return Color(*horizon_linear).clamp(), Color(*zenith_linear).clamp()


__all__ = ['atmospheric_sky_colors', 'render_gradient', 'clamp', 'dot', 'length', 'norm', 'add', 'scale', 'exp_vec']
