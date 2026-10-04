"""Agriculture AI agent that combines specialized tools and Gemini reasoning."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

from google import genai

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tools import build_analysis_summary
else:
    from .tools import build_analysis_summary


class AgricultureAgent:
    def __init__(self, api_key: str | None = None) -> None:
        configured_key = (api_key or os.getenv("GEMINI_API_KEY") or "").strip()
        self.api_key = None if configured_key.lower().startswith(("your_", "replace_")) else configured_key or None
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is missing. Configure the backend .env file before running analysis.")

        tool_summary = build_analysis_summary(payload)
        prompt = self._build_analysis_prompt(payload, tool_summary)

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"response_mime_type": "application/json"},
        )
        text = getattr(response, "text", "")
        return self._parse_json_response(text)

    def translate_report(self, report: str, language: str) -> str:
        if not self.client:
            raise ValueError("GEMINI_API_KEY is missing. Configure the backend .env file before translating the report.")

        target_language = language.strip()
        supported = {"English", "Telugu", "Hindi", "Tamil", "Kannada"}
        if target_language not in supported:
            raise ValueError(f"Unsupported language: {language}")

        prompt = (
            "You are a professional agricultural translation assistant. Translate the following report into "
            f"{target_language}. Preserve the original meaning, recommendations, headings, bullet points, numbered lists, and emojis. "
            "Never add new agricultural advice or recommendations. Translate only the provided report.\n\n"
            f"Original report:\n{report}"
        )

        response = self.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        return getattr(response, "text", report).strip()

    def _build_analysis_prompt(self, payload: dict[str, Any], tool_summary: dict[str, str]) -> str:
        return f"""
You are an expert agriculture decision-support agent. Combine the following specialized tool outputs and produce a clear, farmer-friendly agricultural report.

Farmer inputs:
Crop: {payload.get('crop', '')}
Soil type: {payload.get('soil_type', '')}
Soil moisture: {payload.get('soil_moisture', '')}%
Temperature: {payload.get('temperature', '')}°C
Rainfall: {payload.get('rainfall', '')} mm
Rain probability: {payload.get('rain_probability', '')}%
Season: {payload.get('season', '')}
Crop problem/symptoms: {payload.get('crop_problem', '')}

Tool results:
- Crop Analysis: {tool_summary.get('crop', '')}
- Irrigation Analysis: {tool_summary.get('irrigation', '')}
- Weather Analysis: {tool_summary.get('weather', '')}
- Crop Problem Analysis: {tool_summary.get('health', '')}

Requirements:
1. Return valid JSON with this structure:
{{
  "success": true,
  "report": "...",
  "analysis": {{
    "crop": "...",
    "irrigation": "...",
    "weather": "...",
    "health": "...",
    "actions": "...",
    "precautions": "..."
  }}
}}
2. Each section must use the headings exactly:
# 🌱 Agriculture Analysis
# 💧 Irrigation Recommendation
# 🌦️ Weather Analysis
# 🐛 Crop Problem Analysis
# 🌾 Recommended Actions
# ⚠️ Important Precautions
3. Keep the language simple and farmer-friendly.
4. Do not claim a definitive disease diagnosis without enough evidence.
5. Use bullet points and numbered lists where useful.
6. Do not use Markdown stars such as **text**.
7. Do not add unsupported claims. Use practical action steps.
8. The report must be readable on a farm advisory dashboard.
"""

    def _parse_json_response(self, raw_text: str) -> dict[str, Any]:
        text = (raw_text or "").strip()
        if not text:
            raise ValueError("Empty Gemini response")

        try:
            data = json.loads(text)
            if isinstance(data, dict) and data.get("success") is True:
                return data
            raise ValueError("Gemini response was not a valid success object")
        except json.JSONDecodeError:
            cleaned = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            if isinstance(data, dict) and data.get("success") is True:
                return data
            raise ValueError("Gemini response could not be decoded as JSON")
