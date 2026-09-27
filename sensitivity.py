"""Per-building parameter sensitivity ranking.

Rather than asserting a generic, one-size-fits-all "roof matters most"
rule, this module answers the question precisely for the audited home: it
recomputes the physics-based theoretical demand (``thermal.py``) once per
envelope component with that one component swapped for a realistic
upgraded option, holding everything else fixed (a standard local/one-at-a-
time sensitivity analysis), and reports the resulting MJ saved. Sorting by
that delta gives a building-specific, quantified "fix this first" ranking
-- the actual answer depends on this building's areas, existing materials,
and climate (HDD/CDD), which is exactly why it has to be computed per
building rather than looked up from a table.
"""

from dataclasses import replace

from app.services.thermal import EnvelopeInputs, estimate_theoretical_demand

# The upgrade target used for each component when testing "what if this
# were improved" -- deliberately the realistic *better* catalog option for
# that category, not a fantasy ideal, so the reported savings are
# achievable with normal retrofit materials.
UPGRADE_TARGETS = {
    "wall_material_key": "wall_aac_block_insulated",
    "roof_material_key": "roof_flat_insulated",
    "floor_material_key": "floor_slab_on_grade_insulated",
    "window_material_key": "window_double_lowe_upvc",
}

RECOMMENDATION_TEXT = {
    "wall_material_key": "Insulate/upgrade exterior walls. | عایق‌کاری یا ارتقای دیوار خارجی",
    "roof_material_key": "Insulate the roof (largest exposed surface, frequently the top opportunity in flat-roof Iranian homes). | عایق‌کاری سقف",
    "floor_material_key": "Insulate the ground-contact floor/slab. | عایق‌کاری کف در تماس با زمین",
    "window_material_key": "Replace windows with low-E double glazing. | تعویض پنجره‌ها با دوجداره کم‌گسیل",
    "airtightness": "Seal air leaks (weatherstripping, sealing gaps) to reduce infiltration. | آب‌بندی درزها و کاهش نفوذ هوا",
}


def rank_envelope_sensitivity(base_inputs: EnvelopeInputs, hdd: float, cdd: float) -> list[dict]:
    baseline = estimate_theoretical_demand(base_inputs, hdd, cdd)
    baseline_total = baseline["theoretical_total_mj"]
    if baseline_total <= 0:
        return []

    def _deltas(candidate_inputs: EnvelopeInputs) -> tuple[float, float, float]:
        upgraded = estimate_theoretical_demand(candidate_inputs, hdd, cdd)
        heating_delta = baseline["theoretical_heating_mj"] - upgraded["theoretical_heating_mj"]
        cooling_delta = baseline["theoretical_cooling_mj"] - upgraded["theoretical_cooling_mj"]
        return heating_delta, cooling_delta, heating_delta + cooling_delta

    results = []
    for field_name, upgraded_key in UPGRADE_TARGETS.items():
        current_key = getattr(base_inputs, field_name)
        if current_key == upgraded_key:
            continue  # already at (or past) the upgrade target -- no opportunity here
        candidate_inputs = replace(base_inputs, **{field_name: upgraded_key})
        heating_delta, cooling_delta, total_delta = _deltas(candidate_inputs)
        if total_delta <= 0:
            continue
        results.append({
            "category": "envelope",
            "parameter": field_name,
            "recommendation": RECOMMENDATION_TEXT[field_name],
            "impact_level": "high" if total_delta / baseline_total > 0.10 else "medium",
            "estimated_annual_savings_mj": round(total_delta, 1),
            "heating_savings_mj": round(max(heating_delta, 0), 1),
            "cooling_savings_mj": round(max(cooling_delta, 0), 1),
            "estimated_savings_share_of_theoretical_demand": round(total_delta / baseline_total, 3),
            "precision": "physics_based_comparison",
        })

    if base_inputs.airtightness != "tight":
        tight_inputs = replace(base_inputs, airtightness="tight")
        heating_delta, cooling_delta, total_delta = _deltas(tight_inputs)
        if total_delta > 0:
            results.append({
                "category": "envelope",
                "parameter": "airtightness",
                "recommendation": RECOMMENDATION_TEXT["airtightness"],
                "impact_level": "high" if total_delta / baseline_total > 0.10 else "medium",
                "estimated_annual_savings_mj": round(total_delta, 1),
                "heating_savings_mj": round(max(heating_delta, 0), 1),
                "cooling_savings_mj": round(max(cooling_delta, 0), 1),
                "estimated_savings_share_of_theoretical_demand": round(total_delta / baseline_total, 3),
                "precision": "physics_based_comparison",
            })

    return sorted(results, key=lambda item: item["estimated_annual_savings_mj"], reverse=True)
