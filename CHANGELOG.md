# Changelog -- Precision & Product Upgrade Pass

This pass took the platform from a working bill-benchmarking MVP to a
physics- and statistics-grounded audit engine with real multi-tenant
auth, quantified financial recommendations, and a redesigned UI. Everything
below is implemented and covered by the automated test suite
(`backend/tests`, 26 tests passing).

## Precision & reliability (the core ask)

- **`services/thermal.py`** -- first-principles building-envelope heat-loss
  engine (steady-state UA / degree-day method). Computes theoretical
  heating/cooling demand from wall/roof/floor/window U-values and
  infiltration, independent of billed energy.
- **`services/catalogs.py`** -- reference catalogs of typical U-values
  (by construction type) and typical equipment power draw, so users pick
  from a list instead of needing to know technical values themselves.
- **`services/regression.py`** -- energy-signature (change-point)
  regression, the standard M&V/IPMVP technique: separates weather-
  independent baseload from heating/cooling energy using the building's
  own 12 months of bills, and reports R² as a data-quality signal.
- **Weather-normalized anomaly detection** (`analytics.detect_monthly_anomalies`)
  -- flags months that deviate from their *own weather-adjusted
  expectation* (regression residual > 2 std) instead of a flat annual
  average, which previously mis-flagged ordinary winter/summer peaks.
- **`services/sensitivity.py`** -- per-building local sensitivity
  analysis: recomputes the physics model with each envelope component
  swapped for a realistic upgrade, ranking wall/roof/window/floor/
  air-sealing by the actual MJ saved for *this specific building*.
- **`services/scoring.py`** -- composite 0-100 performance score, plus an
  explicit confidence indicator (data completeness + regression fit)
  reported alongside every result rather than a single unqualified number.
- **`services/economics.py`** -- every recommendation now carries
  estimated annual savings (MJ, Toman), avoided CO2, an installed-cost
  range, and simple payback -- envelope items priced from the physics
  swap-comparison directly; equipment/behavioral items priced from
  published typical-savings percentages (clearly tagged by source).
- **`services/weather_client.py`** -- automatic weather acquisition from
  Open-Meteo's free historical archive (geocodes the city, pulls a full
  year of daily data). No more manual entry for the common case.

## Product / commercial readiness

- **JWT authentication + multi-tenancy** (`core/auth.py`): buildings are
  now scoped to an owner account. The previous version had no auth at
  all with `CORS_ORIGINS: "*"` -- open to anyone with the URL.
- Fixed a real bug: `classify_energy_rating()` was dead code with
  thresholds on the wrong numeric scale relative to the rating system
  actually in use. Removed.
- Full pytest suite added (unit + API integration, 26 tests) -- there
  were previously zero tests.
- `render.yaml`: replaced the open CORS wildcard with explicit origins,
  and JWT_SECRET is now a Render-generated secret rather than a
  hardcoded fallback.

## Frontend

- Full visual redesign: a thermal/infrared-inspired palette (cool blue
  = efficient, amber/ember = wasteful) carried through a custom
  `EnergyGauge` dial, metric cards, and the recommendation list: RTL-
  correct layout using logical CSS properties, Vazirmatn typeface.
- Login/register screens wired to the new auth backend.
- Catalog-driven dropdowns for envelope materials and equipment (auto-
  fills U-values / typical power draw instead of free-typed numbers).
- One-click weather auto-fetch button (falls back to Excel upload).
- Analysis page now surfaces the performance score, confidence badge,
  envelope-vs-billed diagnosis, energy-signature stats, carbon
  footprint, and quantified/ranked recommendations with payback periods.
- `npm run build` passes cleanly (TypeScript strict + Vite production
  build).

## Known, explicitly-scoped gaps (next candidates, not silently skipped)

- Tariff and retrofit-cost figures in `economics.py`/`.env.example` are
  editable placeholders -- recalibrate to current local pricing before
  a real client-facing number goes out.
- PDF/Excel report templates (`services/reports.py`) were not yet
  extended to print the new performance score / confidence / carbon
  sections -- they still generate correctly, just without the newest
  fields laid out.
- Database is still on Render's free Postgres (expires after 90 days of
  the *database's* creation if not upgraded) -- migration to a
  non-expiring free host (Neon) is the deliberately-deferred next step.
