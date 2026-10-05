"""Flask backend for AgriGuide AI."""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from agent import AgricultureAgent
    from tools import future_weather_analysis
    from weather import WeatherAPIError, WeatherService
else:
    from .agent import AgricultureAgent
    from .tools import future_weather_analysis
    from .weather import WeatherAPIError, WeatherService

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "public"
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
agent = AgricultureAgent(api_key=os.getenv("GROQ_API_KEY"))
weather_service = WeatherService(api_key=os.getenv("OPENWEATHER_API_KEY"))


@app.route("/")
def index():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


@app.route("/<path:path>")
def serve_static(path: str):
    if path.startswith("api/"):
        return jsonify({"success": False, "error": "API route not found"}), 404
    if path == "":
        return send_from_directory(str(FRONTEND_DIR), "index.html")
    return send_from_directory(str(FRONTEND_DIR), path)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"success": True, "status": "ok", "service": "AgriGuide AI"})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        payload = request.get_json(silent=True) or {}
        required = [
            "crop",
            "soil_type",
            "season",
            "soil_moisture",
            "location",
            "crop_problem",
        ]

        missing = [field for field in required if payload.get(field) in (None, "")]
        if missing:
            return jsonify({"success": False, "error": "Please complete all farm input fields before analysis."}), 400

        crop = payload.get("crop")
        if not isinstance(crop, str) or not crop.strip() or len(crop.strip()) > 60:
            return jsonify({"success": False, "error": "Enter a crop name of 60 characters or fewer."}), 400
        payload["crop"] = crop.strip()
        location = payload.get("location")
        if not isinstance(location, str) or not location.strip() or len(location.strip()) > 120:
            return jsonify({"success": False, "error": "Enter a city or town name of 120 characters or fewer."}), 400
        payload["location"] = location.strip()

        allowed_values = {
            "soil_type": {"Loamy", "Clay", "Sandy"},
            "season": {"Kharif", "Rabi", "Summer"},
        }
        if any(payload[field] not in choices for field, choices in allowed_values.items()):
            return jsonify({"success": False, "error": "Please select a soil type and season from the available options."}), 400

        numeric_fields = [
            "soil_moisture",
        ]
        invalid = []
        for name in numeric_fields:
            try:
                value = float(payload[name])
                if not math.isfinite(value):
                    invalid.append(name)
                if name == "soil_moisture" and not (0 <= value <= 100):
                    invalid.append(name)
            except (TypeError, ValueError):
                invalid.append(name)
        if invalid:
            return jsonify({"success": False, "error": "Please enter valid numeric values in the form."}), 400

        try:
            weather = weather_service.get_conditions(payload["location"])
        except WeatherAPIError as exc:
            app.logger.warning(
                "Weather lookup failed (%s); continuing without live weather.",
                exc.status_code,
            )
            payload.update(
                {
                    "temperature": None,
                    "rainfall": None,
                    "rain_probability": None,
                    "weather": {},
                }
            )
        else:
            payload.update(
                {
                    "temperature": weather["temperature"],
                    "rainfall": weather["forecast_rainfall_mm_24h"],
                    "rain_probability": weather["rain_probability_pct"],
                    "weather": weather,
                }
            )

        if not agent.client:
            app.logger.warning("Groq is not configured; returning built-in farm guidance.")
            result = agent.build_local_fallback(payload)
        else:
            try:
                result = agent.analyze(payload)
                if not isinstance(result.get("report"), str) or not result["report"].strip():
                    raise ValueError("Groq returned a report without content.")
            except (httpx.HTTPError, ValueError) as exc:
                app.logger.warning(
                    "Groq analysis failed (%s); returning built-in farm guidance.",
                    type(exc).__name__,
                )
                result = agent.build_local_fallback(payload)
        weather_data = payload.get("weather")
        forecast_days = weather_data.get("forecast_days", []) if isinstance(weather_data, dict) else []
        future_weather_section = future_weather_analysis(
            crop=payload["crop"],
            soil_type=payload["soil_type"],
            season=payload["season"],
            soil_moisture=float(payload["soil_moisture"]),
            location=payload["location"],
            forecast_days=forecast_days,
        )
        report = result["report"]
        irrigation_heading = "\n### Irrigation Recommendation"
        insertion_point = report.find(irrigation_heading)
        if insertion_point < 0:
            report = f"{report.rstrip()}\n\n{future_weather_section}"
        else:
            report = (
                f"{report[:insertion_point].rstrip()}\n\n"
                f"{future_weather_section}\n"
                f"{report[insertion_point:]}"
            )
        result["report"] = report
        analysis = result.setdefault("analysis", {})
        if isinstance(analysis, dict):
            analysis["future_weather"] = future_weather_section
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception:  # pragma: no cover - broad fallback for server-side safety
        app.logger.exception("Farm analysis failed")
        return jsonify({"success": False, "error": "The AI analysis could not be completed. Please try again later."}), 500


@app.route("/api/translate", methods=["POST"])
def translate():
    try:
        payload = request.get_json(silent=True) or {}
        report = payload.get("report", "")
        language = payload.get("language", "English")

        if not report.strip():
            return jsonify({"success": False, "error": "There is no report available to translate."}), 400

        if not agent.client:
            return jsonify({"success": False, "error": "Groq is not configured. Add GROQ_API_KEY to the backend environment."}), 500

        translated = agent.translate_report(report, language)
        return jsonify({"success": True, "language": language, "translated_report": translated})
    except httpx.HTTPStatusError as exc:
        status_code = exc.response.status_code
        app.logger.warning("Groq translation request failed (%s): %s", status_code, exc.response.text[:500])
        if status_code == 429:
            return jsonify({
                "success": False,
                "error": "Groq is temporarily rate-limiting requests. Please wait a moment and try again.",
            }), 429
        return jsonify({
            "success": False,
            "error": "The Groq AI service is temporarily unavailable. Please try again later.",
        }), 503
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception:  # pragma: no cover - broad fallback for safety
        app.logger.exception("Report translation failed")
        return jsonify({"success": False, "error": "Translation failed. Please try again later."}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, host="0.0.0.0", port=port)
