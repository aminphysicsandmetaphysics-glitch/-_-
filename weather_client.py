"""Automatic weather data acquisition.

Replaces manual weather entry / Excel upload for the common case: given a
city name (or explicit coordinates), geocode it and pull a full year of
daily historical weather from Open-Meteo's free, keyless historical
archive (ERA5 reanalysis, global coverage, no signup required):

    Geocoding:  https://geocoding-api.open-meteo.com/v1/search
    Archive:    https://archive-api.open-meteo.com/v1/archive

Network note: this client is not reachable from Anthropic's sandboxed
development container (its egress allowlist does not include
open-meteo.com), so it is covered by unit tests against a mocked HTTP
transport rather than a live call. It calls real, documented, keyless
endpoints and will work as soon as it runs anywhere with normal internet
access (Render, Docker on a normal host, etc.).
"""

from dataclasses import dataclass
from datetime import date, timedelta

import httpx

GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

DAILY_VARIABLES = [
    "temperature_2m_max",
    "temperature_2m_min",
    "temperature_2m_mean",
    "relative_humidity_2m_mean",
    "shortwave_radiation_sum",
    "precipitation_sum",
    "wind_speed_10m_max",
]


class WeatherLookupError(RuntimeError):
    """Raised when a city cannot be geocoded or the archive call fails."""


@dataclass
class GeocodeResult:
    name: str
    latitude: float
    longitude: float
    country: str | None = None
    admin1: str | None = None


def geocode_city(city_name: str, client: httpx.Client | None = None) -> GeocodeResult:
    owns_client = client is None
    client = client or httpx.Client(timeout=15.0)
    try:
        response = client.get(GEOCODING_URL, params={"name": city_name, "count": 1, "language": "en"})
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results") or []
        if not results:
            raise WeatherLookupError(f"No geocoding match for '{city_name}'.")
        top = results[0]
        return GeocodeResult(
            name=top.get("name", city_name),
            latitude=top["latitude"],
            longitude=top["longitude"],
            country=top.get("country"),
            admin1=top.get("admin1"),
        )
    finally:
        if owns_client:
            client.close()


def fetch_daily_weather(
    latitude: float,
    longitude: float,
    start_date: date,
    end_date: date,
    client: httpx.Client | None = None,
) -> list[dict]:
    owns_client = client is None
    client = client or httpx.Client(timeout=30.0)
    try:
        response = client.get(
            ARCHIVE_URL,
            params={
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "daily": ",".join(DAILY_VARIABLES),
                "timezone": "auto",
            },
        )
        response.raise_for_status()
        payload = response.json()
        daily = payload.get("daily")
        if not daily or "time" not in daily:
            raise WeatherLookupError("Archive API returned no daily series.")
        rows = []
        for index, day in enumerate(daily["time"]):
            rows.append({
                "date": date.fromisoformat(day),
                "temp_min": _at(daily, "temperature_2m_min", index),
                "temp_max": _at(daily, "temperature_2m_max", index),
                "temp_avg": _at(daily, "temperature_2m_mean", index),
                "humidity": _at(daily, "relative_humidity_2m_mean", index),
                "solar_radiation": _at(daily, "shortwave_radiation_sum", index),
                "rainfall": _at(daily, "precipitation_sum", index),
                "wind_speed": _at(daily, "wind_speed_10m_max", index),
            })
        return rows
    finally:
        if owns_client:
            client.close()


def _at(daily: dict, key: str, index: int) -> float | None:
    series = daily.get(key)
    if not series or index >= len(series):
        return None
    value = series[index]
    return None if value is None else float(value)


def auto_fetch_weather_for_building(
    city: str,
    latitude: float | None,
    longitude: float | None,
    reference_end_date: date | None = None,
    client: httpx.Client | None = None,
) -> dict:
    """Resolve coordinates (explicit if given, else geocoded from city name)
    and pull the most recent full year of daily weather. Returns both the
    resolved location and the daily rows so the caller can persist them via
    the existing WeatherData upsert path."""
    reference_end_date = reference_end_date or (date.today() - timedelta(days=3))  # archive lags ~2-3 days
    start_date = reference_end_date.replace(year=reference_end_date.year - 1) + timedelta(days=1)

    location_label = city
    if latitude is None or longitude is None:
        geocoded = geocode_city(city, client=client)
        latitude, longitude = geocoded.latitude, geocoded.longitude
        location_label = geocoded.name

    rows = fetch_daily_weather(latitude, longitude, start_date, reference_end_date, client=client)
    return {
        "resolved_city": location_label,
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": reference_end_date,
        "rows": rows,
    }
