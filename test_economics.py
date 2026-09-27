import pytest

from app.services.economics import TariffAssumptions, calculate_carbon_footprint, quantify_recommendation, quantify_recommendations

def _tariffs():
    return TariffAssumptions(electricity_toman_per_kwh=5000, gas_toman_per_m3=3000)


def test_quantify_recommendation_produces_positive_payback_for_lighting():
    recommendation = {"category": "lighting", "recommendation": "Replace incandescent lamps with LED", "impact_level": "high"}
    result = quantify_recommendation(
        recommendation, _tariffs(),
        total_energy_mj=50000, electricity_mj=20000, gas_mj=30000,
    )
    assert result["quantified"] is True
    assert result["estimated_annual_savings_toman"] > 0
    assert result["estimated_payback_years_low"] is not None


def test_quantify_recommendation_unknown_category_is_not_quantified():
    recommendation = {"category": "management", "recommendation": "Do a level 2 audit", "impact_level": "medium"}
    result = quantify_recommendation(recommendation, _tariffs(), total_energy_mj=10000, electricity_mj=5000, gas_mj=5000)
    assert result["quantified"] is False


def test_heating_system_savings_uses_gas_tariff_when_gas_present():
    recommendation = {"category": "heating", "recommendation": "Upgrade to condensing boiler", "impact_level": "high"}
    result = quantify_recommendation(
        recommendation, _tariffs(),
        total_energy_mj=50000, electricity_mj=10000, gas_mj=40000,
    )
    assert result["savings_base_source"] == "measured_gas_bill"


def test_carbon_footprint_scales_with_consumption():
    small = calculate_carbon_footprint(1000, 500, _tariffs())
    large = calculate_carbon_footprint(2000, 1000, _tariffs())
    assert large["total_co2_kg"] == pytest.approx(small["total_co2_kg"] * 2)
