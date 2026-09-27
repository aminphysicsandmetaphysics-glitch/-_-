"""Turns the audit's various signals into two single numbers a non-expert
(a homeowner, or an investor skimming a report) can read at a glance:

* ``performance_score`` (0-100) -- how efficient this home is, anchored to
  the climate-normalized EUI ratio already computed in ``analytics.py``,
  adjusted down for unexplained consumption volatility (anomaly months).
  This is a *reporting* convenience over the existing rating -- it does
  not replace the A-E label, which stays the primary, standards-aligned
  output.
* ``confidence`` (0-100) -- how much to trust the numbers above, based on
  how much data actually backed them (bill-months present, weather
  coverage, and the energy-signature regression's R^2). A tool that
  reports one confident-looking number regardless of input quality is
  less trustworthy than one that says so when its inputs are thin.
"""


def calculate_performance_score(energy_index_ratio: float, anomaly_count: int) -> int:
    # ratio 0.6 (rating A cutoff) -> 100; ratio 1.6 -> 0; linear between.
    raw = 100 - (energy_index_ratio - 0.6) * 100
    penalty = min(anomaly_count * 5, 15)
    return int(max(0, min(100, round(raw - penalty))))


def calculate_confidence(
    bill_months: int,
    weather_days_covered: int,
    r_squared: float | None,
) -> dict:
    months_score = min(bill_months / 12, 1.0) * 40
    weather_score = min(weather_days_covered / 300, 1.0) * 30
    fit_score = (r_squared if r_squared is not None else 0.3) * 30
    total = round(months_score + weather_score + fit_score)
    if total >= 80:
        level = "high"
    elif total >= 55:
        level = "medium"
    else:
        level = "low"
    return {
        "confidence_score": total,
        "confidence_level": level,
        "bill_months_used": bill_months,
        "weather_days_used": weather_days_covered,
        "regression_r_squared": r_squared,
    }
