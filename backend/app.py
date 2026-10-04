"""Flask backend for AgriGuide AI."""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, request, send_from_directory
from google.genai.errors import APIError

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from agent import AgricultureAgent
else:
    from .agent import AgricultureAgent

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR.parent / "public"
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__, static_folder=str(FRONTEND_DIR), static_url_path="")
agent = AgricultureAgent(api_key=os.getenv("GEMINI_API_KEY"))


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
            "temperature",
            "rainfall",
            "rain_probability",
            "crop_problem",
        ]

        missing = [field for field in required if payload.get(field) in (None, "")]
        if missing:
            return jsonify({"success": False, "error": "Please complete all farm input fields before analysis."}), 400

        crop = payload.get("crop")
        if not isinstance(crop, str) or not crop.strip() or len(crop.strip()) > 60:
            return jsonify({"success": False, "error": "Enter a crop name of 60 characters or fewer."}), 400
        payload["crop"] = crop.strip()

        allowed_values = {
            "soil_type": {"Loamy", "Clay", "Sandy"},
            "season": {"Kharif", "Rabi", "Summer"},
        }
        if any(payload[field] not in choices for field, choices in allowed_values.items()):
            return jsonify({"success": False, "error": "Please select a soil type and season from the available options."}), 400

        numeric_fields = [
            "soil_moisture",
            "temperature",
            "rainfall",
            "rain_probability",
        ]
        invalid = []
        for name in numeric_fields:
            try:
                value = float(payload[name])
                if not math.isfinite(value):
                    invalid.append(name)
                if name == "soil_moisture" and not (0 <= value <= 100):
                    invalid.append(name)
                if name == "rain_probability" and not (0 <= value <= 100):
                    invalid.append(name)
                if name == "rainfall" and value < 0:
                    invalid.append(name)
            except (TypeError, ValueError):
                invalid.append(name)
        if invalid:
            return jsonify({"success": False, "error": "Please enter valid numeric values in the form."}), 400

        if not agent.client:
            return jsonify({"success": False, "error": "Gemini is not configured. Add GEMINI_API_KEY to backend/.env."}), 500

        result = agent.analyze(payload)
        return jsonify(result)
    except APIError as exc:
        app.logger.warning("Gemini analysis request failed (%s): %s", exc.code, exc.message)
        if exc.code == 429:
            return jsonify({
                "success": False,
                "error": "Gemini's daily request limit has been reached. Please try again after the quota resets, or increase the Gemini API quota.",
            }), 429
        return jsonify({
            "success": False,
            "error": "The Gemini service is temporarily unavailable. Please try again later.",
        }), 503
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
            return jsonify({"success": False, "error": "Gemini is not configured. Add GEMINI_API_KEY to backend/.env."}), 500

        translated = agent.translate_report(report, language)
        return jsonify({"success": True, "language": language, "translated_report": translated})
    except APIError as exc:
        app.logger.warning("Gemini translation request failed (%s): %s", exc.code, exc.message)
        if exc.code == 429:
            return jsonify({
                "success": False,
                "error": "Gemini's daily request limit has been reached. Please try again after the quota resets, or increase the Gemini API quota.",
            }), 429
        return jsonify({
            "success": False,
            "error": "The Gemini service is temporarily unavailable. Please try again later.",
        }), 503
    except ValueError as exc:
        return jsonify({"success": False, "error": str(exc)}), 400
    except Exception:  # pragma: no cover - broad fallback for safety
        app.logger.exception("Report translation failed")
        return jsonify({"success": False, "error": "Translation failed. Please try again later."}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(debug=True, host="0.0.0.0", port=port)
