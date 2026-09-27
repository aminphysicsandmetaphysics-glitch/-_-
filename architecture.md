# High-Level System Architecture

## 3-Tier Design

### Frontend

React + TypeScript single-page app:

- Dashboard for project portfolio and high-consumption alerts.
- Project form for building envelope, HVAC, lighting, and occupancy.
- Excel-like monthly bill input matching `ممیزی.xlsx`.
- Weather data input and future Excel/API upload support.
- Energy analysis charts for electricity, gas, total MJ, EUI, HDD, and CDD.
- Rating and recommendations pages.
- PDF/Excel report download actions.

### Backend

FastAPI application:

- REST endpoints under `/api/v1`.
- SQLAlchemy ORM models for PostgreSQL.
- Analytics engine using Python and Pandas for time-series calculations.
- Report engine using ReportLab and Pandas/XlsxWriter.
- Configurable benchmark EUI and degree-day base temperature.

### Database

PostgreSQL normalized schema:

- `buildings`
- `energy_bills`
- `weather_data`
- `audit_results`
- `recommendations`

## Data Flow

1. User creates a building project in the frontend.
2. Frontend posts building metadata to `POST /api/v1/buildings`.
3. User enters 12 monthly utility bills; frontend posts to `/buildings/{id}/bills`.
4. User uploads or enters weather records; frontend posts to `/buildings/{id}/weather`.
5. Frontend triggers `POST /buildings/{id}/audit/run`.
6. Backend converts energy units, aggregates annual MJ, computes EUI, HDD/CDD, rating, and recommendations.
7. Results are saved to `audit_results` and `recommendations`.
8. User downloads reports from `/reports/pdf` and `/reports/excel`.

## Analytics Algorithms

- Electricity: `MJ = kWh × 3.6`
- Natural gas in Iran: `MJ = m³ × 38`
- Annual energy: sum of monthly total MJ.
- EUI: `annual_energy_MJ / building_area_m2`
- Energy per person: `annual_energy_MJ / occupants`
- HDD/CDD base temperature: `18°C`
- High consumption: `EUI > configured_standard_EUI`
- Default rating:
  - A: `< 100 MJ/m².year`
  - B: `100–150 MJ/m².year`
  - C: `150–200 MJ/m².year`
  - D: `200–300 MJ/m².year`
  - E: `> 300 MJ/m².year`

## Compliance Notes

The implementation keeps مبحث ۱۹ benchmarks configurable because final project benchmark values may vary by climate zone, building geometry, envelope class, and system definitions. Default values include:

- Efficient residential reference: `90 kWh/m².year ≈ 324 MJ/m².year`
- Inefficient range reference: up to `500 kWh/m².year ≈ 1800 MJ/m².year`

The application uses professional audit indices while keeping the workflow student-friendly.
