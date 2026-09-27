from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.auth import create_access_token, get_current_user, hash_password, verify_password
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import (
    AuditResult,
    Building,
    ElectricEquipment,
    EnergyBill,
    GasEquipment,
    Recommendation,
    User,
    WeatherData,
)
from app.schemas.audit import (
    AnomalyRead,
    AuditResultRead,
    BuildingCreate,
    BuildingRead,
    EnergyBillCreate,
    EnergyBillRead,
    ElectricEquipmentCreate,
    ElectricEquipmentRead,
    GasEquipmentCreate,
    GasEquipmentRead,
    MonthlyEnergyRead,
    RecommendationRead,
    Token,
    UserCreate,
    UserRead,
    WeatherAutoFetchRequest,
    WeatherDataCreate,
    WeatherDataRead,
    WeatherMonthlyRead,
)
from app.services.analytics import RecommendationRuleInput, build_audit_result, calculate_electric_equipment, calculate_gas_equipment, generate_recommendations
from app.services.catalogs import get_envelope_options, get_equipment_options
from app.services.economics import TariffAssumptions, calculate_carbon_footprint, quantify_recommendations, quantify_sensitivity_item
from app.services.reports import build_excel_report, build_pdf_report
from app.services.sensitivity import rank_envelope_sensitivity
from app.services.thermal import EnvelopeInputs, compare_theoretical_to_billed, estimate_theoretical_demand
from app.services.weather_client import WeatherLookupError, auto_fetch_weather_for_building

router = APIRouter(prefix="/api/v1")


def _default_tariffs() -> TariffAssumptions:
    return TariffAssumptions(
        electricity_toman_per_kwh=settings.electricity_toman_per_kwh,
        gas_toman_per_m3=settings.gas_toman_per_m3,
        grid_emission_factor_kg_co2_per_kwh=settings.grid_emission_factor_kg_co2_per_kwh,
        gas_emission_factor_kg_co2_per_m3=settings.gas_emission_factor_kg_co2_per_m3,
    )


# --------------------------------------------------------------------------
# Auth
# --------------------------------------------------------------------------

@router.post("/auth/register", response_model=UserRead)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=400, detail="An account with this email already exists")
    user = User(email=payload.email, hashed_password=hash_password(payload.password), full_name=payload.full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/auth/login", response_model=Token)
def login(payload: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return Token(access_token=create_access_token(str(user.id)))


@router.get("/auth/me", response_model=UserRead)
def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


# --------------------------------------------------------------------------
# Reference catalogs -- auto-fill data instead of free-typed technical fields
# --------------------------------------------------------------------------

@router.get("/catalogs/envelope")
def list_envelope_catalog(category: str | None = None):
    return get_envelope_options(category)


@router.get("/catalogs/equipment")
def list_equipment_catalog(fuel: str | None = None):
    return get_equipment_options(fuel)


# --------------------------------------------------------------------------
# Buildings (owner-scoped)
# --------------------------------------------------------------------------

def _get_owned_building(building_id: int, current_user: User, db: Session) -> Building:
    building = db.get(Building, building_id)
    if not building or building.owner_id != current_user.id:
        raise HTTPException(status_code=404, detail="Building not found")
    return building


@router.post("/buildings", response_model=BuildingRead)
def create_building(payload: BuildingCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    building = Building(owner_id=current_user.id, **payload.model_dump())
    db.add(building)
    db.commit()
    db.refresh(building)
    return building


@router.get("/buildings", response_model=list[BuildingRead])
def list_buildings(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Building)
        .filter(Building.owner_id == current_user.id)
        .order_by(Building.created_at.desc())
        .all()
    )


@router.get("/buildings/{building_id}", response_model=BuildingRead)
def get_building(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return _get_owned_building(building_id, current_user, db)


@router.post("/buildings/{building_id}/bills", response_model=list[EnergyBillRead])
def upsert_bills(building_id: int, payload: list[EnergyBillCreate], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_owned_building(building_id, current_user, db)
    saved = []
    for item in payload:
        bill = (
            db.query(EnergyBill)
            .filter(EnergyBill.building_id == building_id, EnergyBill.year == item.year, EnergyBill.month == item.month)
            .one_or_none()
        )
        if bill:
            for key, value in item.model_dump().items():
                setattr(bill, key, value)
        else:
            bill = EnergyBill(building_id=building_id, **item.model_dump())
            db.add(bill)
        saved.append(bill)
    db.commit()
    for bill in saved:
        db.refresh(bill)
    return saved


@router.get("/buildings/{building_id}/bills", response_model=list[EnergyBillRead])
def list_bills(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_owned_building(building_id, current_user, db)
    return (
        db.query(EnergyBill)
        .filter(EnergyBill.building_id == building_id)
        .order_by(EnergyBill.year, EnergyBill.month)
        .all()
    )


@router.post("/buildings/{building_id}/weather", response_model=list[WeatherDataRead])
def upsert_weather(building_id: int, payload: list[WeatherDataCreate], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_owned_building(building_id, current_user, db)
    saved = []
    for item in payload:
        row = (
            db.query(WeatherData)
            .filter(WeatherData.building_id == building_id, WeatherData.date == item.date)
            .one_or_none()
        )
        if row:
            for key, value in item.model_dump().items():
                setattr(row, key, value)
        else:
            row = WeatherData(building_id=building_id, **item.model_dump())
            db.add(row)
        saved.append(row)
    db.commit()
    for row in saved:
        db.refresh(row)
    return saved


@router.get("/buildings/{building_id}/weather", response_model=list[WeatherDataRead])
def list_weather(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_owned_building(building_id, current_user, db)
    return db.query(WeatherData).filter(WeatherData.building_id == building_id).order_by(WeatherData.date).all()


@router.post("/buildings/{building_id}/weather/auto-fetch", response_model=list[WeatherDataRead])
def auto_fetch_weather(building_id: int, payload: WeatherAutoFetchRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Populate a full year of daily weather automatically from the free
    Open-Meteo historical archive, keyed on the building's city (or an
    explicit lat/lon override), instead of requiring manual entry."""
    building = _get_owned_building(building_id, current_user, db)
    city = payload.city or building.city or "Tehran"
    latitude = payload.latitude if payload.latitude is not None else building.latitude
    longitude = payload.longitude if payload.longitude is not None else building.longitude
    try:
        result = auto_fetch_weather_for_building(city, latitude, longitude)
    except WeatherLookupError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    if building.latitude is None or building.longitude is None:
        building.latitude = result["latitude"]
        building.longitude = result["longitude"]
        db.add(building)
        db.commit()

    rows = [WeatherDataCreate(city=result["resolved_city"], **row) for row in result["rows"]]
    return upsert_weather(building_id, rows, db, current_user)


@router.post("/buildings/{building_id}/equipment/electric", response_model=list[ElectricEquipmentRead])
def upsert_electric_equipment(building_id: int, payload: list[ElectricEquipmentCreate], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_owned_building(building_id, current_user, db)
    db.query(ElectricEquipment).filter(ElectricEquipment.building_id == building_id).delete()
    saved = []
    for item in payload:
        row = ElectricEquipment(building_id=building_id, **item.model_dump())
        db.add(row)
        saved.append(row)
    db.commit()
    for row in saved:
        db.refresh(row)
    calculated = calculate_electric_equipment([{**ElectricEquipmentRead.model_validate(row).model_dump()} for row in saved])
    return calculated


@router.get("/buildings/{building_id}/equipment/electric", response_model=list[ElectricEquipmentRead])
def list_electric_equipment(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_owned_building(building_id, current_user, db)
    rows = db.query(ElectricEquipment).filter(ElectricEquipment.building_id == building_id).all()
    return calculate_electric_equipment([ElectricEquipmentRead.model_validate(row).model_dump() for row in rows])


@router.post("/buildings/{building_id}/equipment/gas", response_model=list[GasEquipmentRead])
def upsert_gas_equipment(building_id: int, payload: list[GasEquipmentCreate], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_owned_building(building_id, current_user, db)
    db.query(GasEquipment).filter(GasEquipment.building_id == building_id).delete()
    saved = []
    for item in payload:
        row = GasEquipment(building_id=building_id, **item.model_dump())
        db.add(row)
        saved.append(row)
    db.commit()
    for row in saved:
        db.refresh(row)
    return calculate_gas_equipment([GasEquipmentRead.model_validate(row).model_dump() for row in saved])


@router.get("/buildings/{building_id}/equipment/gas", response_model=list[GasEquipmentRead])
def list_gas_equipment(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _get_owned_building(building_id, current_user, db)
    rows = db.query(GasEquipment).filter(GasEquipment.building_id == building_id).all()
    return calculate_gas_equipment([GasEquipmentRead.model_validate(row).model_dump() for row in rows])


@router.post("/buildings/{building_id}/weather/import")
async def import_weather_excel(building_id: int, file: UploadFile, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    import pandas as pd

    _get_owned_building(building_id, current_user, db)
    frame = pd.read_excel(file.file)
    normalized = {column.lower().strip().replace(" ", "_"): column for column in frame.columns}
    required = ["date", "temp_avg"]
    if any(column not in normalized for column in required):
        raise HTTPException(status_code=400, detail="Excel must include Date and Mean/Avg Temp columns")
    rows = []
    for _, record in frame.iterrows():
        record_date = pd.to_datetime(record[normalized["date"]]).date()
        rows.append(WeatherDataCreate(
            date=record_date,
            temp_min=float(record[normalized.get("temp_min", normalized["temp_avg"])]),
            temp_max=float(record[normalized.get("temp_max", normalized["temp_avg"])]),
            temp_avg=float(record[normalized["temp_avg"]]),
            humidity=float(record[normalized["humidity"]]) if "humidity" in normalized else None,
            solar_radiation=float(record[normalized["solar_radiation"]]) if "solar_radiation" in normalized else None,
            rainfall=float(record[normalized["rainfall"]]) if "rainfall" in normalized else None,
            wind_speed=float(record[normalized["wind_speed"]]) if "wind_speed" in normalized else None,
        ))
    return upsert_weather(building_id, rows, db, current_user)


def _collect_audit_inputs(building_id: int, current_user: User, db: Session):
    building = _get_owned_building(building_id, current_user, db)
    bills = [
        {
            "year": bill.year,
            "month": bill.month,
            "electricity_kwh": bill.electricity_kwh,
            "gas_m3": bill.gas_m3,
            "electricity_cost": bill.electricity_cost,
            "gas_cost": bill.gas_cost,
        }
        for bill in db.query(EnergyBill).filter(EnergyBill.building_id == building_id).order_by(EnergyBill.month).all()
    ]
    if len(bills) < 12:
        raise HTTPException(status_code=400, detail="At least 12 monthly bills are required")
    weather_rows = [
        {
            "date": row.date,
            "temp_min": row.temp_min,
            "temp_max": row.temp_max,
            "temp_avg": row.temp_avg,
            "humidity": row.humidity,
            "solar_radiation": row.solar_radiation,
            "rainfall": row.rainfall,
            "wind_speed": row.wind_speed,
        }
        for row in db.query(WeatherData).filter(WeatherData.building_id == building_id).order_by(WeatherData.date).all()
    ]
    electric_equipment = [
        ElectricEquipmentRead.model_validate(row).model_dump()
        for row in db.query(ElectricEquipment).filter(ElectricEquipment.building_id == building_id).all()
    ]
    gas_equipment = [
        GasEquipmentRead.model_validate(row).model_dump()
        for row in db.query(GasEquipment).filter(GasEquipment.building_id == building_id).all()
    ]
    return building, bills, weather_rows, electric_equipment, gas_equipment


def _run_full_audit(building: Building, bills, weather_rows, electric_equipment, gas_equipment) -> dict:
    result = build_audit_result(
        bills=bills,
        weather_rows=weather_rows,
        area_m2=building.area_m2,
        occupants=building.occupants,
        standard_eui=settings.default_standard_eui_mj_m2_year,
        base_temp=settings.degree_day_base_temp_c,
        climate_zone=building.climate_zone,
        custom_e2=building.ideal_e2,
        electric_equipment=electric_equipment,
        gas_equipment=gas_equipment,
    )

    envelope_inputs = EnvelopeInputs(
        footprint_area_m2=building.area_m2,
        floors=building.floors or 1,
        wall_area_m2=building.wall_area_m2,
        roof_area_m2=building.roof_area_m2,
        floor_area_m2=building.floor_area_m2,
        window_area_m2=building.window_area_m2,
        wall_material_key=building.wall_material_key,
        roof_material_key=building.roof_material_key,
        floor_material_key=building.floor_material_key,
        window_material_key=building.window_material_key,
        airtightness=building.airtightness or "medium",
        has_shading=building.has_shading,
    )
    theoretical = estimate_theoretical_demand(envelope_inputs, result["hdd"], result["cdd"])
    comparison = compare_theoretical_to_billed(theoretical["theoretical_heating_mj"], result["annual_gas_mj"] or result["total_energy_mj"])

    tariffs = _default_tariffs()
    carbon = calculate_carbon_footprint(result["annual_electricity_kwh"], result["annual_gas_m3"], tariffs)

    # Envelope opportunities: precise, physics-based, ranked by *this
    # building's* computed impact (see services/sensitivity.py) rather than
    # generic rule-of-thumb percentages.
    envelope_opportunities = [
        quantify_sensitivity_item(item, tariffs, has_gas_heating=result["annual_gas_mj"] > 0)
        for item in rank_envelope_sensitivity(envelope_inputs, result["hdd"], result["cdd"])
    ]

    # Everything else (lighting/heating-system/cooling-system/thermostat/
    # management) still comes from the rule engine + percentage-based
    # economics model, since there is no physics model for those.
    rule_based = [
        item for item in generate_recommendations(
            RecommendationRuleInput(
                window_type=building.window_type,
                lighting_type=building.lighting_type,
                heating_system=building.heating_system,
                cooling_system=building.cooling_system,
                has_thermostat=building.has_thermostat,
                has_insulation=building.has_insulation,
                has_shading=building.has_shading,
                orientation=building.orientation,
            ),
            high_consumption=result["high_consumption_flag"],
        )
        if item["category"] != "envelope"
    ]
    quantified_rule_based = quantify_recommendations(
        rule_based,
        tariffs,
        total_energy_mj=result["total_energy_mj"],
        electricity_mj=result["annual_electricity_mj"],
        gas_mj=result["annual_gas_mj"],
        theoretical_heating_mj=theoretical["theoretical_heating_mj"],
        theoretical_cooling_mj=theoretical["theoretical_cooling_mj"],
        electric_equipment=result["electric_equipment"],
    )

    quantified = sorted(
        envelope_opportunities + quantified_rule_based,
        key=lambda item: item.get("estimated_annual_savings_toman") or 0,
        reverse=True,
    )

    result["theoretical_heating_mj"] = theoretical["theoretical_heating_mj"]
    result["theoretical_cooling_mj"] = theoretical["theoretical_cooling_mj"]
    result["envelope_diagnosis"] = comparison["diagnosis"]
    result["envelope_breakdown"] = theoretical["breakdown"]
    result["total_co2_kg"] = carbon["total_co2_kg"]
    result["carbon_footprint"] = carbon
    result["quantified_recommendations"] = quantified
    return result


@router.post("/buildings/{building_id}/audit/run", response_model=AuditResultRead)
def run_audit(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    building, bills, weather_rows, electric_equipment, gas_equipment = _collect_audit_inputs(building_id, current_user, db)
    result = _run_full_audit(building, bills, weather_rows, electric_equipment, gas_equipment)

    persistent_keys = {
        "total_energy_mj", "eui", "energy_per_person", "hdd", "cdd", "energy_rating",
        "energy_index_ratio", "ideal_e2", "climate_zone", "standard_eui", "high_consumption_flag",
        "theoretical_heating_mj", "theoretical_cooling_mj", "envelope_diagnosis", "total_co2_kg",
        "performance_score",
    }
    audit = AuditResult(building_id=building_id, **{key: result[key] for key in persistent_keys})
    db.add(audit)
    db.query(Recommendation).filter(Recommendation.building_id == building_id).delete()
    for item in result["quantified_recommendations"]:
        db.add(Recommendation(
            building_id=building_id,
            category=item["category"],
            recommendation=item["recommendation"],
            impact_level=item["impact_level"],
            status=item.get("status", "planned"),
        ))
    db.commit()
    db.refresh(audit)

    response = AuditResultRead.model_validate(audit)
    response.monthly = [MonthlyEnergyRead(**item) for item in result["monthly"]]
    response.weather_monthly = [WeatherMonthlyRead(**item) for item in result["weather_monthly"]]
    response.electric_equipment = [ElectricEquipmentRead(**item) for item in result["electric_equipment"]]
    response.gas_equipment = [GasEquipmentRead(**item) for item in result["gas_equipment"]]
    response.energy_label_ranges = result["energy_label_ranges"]
    response.anomalies = [AnomalyRead(**item) for item in result["anomalies"]]
    response.envelope_breakdown = result["envelope_breakdown"]
    response.carbon_footprint = result["carbon_footprint"]
    response.confidence = result["confidence"]
    response.energy_signature = result["energy_signature"]
    stored_recommendations = db.query(Recommendation).filter(Recommendation.building_id == building_id).order_by(Recommendation.id).all()
    response.recommendations = [
        RecommendationRead(**{**RecommendationRead.model_validate(orm_row).model_dump(), **quantified})
        for orm_row, quantified in zip(stored_recommendations, result["quantified_recommendations"])
    ]
    return response


@router.get("/buildings/{building_id}/audit/latest", response_model=AuditResultRead)
def latest_audit(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    building, bills, weather_rows, electric_equipment, gas_equipment = _collect_audit_inputs(building_id, current_user, db)
    latest = (
        db.query(AuditResult)
        .filter(AuditResult.building_id == building_id)
        .order_by(AuditResult.created_at.desc())
        .first()
    )
    if not latest:
        return run_audit(building_id, db, current_user)

    result = _run_full_audit(building, bills, weather_rows, electric_equipment, gas_equipment)
    response = AuditResultRead.model_validate(latest)
    response.monthly = [MonthlyEnergyRead(**item) for item in result["monthly"]]
    response.weather_monthly = [WeatherMonthlyRead(**item) for item in result["weather_monthly"]]
    response.electric_equipment = [ElectricEquipmentRead(**item) for item in result["electric_equipment"]]
    response.gas_equipment = [GasEquipmentRead(**item) for item in result["gas_equipment"]]
    response.energy_label_ranges = result["energy_label_ranges"]
    response.anomalies = [AnomalyRead(**item) for item in result["anomalies"]]
    response.envelope_breakdown = result["envelope_breakdown"]
    response.carbon_footprint = result["carbon_footprint"]
    response.confidence = result["confidence"]
    response.energy_signature = result["energy_signature"]
    stored_recommendations = db.query(Recommendation).filter(Recommendation.building_id == building_id).order_by(Recommendation.id).all()
    response.recommendations = [
        RecommendationRead(**{**RecommendationRead.model_validate(orm_row).model_dump(), **quantified})
        for orm_row, quantified in zip(stored_recommendations, result["quantified_recommendations"])
    ]
    return response


@router.get("/buildings/{building_id}/reports/pdf")
def download_pdf_report(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    audit = latest_audit(building_id, db, current_user)
    building = _get_owned_building(building_id, current_user, db)
    recommendations = [item.model_dump() for item in audit.recommendations]
    output = build_pdf_report(building, audit.model_dump(), recommendations)
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=audit-{building_id}.pdf"},
    )


@router.get("/buildings/{building_id}/reports/excel")
def download_excel_report(building_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    audit = latest_audit(building_id, db, current_user)
    building, bills, weather_rows, _, _ = _collect_audit_inputs(building_id, current_user, db)
    output = build_excel_report(building, bills, weather_rows, audit.model_dump())
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=audit-{building_id}.xlsx"},
    )
