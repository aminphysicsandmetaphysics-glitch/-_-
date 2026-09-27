"""Energy-signature regression (a.k.a. change-point regression).

This is the standard statistical baselining technique used in utility
measurement & verification (M&V) work -- the same family of method
described in IPMVP Option C ("whole facility") -- adapted here to run
per-building from as few as 12 monthly bills:

    total_mj[i] = baseload + heating_slope * HDD[i] + cooling_slope * CDD[i] + error[i]

Fitting this by ordinary least squares against the building's *own*
12 months of bills and matching degree-days gives three genuinely
data-driven, building-specific numbers:

* ``baseload_mj_per_month``   -- weather-independent consumption (lighting,
  appliances, standby loads, domestic hot water, cooking). A high baseload
  relative to peers is itself an actionable finding independent of climate.
* ``heating_signature_mj_per_hdd`` -- how many MJ this specific home & its
  heating system actually burn per heating-degree-day, measured from its
  bills (as opposed to the theoretical value from the envelope model in
  ``thermal.py``). Comparing the two is the most powerful diagnostic this
  platform offers (see ``thermal.compare_theoretical_to_billed``).
* ``cooling_signature_mj_per_cdd`` -- analogous, for cooling.
* ``r_squared`` -- how well a simple weather-driven model explains this
  home's billing pattern at all; a low R^2 is itself a meaningful, honest
  signal that consumption is dominated by something the model doesn't
  capture (occupancy changes, appliance replacement mid-year, billing
  errors) and that the numeric outputs should be trusted less.

With only 12 data points and 3 free parameters this is a small-sample fit
(9 degrees of freedom) -- appropriate for a Level 1/2 walkthrough audit,
not a substitute for interval-metered data, and the confidence reporting
in ``scoring.py`` reflects that.
"""

from dataclasses import dataclass

import numpy as np


@dataclass
class EnergySignature:
    baseload_mj_per_month: float
    heating_signature_mj_per_hdd: float
    cooling_signature_mj_per_cdd: float
    r_squared: float
    predicted_by_month: dict[int, float]
    residuals_by_month: dict[int, float]
    residual_std: float


def fit_energy_signature(monthly_energy: list[dict], monthly_degree_days: dict[int, dict]) -> EnergySignature | None:
    rows = [
        (item["month"], item["total_mj"], monthly_degree_days[item["month"]]["hdd"], monthly_degree_days[item["month"]]["cdd"])
        for item in monthly_energy
        if item["month"] in monthly_degree_days
    ]
    if len(rows) < 4:
        # Not enough weather-matched billing periods for a meaningful fit;
        # the caller falls back to the flat-average anomaly method.
        return None

    months = [row[0] for row in rows]
    y = np.array([row[1] for row in rows], dtype=float)
    hdd = np.array([row[2] for row in rows], dtype=float)
    cdd = np.array([row[3] for row in rows], dtype=float)
    design = np.column_stack([np.ones_like(y), hdd, cdd])

    coefficients, _, _, _ = np.linalg.lstsq(design, y, rcond=None)
    baseload, heating_slope, cooling_slope = coefficients

    predicted = design @ coefficients
    residuals = y - predicted
    ss_res = float(np.sum(residuals ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    r_squared = 1 - ss_res / ss_tot if ss_tot > 0 else 0.0
    residual_std = float(np.std(residuals, ddof=min(3, len(y) - 1))) if len(y) > 3 else float(np.std(residuals))

    return EnergySignature(
        baseload_mj_per_month=max(float(baseload), 0.0),
        heating_signature_mj_per_hdd=max(float(heating_slope), 0.0),
        cooling_signature_mj_per_cdd=max(float(cooling_slope), 0.0),
        r_squared=round(r_squared, 3),
        predicted_by_month=dict(zip(months, predicted.tolist())),
        residuals_by_month=dict(zip(months, residuals.tolist())),
        residual_std=residual_std,
    )
