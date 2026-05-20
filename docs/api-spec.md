# API Specification

Base URL: `http://localhost:8000/api/v1`

## Buildings

### Create Building

`POST /buildings`

```json
{
  "project_name": "Jajarm Residential Case Study",
  "city": "جاجرم",
  "address": "North Khorasan, Jajarm",
  "area_m2": 150,
  "floors": 2,
  "year_built": 2005,
  "occupants": 4,
  "building_type": "Residential",
  "heating_system": "old boiler",
  "cooling_system": "old split / low EER",
  "lighting_type": "incandescent",
  "window_type": "single",
  "wall_type": "brick wall",
  "roof_type": "flat roof",
  "has_insulation": false,
  "has_thermostat": false,
  "has_shading": false,
  "orientation": "south-west"
}
```

### List Buildings

`GET /buildings`

## Energy Bills

### Post Monthly Bills

`POST /buildings/{building_id}/bills`

```json
[
  {
    "year": 1402,
    "month": 1,
    "electricity_kwh": 220,
    "gas_m3": 180,
    "electricity_cost": 1200000,
    "gas_cost": 900000
  },
  {
    "year": 1402,
    "month": 2,
    "electricity_kwh": 200,
    "gas_m3": 150,
    "electricity_cost": 1100000,
    "gas_cost": 800000
  }
]
```

Monthly rows are compatible with the `ممیزی.xlsx` shape:

- Month
- Electricity consumption
- Gas consumption
- Total MJ
- MJ/m²
- MJ/person

## Weather

### Post Weather Data

`POST /buildings/{building_id}/weather`

```json
[
  {
    "city": "جاجرم",
    "date": "2024-03-20",
    "temp_min": 8.2,
    "temp_max": 22.1,
    "temp_avg": 15.2
  },
  {
    "city": "جاجرم",
    "date": "2024-03-21",
    "temp_min": 7.9,
    "temp_max": 23.4,
    "temp_avg": 15.7
  }
]
```

### Import Weather Excel

`POST /buildings/{building_id}/weather/import`

Multipart field: `file`

Required columns:

- `Date`
- `Temp Avg` or normalized `temp_avg`
- Optional: `Temp Min`, `Temp Max`

## Audit

### Run Audit

`POST /buildings/{building_id}/audit/run`

Example response:

```json
{
  "id": 1,
  "building_id": 1,
  "total_energy_mj": 102384,
  "eui": 682.56,
  "energy_per_person": 25596,
  "hdd": 1720.4,
  "cdd": 1348.2,
  "energy_rating": "E",
  "standard_eui": 324,
  "high_consumption_flag": true,
  "monthly": [
    {
      "month": 1,
      "electricity_kwh": 220,
      "gas_m3": 180,
      "electricity_mj": 792,
      "gas_mj": 6840,
      "total_mj": 7632,
      "energy_per_m2": 50.88,
      "energy_per_person": 1908
    }
  ],
  "recommendations": [
    {
      "id": 1,
      "building_id": 1,
      "category": "envelope",
      "recommendation": "Replace single glazing with low-emissivity double-glazed windows.",
      "impact_level": "high",
      "status": "planned"
    }
  ]
}
```

### Latest Audit

`GET /buildings/{building_id}/audit/latest`

## Reports

- `GET /buildings/{building_id}/reports/pdf`
- `GET /buildings/{building_id}/reports/excel`
