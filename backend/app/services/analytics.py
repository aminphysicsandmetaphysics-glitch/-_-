from dataclasses import dataclass

try:
    import pandas as pd
except ModuleNotFoundError:
    pd = None

ELECTRICITY_KWH_TO_MJ = 3.6
IRAN_NATURAL_GAS_M3_TO_MJ = 38.0
DEFAULT_STANDARD_EUI = 324.0


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
    return {
        "electricity_mj": electricity_mj,
        "gas_mj": gas_mj,
        "total_mj": electricity_mj + gas_mj,
    }


def calculate_monthly_energy(bills: list[dict], area_m2: float, occupants: int) -> list[dict]:
    monthly = []
    for bill in sorted(bills, key=lambda item: item["month"]):
        converted = convert_to_mj(bill.get("electricity_kwh", 0), bill.get("gas_m3", 0))
        monthly.append(
            {
                "month": bill["month"],
                "electricity_kwh": bill.get("electricity_kwh", 0),
                "gas_m3": bill.get("gas_m3", 0),
                "electricity_mj": converted["electricity_mj"],
                "gas_mj": converted["gas_mj"],
                "total_mj": converted["total_mj"],
                "energy_per_m2": converted["total_mj"] / area_m2,
                "energy_per_person": converted["total_mj"] / occupants,
            }
        )
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


def classify_energy_rating(eui: float) -> str:
    if eui < 100:
        return "A"
    if eui < 150:
        return "B"
    if eui < 200:
        return "C"
    if eui <= 300:
        return "D"
    return "E"


def detect_high_consumption(eui: float, standard_eui: float = DEFAULT_STANDARD_EUI) -> bool:
    return eui > standard_eui


def generate_recommendations(inputs: RecommendationRuleInput, high_consumption: bool = False) -> list[dict]:
    recommendations: list[dict] = []
    window_type = (inputs.window_type or "").lower()
    lighting_type = (inputs.lighting_type or "").lower()
    heating_system = (inputs.heating_system or "").lower()
    cooling_system = (inputs.cooling_system or "").lower()
    orientation = (inputs.orientation or "").lower()

    if "single" in window_type or "تک" in window_type:
        recommendations.append({
            "category": "envelope",
            "recommendation": "Replace single glazing with low-emissivity double-glazed windows.",
            "impact_level": "high",
        })
    if not inputs.has_insulation:
        recommendations.append({
            "category": "envelope",
            "recommendation": "Add roof and external wall insulation aligned with مبحث ۱۹ envelope requirements.",
            "impact_level": "high",
        })
    if "incandescent" in lighting_type or "رشته" in lighting_type:
        recommendations.append({
            "category": "lighting",
            "recommendation": "Replace incandescent lamps with LED fixtures and occupancy controls.",
            "impact_level": "high",
        })
    if "old" in heating_system or "low efficiency" in heating_system or "قدیمی" in heating_system:
        recommendations.append({
            "category": "heating",
            "recommendation": "Upgrade heating to a high-efficiency condensing boiler or efficient package system.",
            "impact_level": "high",
        })
    if not inputs.has_thermostat:
        recommendations.append({
            "category": "heating",
            "recommendation": "Install programmable thermostats and zoning controls.",
            "impact_level": "medium",
        })
    if "old" in cooling_system or "low eer" in cooling_system or "قدیمی" in cooling_system:
        recommendations.append({
            "category": "cooling",
            "recommendation": "Use inverter air conditioners with higher EER/COP and proper maintenance.",
            "impact_level": "high",
        })
    if ("south" in orientation or "west" in orientation or "جنوب" in orientation or "غرب" in orientation) and not inputs.has_shading:
        recommendations.append({
            "category": "envelope",
            "recommendation": "Install external shading or awnings for high solar-gain south-west windows.",
            "impact_level": "medium",
        })
    if high_consumption:
        recommendations.append({
            "category": "management",
            "recommendation": "Perform Level 2 detailed audit with end-use metering and occupant behavior review.",
            "impact_level": "medium",
        })
    return recommendations


def build_audit_result(
    bills: list[dict],
    weather_rows: list[dict],
    area_m2: float,
    occupants: int,
    standard_eui: float = DEFAULT_STANDARD_EUI,
    base_temp: float = 18.0,
) -> dict:
    monthly = calculate_monthly_energy(bills, area_m2, occupants)
    annual = calculate_annual_energy(monthly)
    eui = calculate_eui(annual, area_m2)
    energy_per_person = calculate_energy_per_person(annual, occupants)
    hdd, cdd = calculate_hdd_cdd(weather_rows, base_temp)
    return {
        "total_energy_mj": annual,
        "eui": eui,
        "energy_per_person": energy_per_person,
        "hdd": hdd,
        "cdd": cdd,
        "energy_rating": classify_energy_rating(eui),
        "standard_eui": standard_eui,
        "high_consumption_flag": detect_high_consumption(eui, standard_eui),
        "monthly": monthly,
    }
