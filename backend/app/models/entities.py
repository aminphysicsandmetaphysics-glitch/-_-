from sqlalchemy import Boolean, Date, DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Building(Base):
    __tablename__ = "buildings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_name: Mapped[str | None] = mapped_column(Text)
    city: Mapped[str | None] = mapped_column(Text, default="جاجرم")
    address: Mapped[str | None] = mapped_column(Text)
    area_m2: Mapped[float] = mapped_column(Float)
    floors: Mapped[int | None] = mapped_column(Integer)
    year_built: Mapped[int | None] = mapped_column(Integer)
    occupants: Mapped[int] = mapped_column(Integer)
    building_type: Mapped[str | None] = mapped_column(Text, default="Residential")
    heating_system: Mapped[str | None] = mapped_column(Text)
    cooling_system: Mapped[str | None] = mapped_column(Text)
    lighting_type: Mapped[str | None] = mapped_column(Text)
    window_type: Mapped[str | None] = mapped_column(Text)
    wall_type: Mapped[str | None] = mapped_column(Text)
    roof_type: Mapped[str | None] = mapped_column(Text)
    has_insulation: Mapped[bool] = mapped_column(Boolean, default=False)
    has_thermostat: Mapped[bool] = mapped_column(Boolean, default=False)
    has_shading: Mapped[bool] = mapped_column(Boolean, default=False)
    orientation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bills = relationship("EnergyBill", cascade="all, delete-orphan", back_populates="building")
    weather = relationship("WeatherData", cascade="all, delete-orphan", back_populates="building")
    audit_results = relationship("AuditResult", cascade="all, delete-orphan", back_populates="building")
    recommendations = relationship("Recommendation", cascade="all, delete-orphan", back_populates="building")


class EnergyBill(Base):
    __tablename__ = "energy_bills"

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="CASCADE"), index=True)
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)
    electricity_kwh: Mapped[float] = mapped_column(Float, default=0)
    gas_m3: Mapped[float] = mapped_column(Float, default=0)
    electricity_cost: Mapped[float | None] = mapped_column(Float)
    gas_cost: Mapped[float | None] = mapped_column(Float)

    building = relationship("Building", back_populates="bills")


class WeatherData(Base):
    __tablename__ = "weather_data"

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="CASCADE"), index=True)
    city: Mapped[str | None] = mapped_column(Text, default="جاجرم")
    date: Mapped[str] = mapped_column(Date)
    temp_min: Mapped[float | None] = mapped_column(Float)
    temp_max: Mapped[float | None] = mapped_column(Float)
    temp_avg: Mapped[float] = mapped_column(Float)

    building = relationship("Building", back_populates="weather")


class AuditResult(Base):
    __tablename__ = "audit_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="CASCADE"), index=True)
    total_energy_mj: Mapped[float] = mapped_column(Float)
    eui: Mapped[float] = mapped_column(Float)
    energy_per_person: Mapped[float] = mapped_column(Float)
    hdd: Mapped[float] = mapped_column(Float, default=0)
    cdd: Mapped[float] = mapped_column(Float, default=0)
    energy_rating: Mapped[str] = mapped_column(String(1))
    standard_eui: Mapped[float] = mapped_column(Float)
    high_consumption_flag: Mapped[bool] = mapped_column(Boolean)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), server_default=func.now())

    building = relationship("Building", back_populates="audit_results")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    building_id: Mapped[int] = mapped_column(ForeignKey("buildings.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(Text)
    recommendation: Mapped[str] = mapped_column(Text)
    impact_level: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="planned")

    building = relationship("Building", back_populates="recommendations")
