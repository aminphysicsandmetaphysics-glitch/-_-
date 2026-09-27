from dataclasses import dataclass

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

from app.services.regression import fit_energy_signature
from app.services.scoring import calculate_confidence, calculate_performance_score

ELECTRICITY_KWH_TO_MJ = 3.6
IRAN_NATURAL_GAS_M3_TO_MJ = 38.0
DEFAULT_STANDARD_EUI = 324.0

CLIMATE_E2_DEFAULTS = {
    "very_cold": 430.0,
    "cold": 390.0,
    "moderate_dry": 324.0,
    "moderate_humid": 340.0,
    "hot_dry": 360.0,
    "hot_humid": 410.0,
    "mild": 300.0,
    "coastal": 380.0,
}

ENERGY_LABEL_RANGES = [
    {"rating": "A", "min_ratio": 0.0, "max_ratio": 0.6, "label": "Excellent / عالی"},
    {"rating": "B", "min_ratio": 0.6, "max_ratio": 0.8, "label": "Very good / بسیار خوب"},
    {"rating": "C", "min_ratio": 0.8, "max_ratio": 1.0, "label": "Standard / استاندارد"},
    {"rating": "D", "min_ratio": 1.0, "max_ratio": 1.2, "label": "Moderate / متوسط"},
    {"rating": "E", "min_ratio": 1.2, "max_ratio": 999.0, "label": "High consumption / پرمصرف"},
]


@dataclass
class RecommendationRuleInput:
    window_type: str | None = None
    lighting_type: str | None = None
    heating_system: str | None = None
    cooling_system: str | None = None
    has_thermostat: bool = False
    has_insulation: bool = False
    has_shading: bool = False
    orientation: str | None = None


def convert_to_mj(electricity_kwh: float, gas_m3: float) -> dict[str, float]:
    electricity_mj = electricity_kwh * ELECTRICITY_KWH_TO_MJ
    gas_mj = gas_m3 * IRAN_NATURAL_GAS_M3_TO_MJ
    return {"electricity_mj": electricity_mj, "gas_mj": gas_mj, "total_mj": electricity_mj + gas_mj}


def calculate_monthly_energy(bills: list[dict], area_m2: float, occupants: int) -> list[dict]:
    monthly = []
    for bill in sorted(bills, key=lambda item: item["month"]):
        converted = convert_to_mj(bill.get("electricity_kwh", 0), bill.get("gas_m3", 0))
        monthly.append({
            "month": bill["month"],
            "electricity_kwh": bill.get("electricity_kwh", 0),
            "gas_m3": bill.get("gas_m3", 0),
            "electricity_mj": converted["electricity_mj"],
            "gas_mj": converted["gas_mj"],
            "total_mj": converted["total_mj"],
            "energy_per_m2": converted["total_mj"] / area_m2,
            "energy_per_person": converted["total_mj"] / occupants,
        })
    return monthly


def calculate_annual_energy(monthly_energy: list[dict]) -> float:
    return sum(item["total_mj"] for item in monthly_energy)


def calculate_eui(annual_energy_mj: float, building_area_m2: float) -> float:
    if building_area_m2 <= 0:
        raise ValueError("building_area_m2 must be greater than zero")
    return annual_energy_mj / building_area_m2


def calculate_energy_per_person(annual_energy_mj: float, occupants: int) -> float:
    if occupants <= 0:
        raise ValueError("occupants must be greater than zero")
    return annual_energy_mj / occupants


def calculate_hdd_cdd(weather_rows: list[dict], base_temp: float = 18.0) -> tuple[float, float]:
    if not weather_rows:
        return 0.0, 0.0
    if pd is None:
        hdd = sum(max(base_temp - row["temp_avg"], 0) for row in weather_rows)
        cdd = sum(max(row["temp_avg"] - base_temp, 0) for row in weather_rows)
        return float(hdd), float(cdd)
    frame = pd.DataFrame(weather_rows)
    hdd = (base_temp - frame["temp_avg"]).clip(lower=0).sum()
    cdd = (frame["temp_avg"] - base_temp).clip(lower=0).sum()
    return float(hdd), float(cdd)


def calculate_monthly_degree_days(weather_rows: list[dict], base_temp: float = 18.0) -> dict[int, dict]:
    """Per-month HDD/CDD (rather than one annual total) -- required for the
    energy-signature regression, which needs one (HDD, CDD) pair per billing
    period to explain that period's metered consumption."""
    buckets: dict[int, list[float]] = {}
    for row in weather_rows:
        date_value = row.get("date")
        month = getattr(date_value, "month", None)
        if month is None and isinstance(date_value, str) and len(date_value) >= 7:
            month = int(date_value[5:7])
        if month is None or row.get("temp_avg") is None:
            continue
        buckets.setdefault(month, []).append(row["temp_avg"])
    result = {}
    for month, temps in buckets.items():
        hdd = sum(max(base_temp - t, 0) for t in temps)
        cdd = sum(max(t - base_temp, 0) for t in temps)
        result[month] = {"hdd": hdd, "cdd": cdd, "days": len(temps)}
    return result


def get_ideal_e2(climate_zone: str | None, custom_e2: float | None = None) -> float:
    if custom_e2 and custom_e2 > 0:
        return custom_e2
    return CLIMATE_E2_DEFAULTS.get(climate_zone or "moderate_dry", DEFAULT_STANDARD_EUI)


def classify_energy_label_by_ratio(actual_eui: float, ideal_e2: float) -> dict:
    ratio = actual_eui / ideal_e2 if ideal_e2 > 0 else 0
    for item in ENERGY_LABEL_RANGES:
        if item["min_ratio"] <= ratio < item["max_ratio"]:
            return {**item, "ratio": ratio}
    return {**ENERGY_LABEL_RANGES[-1], "ratio": ratio}


def detect_high_consumption(eui: float, standard_eui: float = DEFAULT_STANDARD_EUI) -> bool:
    return eui > standard_eui


def summarize_weather_monthly(weather_rows: list[dict]) -> list[dict]:
    grouped: dict[int, dict] = {}
    for row in weather_rows:
        date_value = row.get("date")
        month = getattr(date_value, "month", None)
        if month is None and isinstance(date_value, str) and len(date_value) >= 7:
            month = int(date_value[5:7])
        if month is None:
            continue
        bucket = grouped.setdefault(month, {"month": month, "count": 0, "temp_avg": 0, "humidity": 0, "solar_radiation": 0, "rainfall": 0})
        bucket["count"] += 1
        bucket["temp_avg"] += row.get("temp_avg") or 0
        bucket["humidity"] += row.get("humidity") or 0
        bucket["solar_radiation"] += row.get("solar_radiation") or 0
        bucket["rainfall"] += row.get("rainfall") or 0
    summary = []
    for month, bucket in sorted(grouped.items()):
        count = bucket["count"] or 1
        summary.append({
            "month": month,
            "temp_avg": bucket["temp_avg"] / count,
            "humidity": bucket["humidity"] / count,
            "solar_radiation": bucket["solar_radiation"] / count,
            "rainfall": bucket["rainfall"],
        })
    return summary


def calculate_electric_equipment(items: list[dict]) -> list[dict]:
    calculated = []
    for item in items:
        quantity = item.get("quantity", 1) or 0
        power_w = item.get("power_w", 0) or 0
        hours = item.get("hours_per_day", 0) or 0
        days = item.get("days_per_year", 365) or 0
        annual_kwh = quantity * power_w * hours * days / 1000
        calculated.append({**item, "annual_kwh": annual_kwh, "average_power_w": quantity * power_w})
    return calculated


def calculate_gas_equipment(items: list[dict]) -> list[dict]:
    calculated = []
    for item in items:
        quantity = item.get("quantity", 1) or 0
        rate = item.get("gas_m3_per_hour", 0) or 0
        hours = item.get("hours_per_day", 0) or 0
        days = item.get("days_per_year", 365) or 0
        annual_m3 = quantity * rate * hours * days
        calculated.append({**item, "annual_m3": annual_m3, "average_gas_m3_per_hour": quantity * rate})
    return calculated


def detect_monthly_anomalies(monthly_energy: list[dict], predicted_by_month: dict[int, float] | None = None, residual_std: float | None = None) -> list[dict]:
    """Flag months whose metered energy deviates unusually from what is
    expected for that month.

    When ``predicted_by_month`` (from the weather-normalized energy-signature
    regression in ``regression.py``) is available, deviation is measured
    against *that month's own weather-adjusted expectation* and flagged
    using a standard statistical threshold (|residual| > 2 * residual_std,
    i.e. outside a ~95% confidence band) -- so a cold month that simply used
    more heating, as expected, is no longer misreported as an "anomaly".

    Without weather data (``predicted_by_month`` is None) this falls back to
    the simpler flat-average comparison, which is coarser but still better
    than nothing."""
    if not monthly_energy:
        return []
    if predicted_by_month and residual_std and residual_std > 0:
        anomalies = []
        for item in monthly_energy:
            predicted = predicted_by_month.get(item["month"])
            if predicted is None:
                continue
            residual = item["total_mj"] - predicted
            z_score = residual / residual_std
            if z_score > 2:
                anomalies.append({
                    "month": item["month"],
                    "type": "peak",
                    "message": f"Metered energy is {residual:.0f} MJ above the weather-adjusted expectation for this month (z={z_score:.1f}).",
                })
            elif z_score < -2:
                anomalies.append({
                    "month": item["month"],
                    "type": "low",
                    "message": f"Metered energy is {abs(residual):.0f} MJ below the weather-adjusted expectation for this month (z={z_score:.1f}).",
                })
        return anomalies

    values = [item["total_mj"] for item in monthly_energy]
    average = sum(values) / len(values)
    anomalies = []
    for item in monthly_energy:
        ratio = item["total_mj"] / average if average else 0
        if ratio > 1.35:
            anomalies.append({"month": item["month"], "type": "peak", "message": "Monthly energy is more than 35% above annual monthly average (weather data unavailable for a precise, weather-adjusted comparison)."})
        elif ratio < 0.65:
            anomalies.append({"month": item["month"], "type": "low", "message": "Monthly energy is more than 35% below annual monthly average (weather data unavailable for a precise, weather-adjusted comparison)."})
    return anomalies


def generate_recommendations(inputs: RecommendationRuleInput, high_consumption: bool = False) -> list[dict]:
    recommendations: list[dict] = []
    window_type = (inputs.window_type or "").lower()
    lighting_type = (inputs.lighting_type or "").lower()
    heating_system = (inputs.heating_system or "").lower()
    cooling_system = (inputs.cooling_system or "").lower()
    orientation = (inputs.orientation or "").lower()

    if "single" in window_type or "تک" in window_type:
        recommendations.append({"category": "envelope", "recommendation": "Replace single glazing with low-emissivity double-glazed windows. | تعویض پنجره تک‌جداره با دوجداره کم‌گسیل", "impact_level": "high"})
    if not inputs.has_insulation:
        recommendations.append({"category": "envelope", "recommendation": "Add roof and external wall insulation aligned with مبحث ۱۹ envelope requirements. | عایق‌کاری سقف و دیوار خارجی", "impact_level": "high"})
    if "incandescent" in lighting_type or "رشته" in lighting_type:
        recommendations.append({"category": "lighting", "recommendation": "Replace incandescent lamps with LED fixtures and controls. | جایگزینی لامپ رشته‌ای با LED", "impact_level": "high"})
    if "old" in heating_system or "low efficiency" in heating_system or "قدیمی" in heating_system:
        recommendations.append({"category": "heating", "recommendation": "Upgrade heating to high-efficiency condensing boiler or efficient package. | ارتقای سیستم گرمایش", "impact_level": "high"})
    if not inputs.has_thermostat:
        recommendations.append({"category": "heating", "recommendation": "Install programmable thermostats and zoning controls. | نصب ترموستات و کنترل منطقه‌ای", "impact_level": "medium"})
    if "old" in cooling_system or "low eer" in cooling_system or "قدیمی" in cooling_system:
        recommendations.append({"category": "cooling", "recommendation": "Use inverter air conditioners with higher EER/COP. | استفاده از کولر گازی اینورتر", "impact_level": "high"})
    if ("south" in orientation or "west" in orientation or "جنوب" in orientation or "غرب" in orientation) and not inputs.has_shading:
        recommendations.append({"category": "envelope", "recommendation": "Install external shading or awnings for high solar-gain windows. | نصب سایه‌بان خارجی", "impact_level": "medium"})
    if high_consumption:
        recommendations.append({"category": "management", "recommendation": "Perform Level 2 detailed audit with end-use metering. | انجام ممیزی تفصیلی سطح دو", "impact_level": "medium"})
    return recommendations


def build_audit_result(
    bills: list[dict],
    weather_rows: list[dict],
    area_m2: float,
    occupants: int,
    standard_eui: float = DEFAULT_STANDARD_EUI,
    base_temp: float = 18.0,
    climate_zone: str | None = "moderate_dry",
    custom_e2: float | None = None,
    electric_equipment: list[dict] | None = None,
    gas_equipment: list[dict] | None = None,
) -> dict:
    monthly = calculate_monthly_energy(bills, area_m2, occupants)
    annual = calculate_annual_energy(monthly)
    annual_electricity_mj = sum(item["electricity_mj"] for item in monthly)
    annual_gas_mj = sum(item["gas_mj"] for item in monthly)
    annual_electricity_kwh = sum(item["electricity_kwh"] for item in bills)
    annual_gas_m3 = sum(item.get("gas_m3", 0) for item in bills)
    eui = calculate_eui(annual, area_m2)
    energy_per_person = calculate_energy_per_person(annual, occupants)
    hdd, cdd = calculate_hdd_cdd(weather_rows, base_temp)
    monthly_degree_days = calculate_monthly_degree_days(weather_rows, base_temp)
    energy_signature = fit_energy_signature(monthly, monthly_degree_days)
    if energy_signature:
        anomalies = detect_monthly_anomalies(monthly, energy_signature.predicted_by_month, energy_signature.residual_std)
    else:
        anomalies = detect_monthly_anomalies(monthly)
    ideal_e2 = get_ideal_e2(climate_zone, custom_e2)
    energy_label = classify_energy_label_by_ratio(eui, ideal_e2)
    performance_score = calculate_performance_score(energy_label["ratio"], len(anomalies))
    confidence = calculate_confidence(
        bill_months=len(bills),
        weather_days_covered=len(weather_rows),
        r_squared=energy_signature.r_squared if energy_signature else None,
    )
    return {
        "total_energy_mj": annual,
        "annual_electricity_mj": annual_electricity_mj,
        "annual_gas_mj": annual_gas_mj,
        "annual_electricity_kwh": annual_electricity_kwh,
        "annual_gas_m3": annual_gas_m3,
        "eui": eui,
        "energy_per_person": energy_per_person,
        "hdd": hdd,
        "cdd": cdd,
        "energy_rating": energy_label["rating"],
        "energy_index_ratio": energy_label["ratio"],
        "energy_label_ranges": ENERGY_LABEL_RANGES,
        "ideal_e2": ideal_e2,
        "climate_zone": climate_zone,
        "standard_eui": ideal_e2 or standard_eui,
        "high_consumption_flag": detect_high_consumption(eui, ideal_e2 or standard_eui),
        "performance_score": performance_score,
        "confidence": confidence,
        "energy_signature": {
            "baseload_mj_per_month": energy_signature.baseload_mj_per_month,
            "heating_signature_mj_per_hdd": energy_signature.heating_signature_mj_per_hdd,
            "cooling_signature_mj_per_cdd": energy_signature.cooling_signature_mj_per_cdd,
            "r_squared": energy_signature.r_squared,
            "implied_annual_heating_mj": energy_signature.heating_signature_mj_per_hdd * hdd,
            "implied_annual_cooling_mj": energy_signature.cooling_signature_mj_per_cdd * cdd,
        } if energy_signature else None,
        "monthly": monthly,
        "weather_monthly": summarize_weather_monthly(weather_rows),
        "electric_equipment": calculate_electric_equipment(electric_equipment or []),
        "gas_equipment": calculate_gas_equipment(gas_equipment or []),
        "anomalies": anomalies,
    }
