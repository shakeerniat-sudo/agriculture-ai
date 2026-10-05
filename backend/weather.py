"""OpenWeather integration for current conditions and forecast data."""

from __future__ import annotations

import os
from typing import Any

import httpx

OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"


class WeatherAPIError(Exception):
    def __init__(self, message: str, *, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class WeatherService:
    def __init__(self, api_key: str | None = None) -> None:
        configured_key = (api_key or os.getenv("OPENWEATHER_API_KEY") or "").strip()
        self.api_key = (
            None
            if configured_key.lower().startswith(("your_", "replace_"))
            else configured_key or None
        )

    def get_conditions(self, location: str) -> dict[str, Any]:
        if not self.api_key:
            raise WeatherAPIError(
                "Weather service is not configured. Add OPENWEATHER_API_KEY to the backend environment."
            )

        params: dict[str, str | int] = {
            "q": location,
            "appid": self.api_key,
            "units": "metric",
        }
        try:
            with httpx.Client(timeout=12) as client:
                current_response = client.get(
                    f"{OPENWEATHER_BASE_URL}/weather",
                    params=params,
                )
                self._check_response(current_response)
                current = current_response.json()

                coordinates = current.get("coord", {})
                latitude = coordinates.get("lat")
                longitude = coordinates.get("lon")
                if latitude is None or longitude is None:
                    raise WeatherAPIError(
                        "Weather service did not return coordinates for that location. Check the location and try again.",
                        status_code=400,
                    )

                forecast_response = client.get(
                    f"{OPENWEATHER_BASE_URL}/forecast",
                    params={
                        "lat": latitude,
                        "lon": longitude,
                        "appid": self.api_key,
                        "units": "metric",
                    },
                )
                self._check_response(forecast_response)
                forecast = forecast_response.json()
        except httpx.TimeoutException as exc:
            raise WeatherAPIError(
                "The weather service timed out. Please try again shortly.",
            ) from exc
        except httpx.RequestError as exc:
            raise WeatherAPIError(
                "The weather service could not be reached. Please try again shortly.",
            ) from exc

        all_forecast_entries = forecast.get("list", [])
        forecast_entries_24h = all_forecast_entries[:8]
        rainfall_24h_mm = sum(
            float(entry.get("rain", {}).get("3h", 0) or 0)
            for entry in forecast_entries_24h
        )
        rain_probability_pct = max(
            (
                float(entry.get("pop", 0) or 0) * 100
                for entry in forecast_entries_24h
            ),
            default=0.0,
        )
        daily_forecasts: dict[str, dict[str, Any]] = {}
        for entry in all_forecast_entries:
            date = str(entry.get("dt_txt", "")).split(" ", maxsplit=1)[0]
            main = entry.get("main", {})
            if not date or not isinstance(main, dict):
                continue

            day = daily_forecasts.setdefault(
                date,
                {
                    "date": date,
                    "min_temperature": None,
                    "max_temperature": None,
                    "rainfall_mm": 0.0,
                    "rain_probability_pct": 0.0,
                    "conditions": [],
                },
            )
            temperatures = [
                float(main[key])
                for key in ("temp_min", "temp_max")
                if main.get(key) is not None
            ]
            if not temperatures and main.get("temp") is not None:
                temperatures = [float(main["temp"])]
            if temperatures:
                daily_min = min(temperatures)
                daily_max = max(temperatures)
                day["min_temperature"] = (
                    daily_min
                    if day["min_temperature"] is None
                    else min(day["min_temperature"], daily_min)
                )
                day["max_temperature"] = (
                    daily_max
                    if day["max_temperature"] is None
                    else max(day["max_temperature"], daily_max)
                )

            day["rainfall_mm"] += float(entry.get("rain", {}).get("3h", 0) or 0)
            day["rain_probability_pct"] = max(
                day["rain_probability_pct"],
                float(entry.get("pop", 0) or 0) * 100,
            )
            weather_items = entry.get("weather", [])
            if weather_items:
                condition = weather_items[0].get("description")
                if condition and condition not in day["conditions"]:
                    day["conditions"].append(str(condition))

        upcoming_days = list(daily_forecasts.values())[:5]
        weather_items = current.get("weather", [])
        description = (
            weather_items[0].get("description", "conditions unavailable")
            if weather_items
            else "conditions unavailable"
        )

        return {
            "location": ", ".join(
                part for part in (current.get("name"), current.get("sys", {}).get("country")) if part
            ),
            "temperature": float(current["main"]["temp"]),
            "humidity": float(current["main"]["humidity"]),
            "description": str(description),
            "wind_speed": float(current.get("wind", {}).get("speed", 0) or 0),
            "current_rainfall_mm": float(current.get("rain", {}).get("1h", 0) or 0),
            "forecast_rainfall_mm_24h": rainfall_24h_mm,
            "rain_probability_pct": rain_probability_pct,
            "forecast_days": upcoming_days,
        }

    @staticmethod
    def _check_response(response: httpx.Response) -> None:
        if response.is_success:
            return
        if response.status_code == 404:
            raise WeatherAPIError(
                "We couldn't find weather for that location. Enter a city or town name and try again.",
                status_code=400,
            )
        if response.status_code in {401, 403}:
            raise WeatherAPIError(
                "The weather service rejected its API key. Check the OPENWEATHER_API_KEY configuration."
            )
        if response.status_code == 429:
            raise WeatherAPIError(
                "The weather service is rate-limiting requests. Please wait a moment and try again.",
                status_code=429,
            )
        raise WeatherAPIError(
            "The weather service is temporarily unavailable. Please try again later."
        )
