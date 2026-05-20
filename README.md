# Iran Residential Energy Audit Platform

Web-based SaaS-style platform for Level 1 walk-through and Level 2 detailed residential energy audits in Iran, with a climatic case study for جاجرم – استان خراسان شمالی.

## Scope

- Primary index: EUI in `MJ/m².year`.
- Utility inputs: electricity in `kWh`, natural gas in `m³`, and costs compatible with توانیر and شرکت ملی گاز bill structures.
- Climate inputs: daily `Date`, `Min Temp`, `Max Temp`, `Mean Temp` compatible with future IRIMO imports.
- Standards alignment: configurable benchmark defaults based on مبحث ۱۹ مقررات ملی ساختمان and common audit practice.
- Reports: PDF and Excel outputs for professional audit documentation.

## Architecture

- `frontend`: React + TypeScript + Recharts guided 7-step workflow.
- `backend`: FastAPI REST API, SQLAlchemy models, Pandas analytics, ReportLab/XlsxWriter reports.
- `database`: PostgreSQL schema migration scripts.
- `docs`: architecture, API examples, and frontend component hierarchy.

## Quick Start

### Docker Compose

```bash
cd energy-audit-app
docker compose up --build
```

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

### Backend

```bash
cd energy-audit-app/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Set `DATABASE_URL` in `.env` if your PostgreSQL connection differs from the default.

### Database

```bash
createdb energy_audit
psql energy_audit < ../database/migrations/001_initial_schema.sql
```

### Frontend

```bash
cd energy-audit-app/frontend
npm install
npm run dev
```

## Main Workflow

1. Create a building audit project.
2. Enter monthly electricity/gas bills similar to `ممیزی.xlsx`.
3. Upload or generate daily weather data for Jajarm.
4. Run energy analysis.
5. Review rating and مبحث ۱۹ benchmark comparison.
6. Review retrofit recommendations.
7. Download PDF and Excel reports.
