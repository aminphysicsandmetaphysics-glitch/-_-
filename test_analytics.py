from datetime import date

from app.services import analytics


def _sample_bills():
    # 12 months, a clear winter/summer swing so HDD/CDD-driven variation is
    # realistic rather than flat -- this matters for the regression test.
    winter_kwh = [900, 850, 700, 400, 250, 200, 220, 230, 260, 450, 700, 880]
    return [
        {"year": 2025, "month": month, "electricity_kwh": kwh, "gas_m3": 250 if month in (11, 12, 1, 2) else 40}
        for month, kwh in zip(list(range(1, 13)), winter_kwh)
    ]


def _sample_weather():
    rows = []
    # roughly sinusoidal monthly mean temps for a moderate-cold climate
    month_temps = {1: -2, 2: 1, 3: 8, 4: 15, 5: 21, 6: 28, 7: 32, 8: 30, 9: 24, 10: 16, 11: 7, 12: 0}
    for month, temp in month_temps.items():
        for day in (5, 15, 25):
            rows.append({"date": date(2025, month, day), "temp_avg": temp, "temp_min": temp - 5, "temp_max": temp + 5, "humidity": 40})
    return rows


def test_convert_to_mj_uses_correct_factors():
    result = analytics.convert_to_mj(100, 10)
    assert result["electricity_mj"] == 360
    assert result["gas_mj"] == 380
    assert result["total_mj"] == 740


def test_classify_energy_label_by_ratio_bounds():
    assert analytics.classify_energy_label_by_ratio(100, 200)["rating"] == "A"  # ratio 0.5
    assert analytics.classify_energy_label_by_ratio(190, 200)["rating"] == "C"  # ratio 0.95
    assert analytics.classify_energy_label_by_ratio(400, 200)["rating"] == "E"  # ratio 2.0


def test_no_dead_absolute_rating_function_remains():
    # Regression test for the fixed bug: the unused, wrongly-scaled
    # classify_energy_rating() must not reappear.
    assert not hasattr(analytics, "classify_energy_rating")


def test_build_audit_result_end_to_end_shapes():
    result = analytics.build_audit_result(
        bills=_sample_bills(),
        weather_rows=_sample_weather(),
        area_m2=120,
        occupants=4,
        climate_zone="cold",
    )
    assert result["eui"] > 0
    assert result["hdd"] > 0 and result["cdd"] > 0
    assert result["energy_rating"] in {"A", "B", "C", "D", "E"}
    assert len(result["monthly"]) == 12
    assert 0 <= result["performance_score"] <= 100
    assert result["confidence"]["confidence_level"] in {"low", "medium", "high"}
    # With a clear winter/summer swing and 12 matched months, the
    # energy-signature regression should have fit successfully.
    assert result["energy_signature"] is not None
    assert result["energy_signature"]["r_squared"] > 0.5


def test_weather_normalized_anomalies_dont_flag_expected_winter_peak():
    result = analytics.build_audit_result(
        bills=_sample_bills(),
        weather_rows=_sample_weather(),
        area_m2=120,
        occupants=4,
        climate_zone="cold",
    )
    # January/December are cold and gas-heavy by construction, but that is
    # *expected* given the weather -- the regression-based detector should
    # not flag every winter month as an anomaly the way a flat-average
    # comparison would have.
    flagged_months = {item["month"] for item in result["anomalies"]}
    assert flagged_months != {1, 2, 11, 12, 6, 7}  # not just "everything far from the mean"


def test_fallback_anomaly_detection_without_weather():
    result = analytics.build_audit_result(
        bills=_sample_bills(),
        weather_rows=[],
        area_m2=120,
        occupants=4,
    )
    assert result["energy_signature"] is None
    assert result["hdd"] == 0 and result["cdd"] == 0
