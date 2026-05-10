"""
Python Weather Scraper
======================
Fetches current weather and a 7-day forecast for any city using the
free Open-Meteo API (https://open-meteo.com) — no API key required.

How to run:
    python weather_scraper.py
"""

import json
import sys
from datetime import datetime

import requests

# ---------------------------------------------------------------------------
# Step 1 – Look up coordinates for a city name
# ---------------------------------------------------------------------------

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"


def get_coordinates(city_name: str) -> dict:
    """Return the first geocoding result for *city_name*, or raise if not found."""
    params = {"name": city_name, "count": 1, "language": "en", "format": "json"}
    response = requests.get(GEOCODE_URL, params=params, timeout=10)
    response.raise_for_status()  # crash loudly if the server returns an error

    data = response.json()
    results = data.get("results")
    if not results:
        raise ValueError(f"City not found: '{city_name}'. Try a different spelling.")

    location = results[0]
    return {
        "name": location["name"],
        "country": location.get("country", ""),
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": location.get("timezone", "UTC"),
    }


# ---------------------------------------------------------------------------
# Step 2 – Fetch weather data
# ---------------------------------------------------------------------------

# WMO weather codes → human-readable description
WMO_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow fall",
    73: "Moderate snow fall",
    75: "Heavy snow fall",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def fetch_weather(location: dict) -> dict:
    """Fetch current conditions and a 7-day daily forecast."""
    params = {
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "timezone": location["timezone"],
        # Current conditions we want
        "current": [
            "temperature_2m",
            "apparent_temperature",
            "relative_humidity_2m",
            "wind_speed_10m",
            "weather_code",
        ],
        # Daily forecast fields
        "daily": [
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
        ],
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
        "forecast_days": 7,
    }

    response = requests.get(WEATHER_URL, params=params, timeout=10)
    response.raise_for_status()
    return response.json()


# ---------------------------------------------------------------------------
# Step 3 – Parse the raw API response into something readable
# ---------------------------------------------------------------------------

def parse_weather(location: dict, raw: dict) -> dict:
    """Turn the raw API JSON into a clean, human-friendly dictionary."""
    current_raw = raw["current"]
    daily_raw = raw["daily"]

    current = {
        "temperature_c": current_raw["temperature_2m"],
        "feels_like_c": current_raw["apparent_temperature"],
        "humidity_pct": current_raw["relative_humidity_2m"],
        "wind_speed_kmh": current_raw["wind_speed_10m"],
        "condition": WMO_CODES.get(current_raw["weather_code"], "Unknown"),
        "observed_at": current_raw["time"],
    }

    forecast = []
    dates = daily_raw["time"]
    for i, date in enumerate(dates):
        forecast.append({
            "date": date,
            "condition": WMO_CODES.get(daily_raw["weather_code"][i], "Unknown"),
            "max_temp_c": daily_raw["temperature_2m_max"][i],
            "min_temp_c": daily_raw["temperature_2m_min"][i],
            "precipitation_mm": daily_raw["precipitation_sum"][i],
        })

    return {
        "city": location["name"],
        "country": location["country"],
        "latitude": location["latitude"],
        "longitude": location["longitude"],
        "scraped_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "current": current,
        "forecast": forecast,
    }


# ---------------------------------------------------------------------------
# Step 4 – Print a nicely formatted summary to the terminal
# ---------------------------------------------------------------------------

def print_weather(weather: dict) -> None:
    city = weather["city"]
    country = weather["country"]
    c = weather["current"]

    print(f"\n{'='*50}")
    print(f"  Weather for {city}, {country}")
    print(f"{'='*50}")
    print(f"  Condition   : {c['condition']}")
    print(f"  Temperature : {c['temperature_c']} °C  (feels like {c['feels_like_c']} °C)")
    print(f"  Humidity    : {c['humidity_pct']} %")
    print(f"  Wind speed  : {c['wind_speed_kmh']} km/h")
    print(f"  Observed at : {c['observed_at']}")
    print(f"\n  7-Day Forecast:")
    print(f"  {'Date':<12} {'Condition':<25} {'Max':>6} {'Min':>6} {'Rain':>8}")
    print(f"  {'-'*65}")
    for day in weather["forecast"]:
        print(
            f"  {day['date']:<12} {day['condition']:<25} "
            f"{day['max_temp_c']:>5}°C {day['min_temp_c']:>5}°C "
            f"{day['precipitation_mm']:>6} mm"
        )
    print()


# ---------------------------------------------------------------------------
# Step 5 – Save the results to a JSON file
# ---------------------------------------------------------------------------

def save_to_file(weather: dict, filename: str) -> None:
    with open(filename, "w") as f:
        json.dump(weather, f, indent=2)
    print(f"  Results saved to: {filename}")


# ---------------------------------------------------------------------------
# Main — ask the user for a city, run everything
# ---------------------------------------------------------------------------

def main() -> None:
    print("=== Python Weather Scraper ===")
    print("Powered by Open-Meteo (https://open-meteo.com)\n")

    city = input("Enter a city name: ").strip()
    if not city:
        print("No city entered. Exiting.")
        sys.exit(1)

    print(f"\nLooking up '{city}'...")
    try:
        location = get_coordinates(city)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except requests.RequestException as e:
        print(f"Network error during geocoding: {e}")
        sys.exit(1)

    print(f"Found: {location['name']}, {location['country']} "
          f"({location['latitude']}, {location['longitude']})")
    print("Fetching weather data...")

    try:
        raw = fetch_weather(location)
    except requests.RequestException as e:
        print(f"Network error fetching weather: {e}")
        sys.exit(1)

    weather = parse_weather(location, raw)
    print_weather(weather)

    output_file = f"weather_{city.lower().replace(' ', '_')}.json"
    save_to_file(weather, output_file)


if __name__ == "__main__":
    main()
