from datetime import date

import httpx
import pytest

from app.services import weather_client


def _mock_client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_geocode_city_parses_first_result():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "geocoding-api" in str(request.url)
        return httpx.Response(200, json={"results": [{"name": "Jajarm", "latitude": 36.95, "longitude": 56.38, "country": "Iran", "admin1": "North Khorasan"}]})

    result = weather_client.geocode_city("Jajarm", client=_mock_client(handler))
    assert result.latitude == 36.95
    assert result.name == "Jajarm"


def test_geocode_city_raises_on_no_match():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"results": []})

    with pytest.raises(weather_client.WeatherLookupError):
        weather_client.geocode_city("Nonexistent Place", client=_mock_client(handler))


def test_fetch_daily_weather_parses_rows():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "archive-api" in str(request.url)
        return httpx.Response(200, json={
            "daily": {
                "time": ["2025-01-01", "2025-01-02"],
                "temperature_2m_max": [5.0, 6.0],
                "temperature_2m_min": [-3.0, -2.0],
                "temperature_2m_mean": [1.0, 2.0],
                "relative_humidity_2m_mean": [55, 60],
                "shortwave_radiation_sum": [10.0, 11.0],
                "precipitation_sum": [0.0, 1.2],
                "wind_speed_10m_max": [12.0, 14.0],
            }
        })

    rows = weather_client.fetch_daily_weather(36.95, 56.38, date(2025, 1, 1), date(2025, 1, 2), client=_mock_client(handler))
    assert len(rows) == 2
    assert rows[0]["date"] == date(2025, 1, 1)
    assert rows[0]["temp_avg"] == 1.0
    assert rows[1]["humidity"] == 60


def test_auto_fetch_weather_geocodes_then_fetches_when_no_coordinates_given():
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        if "geocoding-api" in str(request.url):
            return httpx.Response(200, json={"results": [{"name": "Jajarm", "latitude": 36.95, "longitude": 56.38}]})
        return httpx.Response(200, json={"daily": {"time": ["2025-06-01"], "temperature_2m_mean": [25.0]}})

    result = weather_client.auto_fetch_weather_for_building(
        "Jajarm", latitude=None, longitude=None,
        reference_end_date=date(2025, 6, 1),
        client=_mock_client(handler),
    )
    assert result["latitude"] == 36.95
    assert any("geocoding-api" in url for url in calls)
    assert any("archive-api" in url for url in calls)


def test_auto_fetch_weather_skips_geocoding_when_coordinates_given():
    def handler(request: httpx.Request) -> httpx.Response:
        assert "geocoding-api" not in str(request.url)
        return httpx.Response(200, json={"daily": {"time": ["2025-06-01"], "temperature_2m_mean": [25.0]}})

    result = weather_client.auto_fetch_weather_for_building(
        "Jajarm", latitude=36.95, longitude=56.38,
        reference_end_date=date(2025, 6, 1),
        client=_mock_client(handler),
    )
    assert result["latitude"] == 36.95
