"""
Advanced astrophysics computations powered by Astropy.

This module derives research-grade quantities for an exoplanet system from the
catalogue parameters we store: habitable-zone boundaries (Kopparapu et al.
2014), instellation flux, equilibrium temperature, Earth Similarity Index,
surface gravity / escape velocity, galactic coordinates, transit depth, radial
velocity semi-amplitude and the host star's blackbody peak.

Everything degrades gracefully: if an input is missing, the dependent output is
returned as ``None`` with the rest still computed.
"""

from __future__ import annotations

from typing import Any, Optional
import math

import numpy as np
import astropy.units as u
from astropy.constants import G, sigma_sb, M_earth, R_earth, M_sun, R_sun, L_sun, b_wien
from astropy.coordinates import SkyCoord

from app.models.exoplanet import Exoplanet


# --- Reference constants (Earth) for the ESI ----------------------------------
ESI_REF = {
    # value, weight  (Schulze-Makuch et al. 2011)
    "radius": (1.0, 0.57),          # R_earth
    "density": (5.51, 1.07),        # g/cm^3
    "escape_velocity": (11.186, 0.70),  # km/s
    "surface_temp": (288.0, 5.58),  # K
}

# Kopparapu et al. (2014) coefficients for the 1 Earth-mass case.
# Each: (S_eff_sun, a, b, c, d). Valid for T_eff in [2600, 7200] K.
_KOPPARAPU = {
    "recent_venus": (1.776, 2.136e-4, 2.533e-8, -1.332e-11, -3.097e-15),
    "runaway_greenhouse": (1.107, 1.332e-4, 1.580e-8, -8.308e-12, -1.931e-15),
    "maximum_greenhouse": (0.356, 6.171e-5, 1.698e-9, -3.198e-12, -5.575e-16),
    "early_mars": (0.320, 5.547e-5, 1.526e-9, -2.874e-12, -5.011e-16),
}


def _round(v: Optional[float], n: int = 4) -> Optional[float]:
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return None
    return float(np.round(v, n))


def _luminosity_solar(ep: Exoplanet) -> Optional[float]:
    """Stellar luminosity in L_sun. Uses the stored value, else Stefan-Boltzmann."""
    if ep.stellar_luminosity_solar is not None:
        # NASA stores log10(L/L_sun); typical range makes small values a giveaway.
        val = ep.stellar_luminosity_solar
        # Heuristic: NASA `st_lum` is log-solar. Values in [-6, 6] are logs.
        return float(10 ** val) if -6 <= val <= 6 else float(val)
    if ep.stellar_radius_solar and ep.stellar_temp_k:
        r = ep.stellar_radius_solar * R_sun
        t = ep.stellar_temp_k * u.K
        lum = (4 * math.pi * r**2 * sigma_sb * t**4).to(u.W)
        return float((lum / L_sun).decompose().value)
    return None


def _seff(coeffs: tuple, teff: float) -> float:
    s0, a, b, c, d = coeffs
    t = teff - 5780.0
    return s0 + a * t + b * t**2 + c * t**3 + d * t**4


def habitable_zone(ep: Exoplanet, lum_solar: Optional[float]) -> dict[str, Any]:
    """Kopparapu (2014) HZ edges in AU and the planet's position within them."""
    teff = ep.stellar_temp_k
    if teff is None or lum_solar is None:
        return {"available": False, "reason": "Missing stellar temperature or luminosity"}
    teff_clamped = min(max(teff, 2600.0), 7200.0)

    edges = {}
    for name, coeffs in _KOPPARAPU.items():
        seff = _seff(coeffs, teff_clamped)
        edges[name] = math.sqrt(lum_solar / seff)  # AU

    a = ep.semi_major_axis_au
    position = None
    in_conservative = None
    in_optimistic = None
    if a is not None:
        in_conservative = edges["runaway_greenhouse"] >= a >= edges["maximum_greenhouse"]
        in_optimistic = edges["recent_venus"] >= a >= edges["early_mars"]
        span = edges["maximum_greenhouse"] - edges["runaway_greenhouse"]
        position = (a - edges["runaway_greenhouse"]) / span if span else None

    return {
        "available": True,
        "teff_used_k": _round(teff_clamped, 1),
        "optimistic_inner_au": _round(edges["recent_venus"], 4),
        "conservative_inner_au": _round(edges["runaway_greenhouse"], 4),
        "conservative_outer_au": _round(edges["maximum_greenhouse"], 4),
        "optimistic_outer_au": _round(edges["early_mars"], 4),
        "planet_semi_major_axis_au": _round(a, 4) if a else None,
        "in_conservative_hz": in_conservative,
        "in_optimistic_hz": in_optimistic,
        "relative_position": _round(position, 3) if position is not None else None,
        "reference": "Kopparapu et al. (2014), 1 M⊕ coefficients",
    }


def energy_budget(ep: Exoplanet, lum_solar: Optional[float]) -> dict[str, Any]:
    """Instellation flux (S⊕) and equilibrium temperature for a few albedos."""
    a = ep.semi_major_axis_au
    out: dict[str, Any] = {"available": False}
    if lum_solar is not None and a:
        s = lum_solar / (a**2)  # in units of Earth's insolation (S/S_earth)
        out["instellation_earth_flux"] = _round(s, 3)
        out["instellation_w_m2"] = _round(s * 1361.0, 1)  # solar constant
        out["available"] = True

    # Equilibrium temperature: Teq = Teff * sqrt(Rstar / 2a) * (1-A)^0.25
    if ep.stellar_temp_k and ep.stellar_radius_solar and a:
        rstar = (ep.stellar_radius_solar * R_sun).to(u.au).value
        base = ep.stellar_temp_k * math.sqrt(rstar / (2 * a))
        out["equilibrium_temp_bond0_k"] = _round(base, 1)                  # A=0
        out["equilibrium_temp_bond0_3_k"] = _round(base * (0.7) ** 0.25, 1)  # A=0.3 (Earth-like)
        out["equilibrium_temp_bond0_7_k"] = _round(base * (0.3) ** 0.25, 1)  # A=0.7 (Venus-like)
        out["catalog_equilibrium_temp_k"] = _round(ep.equilibrium_temp_k, 1)
        out["available"] = True
    return out


def planet_physics(ep: Exoplanet) -> dict[str, Any]:
    """Bulk density, surface gravity and escape velocity from mass & radius."""
    out: dict[str, Any] = {}
    m = ep.planet_mass_earth
    r = ep.planet_radius_earth

    if m and r:
        gravity_g = m / (r**2)  # in Earth g
        out["surface_gravity_g"] = _round(gravity_g, 3)
        out["surface_gravity_ms2"] = _round(gravity_g * 9.80665, 2)
        out["escape_velocity_kms"] = _round(11.186 * math.sqrt(m / r), 2)

    if ep.planet_density_g_cm3:
        out["density_g_cm3"] = _round(ep.planet_density_g_cm3, 3)
    elif m and r:
        mass = (m * M_earth).to(u.g)
        radius = (r * R_earth).to(u.cm)
        vol = (4 / 3) * math.pi * radius**3
        out["density_g_cm3"] = _round((mass / vol).value, 3)

    return out


def earth_similarity_index(ep: Exoplanet, physics: dict[str, Any]) -> dict[str, Any]:
    """Multi-parameter Earth Similarity Index (Schulze-Makuch et al. 2011)."""
    values = {
        "radius": ep.planet_radius_earth,
        "density": physics.get("density_g_cm3"),
        "escape_velocity": physics.get("escape_velocity_kms"),
        "surface_temp": ep.equilibrium_temp_k,
    }
    terms = {}
    product = 1.0
    total_weight = 0.0
    used = 0
    for key, (ref, weight) in ESI_REF.items():
        x = values.get(key)
        if x is None or (x + ref) == 0:
            continue
        term = (1 - abs((x - ref) / (x + ref))) ** (weight / 4.0)
        terms[key] = _round(term, 3)
        product *= term
        total_weight += weight
        used += 1
    if used == 0:
        return {"available": False}
    # Global ESI as the weighted geometric mean of the available terms.
    esi = product ** (4.0 / total_weight) if total_weight else None
    return {
        "available": True,
        "esi": _round(esi, 3),
        "components": terms,
        "parameters_used": used,
        "reference": "Schulze-Makuch et al. (2011)",
    }


def galactic_position(ep: Exoplanet) -> dict[str, Any]:
    """Transform ICRS (RA/Dec) to Galactic coordinates; distance in light-years."""
    if ep.ra_deg is None or ep.dec_deg is None:
        return {"available": False}
    coord = SkyCoord(ra=ep.ra_deg * u.deg, dec=ep.dec_deg * u.deg, frame="icrs")
    gal = coord.galactic
    out = {
        "available": True,
        "ra_deg": _round(ep.ra_deg, 4),
        "dec_deg": _round(ep.dec_deg, 4),
        "galactic_longitude_deg": _round(float(gal.l.deg), 3),
        "galactic_latitude_deg": _round(float(gal.b.deg), 3),
    }
    if ep.distance_pc:
        out["distance_pc"] = _round(ep.distance_pc, 2)
        out["distance_light_years"] = _round(ep.distance_pc * 3.26156, 1)
    return out


def observability(ep: Exoplanet) -> dict[str, Any]:
    """Transit depth and radial-velocity semi-amplitude — how we detect it."""
    out: dict[str, Any] = {}

    # Transit depth = (Rp / Rstar)^2
    if ep.planet_radius_earth and ep.stellar_radius_solar:
        rp = (ep.planet_radius_earth * R_earth).to(u.m).value
        rs = (ep.stellar_radius_solar * R_sun).to(u.m).value
        depth = (rp / rs) ** 2
        out["transit_depth_ppm"] = _round(depth * 1e6, 1)
        out["transit_depth_percent"] = _round(depth * 100, 4)

    # Radial velocity semi-amplitude K (m/s)
    if (
        ep.planet_mass_earth
        and ep.stellar_mass_solar
        and ep.orbital_period_days
    ):
        P = (ep.orbital_period_days * u.day).to(u.s)
        mp = (ep.planet_mass_earth * M_earth)
        ms = (ep.stellar_mass_solar * M_sun)
        e = ep.eccentricity or 0.0
        inc = math.radians(ep.inclination_deg) if ep.inclination_deg else math.pi / 2
        try:
            k = (
                (2 * math.pi * G / P) ** (1 / 3)
                * (mp * math.sin(inc))
                / (ms + mp) ** (2 / 3)
                / math.sqrt(max(1 - e**2, 1e-9))
            ).to(u.m / u.s)
            out["rv_semi_amplitude_ms"] = _round(float(k.value), 3)
        except Exception:
            pass

    # Orbital velocity (circular approximation)
    if ep.stellar_mass_solar and ep.semi_major_axis_au:
        a = (ep.semi_major_axis_au * u.au).to(u.m)
        ms = (ep.stellar_mass_solar * M_sun)
        v = math.sqrt((G * ms / a).to((u.m / u.s) ** 2).value)
        out["orbital_velocity_kms"] = _round(v / 1000.0, 2)

    return out


def stellar_light(ep: Exoplanet) -> dict[str, Any]:
    """Blackbody peak wavelength (Wien) and an approximate visible colour."""
    if not ep.stellar_temp_k:
        return {"available": False}
    teff = ep.stellar_temp_k
    peak = (b_wien / (teff * u.K)).to(u.nm).value
    if teff >= 30000:
        color = "blue"
    elif teff >= 10000:
        color = "blue-white"
    elif teff >= 7500:
        color = "white"
    elif teff >= 6000:
        color = "yellow-white"
    elif teff >= 5200:
        color = "yellow"
    elif teff >= 3700:
        color = "orange"
    else:
        color = "red"
    return {
        "available": True,
        "effective_temp_k": _round(teff, 1),
        "wien_peak_nm": _round(peak, 1),
        "approx_color": color,
    }


def compute_all(ep: Exoplanet) -> dict[str, Any]:
    """Full astrophysics report for a single exoplanet."""
    lum = _luminosity_solar(ep)
    physics = planet_physics(ep)
    return {
        "exoplanet_id": ep.id,
        "exoplanet_name": ep.name,
        "host_star": ep.host_star,
        "stellar_luminosity_solar": _round(lum, 5) if lum is not None else None,
        "habitable_zone": habitable_zone(ep, lum),
        "energy_budget": energy_budget(ep, lum),
        "planet_physics": physics,
        "earth_similarity_index": earth_similarity_index(ep, physics),
        "galactic_position": galactic_position(ep),
        "observability": observability(ep),
        "stellar_light": stellar_light(ep),
        "disclaimer": (
            "Derived with Astropy from catalogue parameters. Habitable-zone edges "
            "follow Kopparapu et al. (2014); ESI follows Schulze-Makuch et al. (2011). "
            "These are model estimates, not measurements."
        ),
    }
