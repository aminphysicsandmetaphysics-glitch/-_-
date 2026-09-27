"""First-principles building-envelope heat balance engine.

This module implements the static UA / degree-day method (the same family
of simplified steady-state methods used by ISO 13790's monthly method and
most prescriptive national energy codes, مبحث ۱۹ included) to estimate the
*theoretical* annual heating and cooling energy demand of a building from
its physical description -- independent of what the utility bills say.

Why this matters: the existing analytics engine (``analytics.py``) only
benchmarks *billed* energy against a reference EUI. That tells you a home
is a high consumer, but not *why*. This module adds the missing physics
layer so the audit can separate two very different problems:

* envelope losses (bad walls/roof/windows/infiltration) -- theoretical
  demand is high
* system/operational inefficiency (old boiler, high setpoint, leaks in
  ductwork) -- theoretical demand is normal/low but billed energy is high
  anyway

Heat balance
------------
Steady-state heat loss coefficient (W/K):

    H_transmission = sum(U_i * A_i)              # walls + roof + floor + windows
    H_infiltration = 0.34 * ACH * Volume          # 0.34 Wh/(m3.K): volumetric heat
                                                    # capacity of air per hour
    H_total = H_transmission + H_infiltration

Annual conductive/infiltration energy exchange from degree-days:

    E_heating_kWh = H_total * HDD * 24 / 1000
    E_cooling_kWh = H_total * CDD * 24 / 1000 - solar/internal gain offset

These are intentionally simple, transparent, and auditable -- exactly the
level of rigor expected from a Level 1/2 walkthrough+utility-bill audit.
A full dynamic hourly simulation is out of scope and would not be more
trustworthy without much more site-measured input data.
"""

from dataclasses import dataclass

from app.services.catalogs import get_u_value

AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K = 0.34  # Wh/(m3.K), standard air constant
DEFAULT_FLOOR_HEIGHT_M = 3.0
DEFAULT_WINDOW_TO_WALL_RATIO = 0.15
DEFAULT_SOLAR_HEAT_GAIN_COEFFICIENT = 0.6  # unshaded ordinary double glazing
DEFAULT_INTERNAL_GAIN_W_M2 = 4.0  # occupants + appliances, offsets cooling/heating slightly

# Air changes per hour by qualitative airtightness class. These map to the
# building's declared insulation/age status when the user has not measured
# blower-door ACH directly (the normal situation for a residential audit).
ACH_BY_TIGHTNESS = {
    "leaky": 1.2,     # older building, no weatherstripping, single glazing
    "medium": 0.8,    # typical existing Iranian residential stock
    "tight": 0.5,     # insulated envelope + modern windows + weatherstripping
}


@dataclass
class EnvelopeInputs:
    footprint_area_m2: float
    floors: int = 1
    wall_area_m2: float | None = None
    roof_area_m2: float | None = None
    floor_area_m2: float | None = None
    window_area_m2: float | None = None
    wall_u_value: float | None = None
    roof_u_value: float | None = None
    floor_u_value: float | None = None
    window_u_value: float | None = None
    wall_material_key: str | None = None
    roof_material_key: str | None = None
    floor_material_key: str | None = None
    window_material_key: str | None = None
    airtightness: str = "medium"
    has_shading: bool = False


def estimate_geometry(inputs: EnvelopeInputs) -> dict:
    """Fill in envelope areas that were not explicitly measured, from the
    footprint area and a typical residential window-to-wall ratio. All
    estimates can be overridden by explicit user input at any time."""
    floors = max(inputs.floors or 1, 1)
    perimeter_estimate = 4 * (inputs.footprint_area_m2 / floors) ** 0.5
    gross_wall_area = perimeter_estimate * DEFAULT_FLOOR_HEIGHT_M * floors
    window_area = inputs.window_area_m2 if inputs.window_area_m2 is not None else gross_wall_area * DEFAULT_WINDOW_TO_WALL_RATIO
    wall_area = inputs.wall_area_m2 if inputs.wall_area_m2 is not None else max(gross_wall_area - window_area, 0)
    roof_area = inputs.roof_area_m2 if inputs.roof_area_m2 is not None else inputs.footprint_area_m2 / floors
    floor_area = inputs.floor_area_m2 if inputs.floor_area_m2 is not None else inputs.footprint_area_m2 / floors
    volume = inputs.footprint_area_m2 * DEFAULT_FLOOR_HEIGHT_M
    return {
        "wall_area_m2": wall_area,
        "roof_area_m2": roof_area,
        "floor_area_m2": floor_area,
        "window_area_m2": window_area,
        "volume_m3": volume,
        "estimated": {
            "wall_area_m2": inputs.wall_area_m2 is None,
            "roof_area_m2": inputs.roof_area_m2 is None,
            "floor_area_m2": inputs.floor_area_m2 is None,
            "window_area_m2": inputs.window_area_m2 is None,
        },
    }


def resolve_u_values(inputs: EnvelopeInputs) -> dict:
    return {
        "wall": inputs.wall_u_value if inputs.wall_u_value is not None else get_u_value(inputs.wall_material_key, 1.5),
        "roof": inputs.roof_u_value if inputs.roof_u_value is not None else get_u_value(inputs.roof_material_key, 1.8),
        "floor": inputs.floor_u_value if inputs.floor_u_value is not None else get_u_value(inputs.floor_material_key, 0.9),
        "window": inputs.window_u_value if inputs.window_u_value is not None else get_u_value(inputs.window_material_key, 4.5),
    }


def calculate_heat_loss_coefficient(inputs: EnvelopeInputs) -> dict:
    geometry = estimate_geometry(inputs)
    u_values = resolve_u_values(inputs)
    h_wall = u_values["wall"] * geometry["wall_area_m2"]
    h_roof = u_values["roof"] * geometry["roof_area_m2"]
    h_floor = u_values["floor"] * geometry["floor_area_m2"]
    h_window = u_values["window"] * geometry["window_area_m2"]
    h_transmission = h_wall + h_roof + h_floor + h_window
    ach = ACH_BY_TIGHTNESS.get(inputs.airtightness, ACH_BY_TIGHTNESS["medium"])
    h_infiltration = AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K * ach * geometry["volume_m3"]
    h_total = h_transmission + h_infiltration
    return {
        "geometry": geometry,
        "u_values": u_values,
        "ach": ach,
        "h_wall_w_k": h_wall,
        "h_roof_w_k": h_roof,
        "h_floor_w_k": h_floor,
        "h_window_w_k": h_window,
        "h_transmission_w_k": h_transmission,
        "h_infiltration_w_k": h_infiltration,
        "h_total_w_k": h_total,
    }


def estimate_theoretical_demand(
    inputs: EnvelopeInputs,
    hdd: float,
    cdd: float,
) -> dict:
    """Estimate theoretical annual heating/cooling energy demand (MJ) from
    the envelope heat-loss coefficient and degree-days, independent of any
    metered bill. This is the physics-based cross-check against
    ``analytics.build_audit_result``'s bill-based EUI."""
    breakdown = calculate_heat_loss_coefficient(inputs)
    h_total = breakdown["h_total_w_k"]

    heating_kwh = h_total * hdd * 24 / 1000
    raw_cooling_kwh = h_total * cdd * 24 / 1000

    # Solar and internal gains reduce net heating need and add to cooling
    # load; applied as a simple constant offset rather than an hourly
    # simulation, consistent with the static degree-day method.
    window_area = breakdown["geometry"]["window_area_m2"]
    shading_factor = 0.6 if inputs.has_shading else 1.0
    solar_gain_kwh = (
        window_area * DEFAULT_SOLAR_HEAT_GAIN_COEFFICIENT * shading_factor * cdd * 24 / 1000 * 0.15
    )
    cooling_kwh = max(raw_cooling_kwh + solar_gain_kwh, 0)

    heating_mj = heating_kwh * 3.6
    cooling_mj = cooling_kwh * 3.6

    return {
        "breakdown": breakdown,
        "theoretical_heating_mj": heating_mj,
        "theoretical_cooling_mj": cooling_mj,
        "theoretical_total_mj": heating_mj + cooling_mj,
    }


def compare_theoretical_to_billed(theoretical_heating_mj: float, billed_heating_mj: float) -> dict:
    """Flag whether the gap between physics-based demand and the metered
    heating energy points at the envelope or at the heating system/usage
    pattern. Returned as a diagnostic hint, not a certified diagnosis --
    both estimates carry uncertainty."""
    if theoretical_heating_mj <= 0:
        return {"ratio": None, "diagnosis": "insufficient_data"}
    ratio = billed_heating_mj / theoretical_heating_mj
    if ratio <= 1.15:
        diagnosis = "consistent"  # billed use roughly matches physics-based demand
    elif ratio <= 1.6:
        diagnosis = "system_or_operation"  # plausible envelope, likely inefficient system/usage
    else:
        diagnosis = "envelope_or_system"  # gap too large to attribute confidently; inspect both
    return {"ratio": ratio, "diagnosis": diagnosis}
