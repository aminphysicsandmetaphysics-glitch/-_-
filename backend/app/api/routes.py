from datetime import date

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.entities import AuditResult, Building, EnergyBill, Recommendation, WeatherData
from app.schemas.audit import (
    AuditResultRead,
    BuildingCreate,
    BuildingRead,
    EnergyBillCreate,
    EnergyBillRead,
    RecommendationRead,
    WeatherDataCreate,
    WeatherDataRead,
)
from app.services.analytics import RecommendationRuleInput, build_audit_result, generate_recommendations
from app.services.reports import build_excel_report, build_pdf_report

router = APIRouter(prefix="/api/v1")


@router.post("/buildings", response_model=BuildingRead)
def create_building(payload: BuildingCreate, db: Session = Depends(get_db)):
    building = Building(**payload.model_dump())
    db.add(building)
    db.commit()
    db.refresh(building)
    return building


@router.get("/buildings", response_model=list[BuildingRead])
def list_buildings(db: Session = Depends(get_db)):
    return db.query(Building).order_by(Building.created_at.desc()).all()


@router.get("/buildings/{building_id}", response_model=BuildingRead)
def get_building(building_id: int, db: Session = Depends(get_db)):
    building = db.get(Building, building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
    return building


@router.post("/buildings/{building_id}/bills", response_model=list[EnergyBillRead])
def upsert_bills(building_id: int, payload: list[EnergyBillCreate], db: Session = Depends(get_db)):
    if not db.get(Building, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
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
def list_bills(building_id: int, db: Session = Depends(get_db)):
    return (
        db.query(EnergyBill)
        .filter(EnergyBill.building_id == building_id)
        .order_by(EnergyBill.year, EnergyBill.month)
        .all()
    )


@router.post("/buildings/{building_id}/weather", response_model=list[WeatherDataRead])
def upsert_weather(building_id: int, payload: list[WeatherDataCreate], db: Session = Depends(get_db)):
    if not db.get(Building, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
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
def list_weather(building_id: int, db: Session = Depends(get_db)):
    return db.query(WeatherData).filter(WeatherData.building_id == building_id).order_by(WeatherData.date).all()


@router.post("/buildings/{building_id}/weather/import")
async def import_weather_excel(building_id: int, file: UploadFile, db: Session = Depends(get_db)):
    import pandas as pd

    if not db.get(Building, building_id):
        raise HTTPException(status_code=404, detail="Building not found")
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
        ))
    return upsert_weather(building_id, rows, db)


def _collect_audit_inputs(building_id: int, db: Session):
    building = db.get(Building, building_id)
    if not building:
        raise HTTPException(status_code=404, detail="Building not found")
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
        }
        for row in db.query(WeatherData).filter(WeatherData.building_id == building_id).order_by(WeatherData.date).all()
    ]
    return building, bills, weather_rows


@router.post("/buildings/{building_id}/audit/run", response_model=AuditResultRead)
def run_audit(building_id: int, db: Session = Depends(get_db)):
    building, bills, weather_rows = _collect_audit_inputs(building_id, db)
    result = build_audit_result(
        bills=bills,
        weather_rows=weather_rows,
        area_m2=building.area_m2,
        occupants=building.occupants,
        standard_eui=settings.default_standard_eui_mj_m2_year,
        base_temp=settings.degree_day_base_temp_c,
    )
    audit = AuditResult(building_id=building_id, **{key: result[key] for key in result if key != "monthly"})
    db.add(audit)
    db.query(Recommendation).filter(Recommendation.building_id == building_id).delete()
    recommendations = generate_recommendations(
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
    for item in recommendations:
        db.add(Recommendation(building_id=building_id, **item))
    db.commit()
    db.refresh(audit)
    result_recommendations = db.query(Recommendation).filter(Recommendation.building_id == building_id).all()
    response = AuditResultRead.model_validate(audit)
    response.monthly = result["monthly"]
    response.recommendations = [RecommendationRead.model_validate(item) for item in result_recommendations]
    return response


@router.get("/buildings/{building_id}/audit/latest", response_model=AuditResultRead)
def latest_audit(building_id: int, db: Session = Depends(get_db)):
    building, bills, weather_rows = _collect_audit_inputs(building_id, db)
    latest = (
        db.query(AuditResult)
        .filter(AuditResult.building_id == building_id)
        .order_by(AuditResult.created_at.desc())
        .first()
    )
    if not latest:
        return run_audit(building_id, db)
    result = build_audit_result(bills, weather_rows, building.area_m2, building.occupants, latest.standard_eui)
    response = AuditResultRead.model_validate(latest)
    response.monthly = result["monthly"]
    response.recommendations = [
        RecommendationRead.model_validate(item)
        for item in db.query(Recommendation).filter(Recommendation.building_id == building_id).all()
    ]
    return response


@router.get("/buildings/{building_id}/reports/pdf")
def download_pdf_report(building_id: int, db: Session = Depends(get_db)):
    audit = latest_audit(building_id, db)
    building = db.get(Building, building_id)
    recommendations = [item.model_dump() for item in audit.recommendations]
    output = build_pdf_report(building, audit.model_dump(), recommendations)
    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=audit-{building_id}.pdf"},
    )


@router.get("/buildings/{building_id}/reports/excel")
def download_excel_report(building_id: int, db: Session = Depends(get_db)):
    audit = latest_audit(building_id, db)
    building, bills, weather_rows = _collect_audit_inputs(building_id, db)
    output = build_excel_report(building, bills, weather_rows, audit.model_dump())
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=audit-{building_id}.xlsx"},
    )
