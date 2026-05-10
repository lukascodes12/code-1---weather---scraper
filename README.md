# Python Weather Scraper

A beginner-friendly command-line weather scraper written in Python.

It looks up any city, fetches the **current conditions** and a **7-day forecast**,
prints them to the terminal, and saves the results to a JSON file.

**Powered by [Open-Meteo](https://open-meteo.com) — free, no API key required.**

---

## What you'll learn

- Making HTTP requests with the `requests` library
- Parsing JSON responses from a real API
- Structuring a Python script into small, focused functions
- Writing tests with `unittest` and mocking external services

---

## Project structure

```
weather_scraper.py       # main script
test_weather_scraper.py  # unit tests (no internet needed)
requirements.txt         # dependencies
```

---

## Setup

**1. Install Python 3.8+**
Download from https://python.org if you don't have it.

**2. Install the dependency**

```bash
pip install -r requirements.txt
```

---

## Running the scraper

```bash
python weather_scraper.py
```

You'll be prompted to type a city name:

```
=== Python Weather Scraper ===
Powered by Open-Meteo (https://open-meteo.com)

Enter a city name: Tokyo

Looking up 'Tokyo'...
Found: Tokyo, Japan (35.6895, 139.6917)
Fetching weather data...

==================================================
  Weather for Tokyo, Japan
==================================================
  Condition   : Partly cloudy
  Temperature : 24.1 °C  (feels like 25.8 °C)
  Humidity    : 72 %
  Wind speed  : 11.3 km/h
  Observed at : 2024-06-15T09:00

  7-Day Forecast:
  Date         Condition                 Max    Min     Rain
  -----------------------------------------------------------------
  2024-06-15   Partly cloudy           24.1°C 18.3°C    0.0 mm
  ...

  Results saved to: weather_tokyo.json
```

The JSON file is saved in the same folder as `weather_scraper.py`.

---

## Running the tests

The tests use Python's built-in `unittest` and fake (mock) API responses,
so no internet connection is needed.

```bash
python test_weather_scraper.py
```

Expected output:

```
Ran 15 tests in 0.006s

OK
```

---

## How it works (step by step)

| Step | Function | What it does |
|------|----------|--------------|
| 1 | `get_coordinates` | Sends a city name to the geocoding API and gets back lat/lon |
| 2 | `fetch_weather`   | Sends lat/lon to the weather API and gets back raw JSON |
| 3 | `parse_weather`   | Converts raw JSON into a clean Python dictionary |
| 4 | `print_weather`   | Formats and prints the results to the terminal |
| 5 | `save_to_file`    | Writes the clean dictionary to a `.json` file |

---

## Customisation ideas (once you're comfortable)

- Add `--city` as a command-line argument so you don't need the prompt
- Support Fahrenheit with a `--units imperial` flag
- Schedule it with `cron` to log weather data every hour
- Plot the 7-day temperature range with `matplotlib`
