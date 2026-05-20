# Frontend Wireframes and Component Hierarchy

## App Shell

- `App`
- `HeroHeader`
- `StepNavigation`
- `Dashboard`
- `CreateProject`
- `BillsInput`
- `WeatherInput`
- `Analysis`
- `Reports`

## Guided 7-Step Workflow

### 1. Dashboard

- Project list
- Summary cards:
  - Latest EUI
  - Average energy per person
  - High-consumption buildings count
- Alert area:
  - `مصرف انرژی بالاتر از استاندارد`

### 2. Create Audit Project

Fields:

- Project name
- City, default `جاجرم`
- Address
- Area
- Floors
- Year built
- Occupants
- Building type
- Heating/cooling systems
- Window, wall, roof types
- Insulation, thermostat, shading
- Orientation

### 3. Energy Bills Input

Excel-like table:

- Month: فروردین تا اسفند
- Electricity `kWh`
- Gas `m³`
- Electricity cost
- Gas cost

### 4. Weather Data Input

- Excel upload guidance
- Weather preview
- Validation target: at least 365 days
- Sample Jajarm data generator for student use

### 5. Energy Analysis

Charts:

- Monthly electricity
- Monthly gas
- Monthly total energy in MJ

Indices:

- Annual total energy
- EUI
- Energy per person
- HDD/CDD

### 6. Energy Rating and Recommendations

- A–E color-coded rating badge
- مبحث ۱۹ benchmark comparison
- Recommendation cards with category and impact

### 7. Report Generation

- Download PDF
- Download Excel

## Localization Strategy

UI labels are bilingual-friendly. Production localization can replace static labels with translation keys such as:

- `audit.dashboard.title`
- `audit.project.area_m2`
- `audit.results.eui`
- `audit.alert.high_consumption`
