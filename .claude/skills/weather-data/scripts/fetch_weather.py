#!/usr/bin/env python3
"""
Weather Data Fetcher for Claude Code Skills
Fetches real-time weather data using Open-Meteo API (free, no auth required)
"""

import argparse
import json
import sys
import subprocess
from datetime import datetime
from pathlib import Path


def get_coordinates(location: str) -> tuple[float, float]:
    """
    Convert location name to coordinates using geocoding.
    Uses Open-Meteo Geocoding API (free, no authentication required)
    """
    try:
        import httpx
    except ImportError:
        print(
            json.dumps({
                "error": "httpx not installed",
                "message": "Install httpx: pip install httpx"
            }),
            file=sys.stderr
        )
        sys.exit(1)

    # Check if location is already coordinates
    if "," in location:
        try:
            lat, lon = location.split(",")
            return float(lat.strip()), float(lon.strip())
        except ValueError:
            pass

    # Geocode the location
    try:
        with httpx.Client() as client:
            response = client.get(
                "https://geocoding-api.open-meteo.com/v1/search",
                params={
                    "name": location,
                    "count": 1,
                    "language": "en",
                    "format": "json"
                }
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("results"):
                return None

            result = data["results"][0]
            return result["latitude"], result["longitude"], result
    except Exception as e:
        print(
            json.dumps({
                "error": "geocoding_failed",
                "message": f"Could not find location: {location}",
                "details": str(e)
            }),
            file=sys.stderr
        )
        sys.exit(1)


def fetch_weather(latitude: float, longitude: float, units: str = "metric") -> dict:
    """
    Fetch weather data from Open-Meteo API
    """
    try:
        import httpx
    except ImportError:
        print(
            json.dumps({
                "error": "httpx not installed",
                "message": "Install httpx: pip install httpx"
            }),
            file=sys.stderr
        )
        sys.exit(1)

    try:
        with httpx.Client() as client:
            response = client.get(
                "https://api.open-meteo.com/v1/forecast",
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": (
                        "temperature_2m,relative_humidity_2m,"
                        "apparent_temperature,is_day,weather_code,"
                        "wind_speed_10m,wind_direction_10m"
                    ),
                    "timezone": "auto",
                    "temperature_unit": "celsius" if units == "metric" else "fahrenheit",
                    "wind_speed_unit": "ms" if units == "metric" else "mph"
                }
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(
            json.dumps({
                "error": "weather_fetch_failed",
                "message": f"Could not fetch weather data",
                "details": str(e)
            }),
            file=sys.stderr
        )
        sys.exit(1)


def decode_weather_code(code: int, is_day: bool) -> tuple[str, str]:
    """
    Decode WMO weather code to human-readable description
    """
    codes = {
        0: ("Clear sky", "Sunny" if is_day else "Clear"),
        1: ("Mainly clear", "Mostly sunny" if is_day else "Mostly clear"),
        2: ("Partly cloudy", "Partly cloudy"),
        3: ("Overcast", "Overcast"),
        45: ("Foggy", "Foggy"),
        48: ("Depositing rime fog", "Foggy"),
        51: ("Light drizzle", "Light drizzle"),
        53: ("Moderate drizzle", "Drizzle"),
        55: ("Dense drizzle", "Heavy drizzle"),
        61: ("Slight rain", "Light rain"),
        63: ("Moderate rain", "Moderate rain"),
        65: ("Heavy rain", "Heavy rain"),
        71: ("Slight snow", "Light snow"),
        73: ("Moderate snow", "Moderate snow"),
        75: ("Heavy snow", "Heavy snow"),
        77: ("Snow grains", "Snow"),
        80: ("Slight rain showers", "Light rain showers"),
        81: ("Moderate rain showers", "Rain showers"),
        82: ("Violent rain showers", "Violent rain showers"),
        85: ("Slight snow showers", "Light snow showers"),
        86: ("Heavy snow showers", "Heavy snow showers"),
        95: ("Thunderstorm", "Thunderstorm"),
        96: ("Thunderstorm with slight hail", "Thunderstorm with hail"),
        99: ("Thunderstorm with heavy hail", "Thunderstorm with heavy hail"),
    }
    return codes.get(code, ("Unknown", "Unknown"))


def format_output(weather_data: dict, geo_info: dict, location_str: str, units: str) -> dict:
    """
    Format raw API data into user-friendly format
    """
    current = weather_data["current"]
    timezone = weather_data["timezone"]

    # Decode weather
    condition, description = decode_weather_code(
        current["weather_code"],
        current["is_day"]
    )

    # Determine wind direction
    wind_deg = current["wind_direction_10m"]
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                  "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    direction = directions[round(wind_deg / 22.5) % 16]

    return {
        "location": {
            "city": geo_info.get("name", "Unknown"),
            "country": geo_info.get("country", ""),
            "latitude": geo_info.get("latitude", 0),
            "longitude": geo_info.get("longitude", 0),
            "timezone": timezone
        },
        "current": {
            "temperature": round(current["temperature_2m"], 1),
            "feels_like": round(current["apparent_temperature"], 1),
            "humidity": current["relative_humidity_2m"],
            "condition": condition,
            "description": description,
            "weather_code": current["weather_code"],
            "is_day": bool(current["is_day"]),
            "wind": {
                "speed": round(current["wind_speed_10m"], 1),
                "direction_degrees": current["wind_direction_10m"],
                "direction": direction,
                "unit": "m/s" if units == "metric" else "mph"
            },
            "temperature_unit": "°C" if units == "metric" else "°F"
        },
        "timestamp": current["time"],
        "units": units
    }


def main():
    parser = argparse.ArgumentParser(
        description="Fetch weather data for a location"
    )
    parser.add_argument(
        "--location",
        required=True,
        help="Location name, 'City, Country', or 'latitude,longitude'"
    )
    parser.add_argument(
        "--units",
        choices=["metric", "imperial"],
        default="metric",
        help="Temperature and speed units (default: metric)"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        default=True,
        help="Output as JSON (default)"
    )

    args = parser.parse_args()

    # Get coordinates
    coords_result = get_coordinates(args.location)
    if coords_result is None:
        print(
            json.dumps({
                "error": "location_not_found",
                "message": f"Could not find location: {args.location}"
            }),
            file=sys.stderr
        )
        sys.exit(1)

    latitude, longitude, geo_info = coords_result

    # Fetch weather
    weather_data = fetch_weather(latitude, longitude, args.units)

    # Format output
    result = format_output(weather_data, geo_info, args.location, args.units)

    # Output
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
