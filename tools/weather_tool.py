"""Weather tool using Open-Meteo (geocoding + daily forecast)."""

from datetime import date, datetime

import requests
from langchain_core.tools import tool


GEO_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
TIMEOUT = (3.0, 10.0)  # (connect, read)


def _parse_date(date_str: str) -> str:
    """Validate YYYY-MM-DD and return normalized string."""
    datetime.strptime(date_str, "%Y-%m-%d")
    return date_str


def _get_json(resp: requests.Response) -> dict:
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("Unexpected JSON payload")
    return data


def _geocode(city: str, country_code: str | None):
    params = {"name": city, "count": 1}
    if country_code:
        params["country_code"] = country_code

    data = _get_json(requests.get(GEO_URL, params=params, timeout=TIMEOUT))
    results = data.get("results")
    if not results:
        raise ValueError("City not found")

    r0 = results[0]
    return {
        "name": r0.get("name") or city,
        "lat": r0["latitude"],
        "lon": r0["longitude"],
        "timezone": r0.get("timezone") or "auto",
        "country": r0.get("country"),
        "admin1": r0.get("admin1"),
    }


def _daily(lat: float, lon: float, timezone: str) -> dict:
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum",
        "timezone": timezone or "auto",
    }
    return _get_json(requests.get(FORECAST_URL, params=params, timeout=TIMEOUT))


@tool
def get_weather_forecast(city: str, date_str: str = "", country_code: str = "") -> str:
    """Get a daily weather forecast for a city and a specific date.

    Use this when the user asks about weather, temperature, rain, or "will it rain".

    Args:
        city: City name (e.g., "Strasbourg", "Tokyo"). Required.
        date_str: Target date in YYYY-MM-DD. If empty, defaults to today.
        country_code: Optional ISO 3166-1 alpha-2 code to disambiguate (e.g., "FR", "US").

    Returns:
        A single short sentence, e.g.:
        "Weather in Strasbourg, Grand Est, France on 2026-04-02: min 5C, max 15C, precipitation 1.3mm."

    Failure modes:
        - If city is unknown: returns an error string.
        - If date_str is invalid: returns "Error: invalid date. Use YYYY-MM-DD."
        - If the API times out or fails: returns an error string.
    """

    city = (city or "").strip()
    if not city:
        return "Error: city is required."

    date_str = (date_str or "").strip()
    if not date_str:
        date_str = date.today().strftime("%Y-%m-%d")
    else:
        try:
            date_str = _parse_date(date_str)
        except ValueError:
            return "Error: invalid date. Use YYYY-MM-DD."

    cc = (country_code or "").strip().upper() or None

    try:
        geo = _geocode(city, cc)
        data = _daily(geo["lat"], geo["lon"], geo["timezone"])

        daily = data.get("daily")
        if not isinstance(daily, dict):
            return "Error: weather payload is missing daily data."

        dates = daily.get("time")
        if not isinstance(dates, list) or not dates:
            return "Error: weather payload is missing dates."

        if date_str not in dates:
            return f"Forecast not available for {geo['name']} on {date_str}."

        idx = dates.index(date_str)

        def at(key: str):
            arr = daily.get(key)
            if not isinstance(arr, list) or idx >= len(arr):
                raise KeyError(key)
            return arr[idx]

        t_max = at("temperature_2m_max")
        t_min = at("temperature_2m_min")
        rain = at("precipitation_sum")

        place = geo["name"]
        if geo.get("admin1"):
            place = f"{place}, {geo['admin1']}"
        if geo.get("country"):
            place = f"{place}, {geo['country']}"

        return f"Weather in {place} on {date_str}: min {t_min}C, max {t_max}C, precipitation {rain}mm."

    except requests.Timeout:
        return "Error: weather request timed out."
    except requests.HTTPError as e:
        code = getattr(e.response, "status_code", None)
        return f"Error: weather service returned HTTP {code}." if code else "Error: weather service failed."
    except requests.RequestException:
        return "Error: network error while fetching weather."
    except ValueError:
        return f"Error: could not find city '{city}'."
    except KeyError:
        return "Error: weather payload is missing data."
