from app.services.sensitivity import rank_envelope_sensitivity
from app.services.thermal import EnvelopeInputs, calculate_heat_loss_coefficient, compare_theoretical_to_billed, estimate_theoretical_demand


def test_insulated_envelope_has_lower_heat_loss_coefficient_than_uninsulated():
    uninsulated = EnvelopeInputs(footprint_area_m2=100, floors=1, wall_material_key="wall_brick_single_wythe", roof_material_key="roof_flat_uninsulated", airtightness="leaky")
    insulated = EnvelopeInputs(footprint_area_m2=100, floors=1, wall_material_key="wall_aac_block_insulated", roof_material_key="roof_flat_insulated", airtightness="tight")

    h_uninsulated = calculate_heat_loss_coefficient(uninsulated)["h_total_w_k"]
    h_insulated = calculate_heat_loss_coefficient(insulated)["h_total_w_k"]

    assert h_insulated < h_uninsulated


def test_theoretical_demand_scales_with_degree_days():
    inputs = EnvelopeInputs(footprint_area_m2=100, floors=1)
    low_hdd = estimate_theoretical_demand(inputs, hdd=500, cdd=200)
    high_hdd = estimate_theoretical_demand(inputs, hdd=3000, cdd=200)
    assert high_hdd["theoretical_heating_mj"] > low_hdd["theoretical_heating_mj"]


def test_compare_theoretical_to_billed_diagnoses_consistent_case():
    comparison = compare_theoretical_to_billed(theoretical_heating_mj=1000, billed_heating_mj=1050)
    assert comparison["diagnosis"] == "consistent"


def test_compare_theoretical_to_billed_flags_large_gap():
    comparison = compare_theoretical_to_billed(theoretical_heating_mj=1000, billed_heating_mj=2500)
    assert comparison["diagnosis"] == "envelope_or_system"


def test_sensitivity_ranks_uninsulated_home_with_real_opportunities():
    poor_envelope = EnvelopeInputs(
        footprint_area_m2=120,
        floors=1,
        wall_material_key="wall_brick_single_wythe",
        roof_material_key="roof_flat_uninsulated",
        window_material_key="window_single_aluminum",
        airtightness="leaky",
    )
    ranked = rank_envelope_sensitivity(poor_envelope, hdd=2500, cdd=800)
    assert len(ranked) > 0
    # Results must be sorted descending by savings.
    savings = [item["estimated_annual_savings_mj"] for item in ranked]
    assert savings == sorted(savings, reverse=True)
    # An already-well-insulated home should show few/no further opportunities
    # for the components already at the upgrade target.
    good_envelope = EnvelopeInputs(
        footprint_area_m2=120,
        floors=1,
        wall_material_key="wall_aac_block_insulated",
        roof_material_key="roof_flat_insulated",
        window_material_key="window_double_lowe_upvc",
        floor_material_key="floor_slab_on_grade_insulated",
        airtightness="tight",
    )
    ranked_good = rank_envelope_sensitivity(good_envelope, hdd=2500, cdd=800)
    assert len(ranked_good) == 0
