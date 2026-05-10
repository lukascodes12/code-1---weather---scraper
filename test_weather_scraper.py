"""
Tests for weather_scraper.py
Run with: python test_weather_scraper.py
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from weather_scraper import (
    fetch_weather,
    get_coordinates,
    parse_weather,
    WMO_CODES,
)

# ---------------------------------------------------------------------------
# Fake API responses (so tests never hit the real internet)
# ---------------------------------------------------------------------------

FAKE_GEOCODE_RESPONSE = {
    "results": [
        {
            "name": "London",
            "country": "United Kingdom",
            "latitude": 51.5085,
            "longitude": -0.1257,
            "timezone": "Europe/London",
        }
    ]
}

FAKE_WEATHER_RESPONSE = {
    "current": {
        "time": "2024-06-15T12:00",
        "temperature_2m": 18.3,
        "apparent_temperature": 16.7,
        "relative_humidity_2m": 65,
        "wind_speed_10m": 14.2,
        "weather_code": 2,
    },
    "daily": {
        "time": [
            "2024-06-15", "2024-06-16", "2024-06-17",
            "2024-06-18", "2024-06-19", "2024-06-20", "2024-06-21",
        ],
        "weather_code": [2, 61, 63, 3, 1, 0, 2],
        "temperature_2m_max": [19.1, 16.5, 15.8, 17.2, 20.0, 22.3, 21.5],
        "temperature_2m_min": [12.3, 11.0, 10.5, 11.8, 13.2, 14.1, 13.9],
        "precipitation_sum": [0.0, 3.2, 8.7, 0.5, 0.0, 0.0, 0.1],
    },
}


def make_mock_response(data: dict) -> MagicMock:
    """Build a requests.Response mock that returns *data* as JSON."""
    mock = MagicMock()
    mock.raise_for_status = MagicMock()
    mock.json.return_value = data
    return mock


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetCoordinates(unittest.TestCase):

    @patch("weather_scraper.requests.get")
    def test_returns_location_dict(self, mock_get):
        mock_get.return_value = make_mock_response(FAKE_GEOCODE_RESPONSE)

        result = get_coordinates("London")

        self.assertEqual(result["name"], "London")
        self.assertEqual(result["country"], "United Kingdom")
        self.assertAlmostEqual(result["latitude"], 51.5085)
        self.assertAlmostEqual(result["longitude"], -0.1257)

    @patch("weather_scraper.requests.get")
    def test_raises_for_unknown_city(self, mock_get):
        mock_get.return_value = make_mock_response({"results": []})

        with self.assertRaises(ValueError) as ctx:
            get_coordinates("XxNotACityxX")

        self.assertIn("City not found", str(ctx.exception))

    @patch("weather_scraper.requests.get")
    def test_raises_for_empty_results_key_missing(self, mock_get):
        mock_get.return_value = make_mock_response({})  # no "results" key at all

        with self.assertRaises(ValueError):
            get_coordinates("Nowhere")


class TestFetchWeather(unittest.TestCase):

    @patch("weather_scraper.requests.get")
    def test_returns_raw_dict(self, mock_get):
        mock_get.return_value = make_mock_response(FAKE_WEATHER_RESPONSE)

        location = {
            "name": "London", "country": "United Kingdom",
            "latitude": 51.5085, "longitude": -0.1257,
            "timezone": "Europe/London",
        }
        result = fetch_weather(location)

        self.assertIn("current", result)
        self.assertIn("daily", result)

    @patch("weather_scraper.requests.get")
    def test_correct_params_sent(self, mock_get):
        mock_get.return_value = make_mock_response(FAKE_WEATHER_RESPONSE)

        location = {
            "name": "London", "country": "United Kingdom",
            "latitude": 51.5085, "longitude": -0.1257,
            "timezone": "Europe/London",
        }
        fetch_weather(location)

        call_kwargs = mock_get.call_args[1]["params"]
        self.assertEqual(call_kwargs["latitude"], 51.5085)
        self.assertEqual(call_kwargs["forecast_days"], 7)


class TestParseWeather(unittest.TestCase):

    def setUp(self):
        self.location = {
            "name": "London", "country": "United Kingdom",
            "latitude": 51.5085, "longitude": -0.1257,
        }

    def test_city_and_country_preserved(self):
        result = parse_weather(self.location, FAKE_WEATHER_RESPONSE)
        self.assertEqual(result["city"], "London")
        self.assertEqual(result["country"], "United Kingdom")

    def test_current_temperature(self):
        result = parse_weather(self.location, FAKE_WEATHER_RESPONSE)
        self.assertEqual(result["current"]["temperature_c"], 18.3)
        self.assertEqual(result["current"]["feels_like_c"], 16.7)
        self.assertEqual(result["current"]["humidity_pct"], 65)

    def test_current_condition_decoded(self):
        result = parse_weather(self.location, FAKE_WEATHER_RESPONSE)
        self.assertEqual(result["current"]["condition"], "Partly cloudy")  # code 2

    def test_forecast_has_seven_days(self):
        result = parse_weather(self.location, FAKE_WEATHER_RESPONSE)
        self.assertEqual(len(result["forecast"]), 7)

    def test_forecast_first_day(self):
        result = parse_weather(self.location, FAKE_WEATHER_RESPONSE)
        day = result["forecast"][0]
        self.assertEqual(day["date"], "2024-06-15")
        self.assertEqual(day["max_temp_c"], 19.1)
        self.assertEqual(day["min_temp_c"], 12.3)
        self.assertEqual(day["precipitation_mm"], 0.0)

    def test_forecast_condition_decoded(self):
        result = parse_weather(self.location, FAKE_WEATHER_RESPONSE)
        self.assertEqual(result["forecast"][1]["condition"], "Slight rain")  # code 61

    def test_unknown_wmo_code_falls_back(self):
        raw = {
            "current": {**FAKE_WEATHER_RESPONSE["current"], "weather_code": 9999},
            "daily": FAKE_WEATHER_RESPONSE["daily"],
        }
        result = parse_weather(self.location, raw)
        self.assertEqual(result["current"]["condition"], "Unknown")

    def test_scraped_at_present(self):
        result = parse_weather(self.location, FAKE_WEATHER_RESPONSE)
        self.assertIn("scraped_at", result)
        self.assertTrue(result["scraped_at"].endswith("Z"))


class TestWmoCodes(unittest.TestCase):

    def test_clear_sky(self):
        self.assertEqual(WMO_CODES[0], "Clear sky")

    def test_thunderstorm(self):
        self.assertEqual(WMO_CODES[95], "Thunderstorm")


if __name__ == "__main__":
    unittest.main(verbosity=2)
