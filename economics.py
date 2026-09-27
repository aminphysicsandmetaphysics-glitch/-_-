"""Turns qualitative recommendations into numbers a homeowner or investor
can act on: estimated annual energy savings, an approximate cost range,
simple payback, and avoided CO2.

Savings percentages below are typical published ranges for residential
retrofits (e.g. roof insulation cutting combined heating+cooling energy by
roughly a third; see building-science literature on Iranian residential
stock), not a substitute for a metered before/after comparison. Cost
ranges are placeholders in Toman that the operator should calibrate to
current local contractor quotes before showing a client -- they are kept
as explicit, editable settings for exactly that reason rather than
hard-coded "fake-precise" numbers.
"""

from dataclasses import dataclass

MJ_PER_KWH = 3.6
MJ_PER_M3_GAS = 38.0

# (low, mid, high) fractional savings applied to the *relevant* energy base
# for each recommendation category -- see `_savings_base` for which base
# applies to which category.
SAVINGS_FRACTION_RANGES: dict[str, tuple[float, float, float]] = {
    "envelope_window": (0.08, 0.12, 0.18),
    "envelope_insulation": (0.15, 0.25, 0.35),
    "lighting": (0.55, 0.70, 0.85),
    "heating_system": (0.10, 0.18, 0.28),
    "cooling_system": (0.20, 0.30, 0.40),
    "thermostat": (0.05, 0.08, 0.12),
    "shading": (0.06, 0.10, 0.15),
}

# Placeholder installed-cost ranges in Toman -- deliberately explicit
# so they are easy to find and update from `Settings`, not buried in code.
DEFAULT_COST_RANGES_TOMAN: dict[str, tuple[int, int]] = {
    "envelope_window": (25_000_000, 60_000_000),
    "envelope_insulation": (15_000_000, 40_000_000),
    "lighting": (2_000_000, 6_000_000),
    "heating_system": (30_000_000, 90_000_000),
    "cooling_system": (20_000_000, 60_000_000),
    "thermostat": (3_000_000, 8_000_000),
    "shading": (5_000_000, 15_000_000),
}


@dataclass
class TariffAssumptions:
    electricity_toman_per_kwh: float
    gas_toman_per_m3: float
    grid_emission_factor_kg_co2_per_kwh: float = 0.5
    gas_emission_factor_kg_co2_per_m3: float = 2.0


def _category_for_recommendation(category: str, recommendation_text: str) -> str:
    text = recommendation_text.lower()
    if category == "envelope":
        if "window" in text or "glaz" in text or "پنجره" in recommendation_text:
            return "envelope_window"
        return "envelope_insulation"
    if category == "lighting":
        return "lighting"
    if category == "heating":
        if "thermostat" in text or "ترموستات" in recommendation_text:
            return "thermostat"
        return "heating_system"
    if category == "cooling":
        return "cooling_system"
    return category


def _savings_base_mj(
    quantified_category: str,
    total_energy_mj: float,
    electricity_mj: float,
    gas_mj: float,
    theoretical_heating_mj: float | None,
    theoretical_cooling_mj: float | None,
    electric_equipment: list[dict] | None,
) -> tuple[float, str]:
    """Pick the most specific energy base available for a category, and
    report whether it came from measured equipment data, the physics-based
    envelope model, or a coarse fallback share of the total bill -- so the
    UI can show its own confidence level next to the number."""
    equipment = electric_equipment or []

    if quantified_category == "heating_system":
        if gas_mj > 0:
            return gas_mj, "measured_gas_bill"
        if theoretical_heating_mj:
            return theoretical_heating_mj, "theoretical_envelope_model"
        return total_energy_mj * 0.5, "assumed_share_of_total"

    if quantified_category in ("envelope_insulation", "envelope_window", "thermostat"):
        if theoretical_heating_mj is not None and theoretical_cooling_mj is not None:
            return theoretical_heating_mj + theoretical_cooling_mj, "theoretical_envelope_model"
        return total_energy_mj * 0.6, "assumed_share_of_total"

    if quantified_category == "cooling_system" or quantified_category == "shading":
        cooling_items = [item for item in equipment if (item.get("category") or "").lower() == "cooling"]
        if cooling_items:
            return sum(item.get("annual_kwh", 0) for item in cooling_items) * MJ_PER_KWH, "measured_equipment_list"
        if theoretical_cooling_mj:
            return theoretical_cooling_mj, "theoretical_envelope_model"
        return electricity_mj * 0.35, "assumed_share_of_total"

    if quantified_category == "lighting":
        lighting_items = [item for item in equipment if (item.get("category") or "").lower() == "lighting"]
        if lighting_items:
            return sum(item.get("annual_kwh", 0) for item in lighting_items) * MJ_PER_KWH, "measured_equipment_list"
        return electricity_mj * 0.12, "assumed_share_of_total"

    return total_energy_mj * 0.1, "assumed_share_of_total"


def quantify_recommendation(
    recommendation: dict,
    tariffs: TariffAssumptions,
    total_energy_mj: float,
    electricity_mj: float,
    gas_mj: float,
    theoretical_heating_mj: float | None = None,
    theoretical_cooling_mj: float | None = None,
    electric_equipment: list[dict] | None = None,
    cost_ranges: dict[str, tuple[int, int]] | None = None,
) -> dict:
    quantified_category = _category_for_recommendation(recommendation["category"], recommendation["recommendation"])
    savings_fractions = SAVINGS_FRACTION_RANGES.get(quantified_category)
    if not savings_fractions:
        return {**recommendation, "quantified": False}

    base_mj, base_source = _savings_base_mj(
        quantified_category, total_energy_mj, electricity_mj, gas_mj,
        theoretical_heating_mj, theoretical_cooling_mj, electric_equipment,
    )
    low, mid, high = savings_fractions
    savings_mj_mid = base_mj * mid

    # Split back into electricity/gas terms for cost calculation: envelope
    # and cooling/lighting measures save electricity-equivalent energy;
    # heating-system measures save gas (falls back to electricity-equivalent
    # if the home has no gas bill, e.g. all-electric heating).
    if quantified_category == "heating_system" and gas_mj > 0:
        savings_toman = (savings_mj_mid / MJ_PER_M3_GAS) * tariffs.gas_toman_per_m3
        savings_co2_kg = (savings_mj_mid / MJ_PER_M3_GAS) * tariffs.gas_emission_factor_kg_co2_per_m3
    else:
        savings_toman = (savings_mj_mid / MJ_PER_KWH) * tariffs.electricity_toman_per_kwh
        savings_co2_kg = (savings_mj_mid / MJ_PER_KWH) * tariffs.grid_emission_factor_kg_co2_per_kwh

    cost_low, cost_high = (cost_ranges or DEFAULT_COST_RANGES_TOMAN).get(
        quantified_category, DEFAULT_COST_RANGES_TOMAN.get(quantified_category, (10_000_000, 30_000_000))
    )
    payback_low = (cost_low / savings_toman) if savings_toman > 0 else None
    payback_high = (cost_high / savings_toman) if savings_toman > 0 else None

    return {
        **recommendation,
        "quantified": True,
        "estimated_savings_fraction_low": low,
        "estimated_savings_fraction_mid": mid,
        "estimated_savings_fraction_high": high,
        "estimated_annual_savings_mj": round(savings_mj_mid, 1),
        "estimated_annual_savings_toman": round(savings_toman),
        "estimated_annual_co2_avoided_kg": round(savings_co2_kg, 1),
        "estimated_cost_toman_low": cost_low,
        "estimated_cost_toman_high": cost_high,
        "estimated_payback_years_low": round(payback_low, 1) if payback_low else None,
        "estimated_payback_years_high": round(payback_high, 1) if payback_high else None,
        "savings_base_source": base_source,
    }


def quantify_recommendations(
    recommendations: list[dict],
    tariffs: TariffAssumptions,
    total_energy_mj: float,
    electricity_mj: float,
    gas_mj: float,
    theoretical_heating_mj: float | None = None,
    theoretical_cooling_mj: float | None = None,
    electric_equipment: list[dict] | None = None,
) -> list[dict]:
    return [
        quantify_recommendation(
            item, tariffs, total_energy_mj, electricity_mj, gas_mj,
            theoretical_heating_mj, theoretical_cooling_mj, electric_equipment,
        )
        for item in recommendations
    ]


def quantify_sensitivity_item(
    item: dict,
    tariffs: TariffAssumptions,
    has_gas_heating: bool,
    cost_ranges: dict[str, tuple[int, int]] | None = None,
) -> dict:
    """Attach Toman/CO2/payback figures to a physics-based sensitivity
    result (see ``sensitivity.rank_envelope_sensitivity``), splitting the
    heating-side savings onto the gas tariff when the home heats with gas
    and onto electricity otherwise, and the cooling-side savings onto
    electricity (residential cooling in Iran is overwhelmingly electric)."""
    heating_mj = item.get("heating_savings_mj", 0)
    cooling_mj = item.get("cooling_savings_mj", 0)

    if has_gas_heating:
        heating_toman = (heating_mj / MJ_PER_M3_GAS) * tariffs.gas_toman_per_m3
        heating_co2 = (heating_mj / MJ_PER_M3_GAS) * tariffs.gas_emission_factor_kg_co2_per_m3
    else:
        heating_toman = (heating_mj / MJ_PER_KWH) * tariffs.electricity_toman_per_kwh
        heating_co2 = (heating_mj / MJ_PER_KWH) * tariffs.grid_emission_factor_kg_co2_per_kwh

    cooling_toman = (cooling_mj / MJ_PER_KWH) * tariffs.electricity_toman_per_kwh
    cooling_co2 = (cooling_mj / MJ_PER_KWH) * tariffs.grid_emission_factor_kg_co2_per_kwh

    savings_toman = heating_toman + cooling_toman
    savings_co2 = heating_co2 + cooling_co2

    quantified_category = "envelope_window" if item["parameter"] == "window_material_key" else "envelope_insulation"
    cost_low, cost_high = (cost_ranges or DEFAULT_COST_RANGES_TOMAN).get(quantified_category, (10_000_000, 30_000_000))
    payback_low = (cost_low / savings_toman) if savings_toman > 0 else None
    payback_high = (cost_high / savings_toman) if savings_toman > 0 else None

    return {
        **item,
        "quantified": True,
        "estimated_annual_savings_toman": round(savings_toman),
        "estimated_annual_co2_avoided_kg": round(savings_co2, 1),
        "estimated_cost_toman_low": cost_low,
        "estimated_cost_toman_high": cost_high,
        "estimated_payback_years_low": round(payback_low, 1) if payback_low else None,
        "estimated_payback_years_high": round(payback_high, 1) if payback_high else None,
        "savings_base_source": "theoretical_envelope_model",
    }


def calculate_carbon_footprint(electricity_kwh: float, gas_m3: float, tariffs: TariffAssumptions) -> dict:
    electricity_kg = electricity_kwh * tariffs.grid_emission_factor_kg_co2_per_kwh
    gas_kg = gas_m3 * tariffs.gas_emission_factor_kg_co2_per_m3
    return {
        "electricity_co2_kg": round(electricity_kg, 1),
        "gas_co2_kg": round(gas_kg, 1),
        "total_co2_kg": round(electricity_kg + gas_kg, 1),
        "total_co2_tonnes": round((electricity_kg + gas_kg) / 1000, 2),
    }
