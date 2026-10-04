"""Agriculture AI agent that combines specialized tools and Groq reasoning."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import httpx

GROQ_API_BASE_URL = "https://api.groq.com/openai/v1/"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tools import build_analysis_summary
else:
    from .tools import build_analysis_summary


class AgricultureAgent:
    def __init__(self, api_key: str | None = None) -> None:
        configured_key = (api_key or os.getenv("GROQ_API_KEY") or "").strip()
        self.api_key = None if configured_key.lower().startswith(("your_", "replace_")) else configured_key or None
        self.model = os.getenv("GROQ_MODEL", DEFAULT_GROQ_MODEL)
        self.client = (
            httpx.Client(
                base_url=GROQ_API_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=90,
            )
            if self.api_key
            else None
        )

    def analyze(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not self.client:
            raise ValueError("GROQ_API_KEY is missing. Configure it in the backend environment before running analysis.")

        tool_summary = build_analysis_summary(payload)
        prompt = self._build_analysis_prompt(payload, tool_summary)

        text = self._generate_content(prompt, json_response=True)
        return self._parse_json_response(text)

    def translate_report(self, report: str, language: str) -> str:
        if not self.client:
            raise ValueError("GROQ_API_KEY is missing. Configure it in the backend environment before translating the report.")

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

        return self._generate_content(prompt).strip()

    def _generate_content(self, prompt: str, *, json_response: bool = False) -> str:
        if not self.client:
            raise ValueError("GROQ_API_KEY is missing. Configure it in the backend environment.")

        request_body: dict[str, Any] = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
        }
        if json_response:
            request_body["response_format"] = {"type": "json_object"}

        response = self.client.post("chat/completions", json=request_body)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise ValueError("Groq returned no completion choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Groq returned an empty completion.")
        return content

    def _build_analysis_prompt(self, payload: dict[str, Any], tool_summary: dict[str, str]) -> str:
        return f"""
You are an expert agriculture decision-support agent. Combine the following specialized tool outputs and produce a clear, farmer-friendly agricultural report.

Farmer inputs:
Crop: {payload.get('crop', '')}
Soil type: {payload.get('soil_type', '')}
Soil moisture: {payload.get('soil_moisture', '')}%
Season: {payload.get('season', '')}
Farm location: {payload.get('location', '')}
Crop problem/symptoms: {payload.get('crop_problem', '')}

Live weather data from OpenWeather:
Current temperature: {payload.get('temperature', '')}°C
Current conditions: {payload.get('weather', {}).get('description', 'unavailable')}
Humidity: {payload.get('weather', {}).get('humidity', 'unavailable')}%
Wind speed: {payload.get('weather', {}).get('wind_speed', 'unavailable')} m/s
Rain in the previous hour: {payload.get('weather', {}).get('current_rainfall_mm', 'unavailable')} mm
Forecast rainfall over the next 24 hours: {payload.get('rainfall', '')} mm
Maximum forecast rain probability over the next 24 hours: {payload.get('rain_probability', '')}%

Tool results:
- Crop Analysis: {tool_summary.get('crop', '')}
- Irrigation Analysis: {tool_summary.get('irrigation', '')}
- Weather Analysis: {tool_summary.get('weather', '')}
- Crop Problem Analysis: {tool_summary.get('health', '')}

Report requirements:
1. Return valid JSON with this structure:
{{
  "success": true,
  "report": "...",
  "analysis": {{
    "crop": "...",
    "irrigation": "...",
    "health": "...",
    "actions": "...",
    "precautions": "..."
  }}
}}
2. The report must contain exactly these five top-level Markdown headings, in this order, with no additional top-level headings:
### 🌱 Agriculture Analysis
### Irrigation Recommendation
### Crop Problem Analysis
### Recommended Actions
### Important Precautions
3. Make the report meaningfully detailed and specific to this farmer's crop, soil type, season, soil moisture, symptoms, location, and fetched weather. Do not repeat generic advice that does not relate to the supplied facts.
4. Under Agriculture Analysis, explain crop/season/soil suitability and relevant soil and moisture implications. Within this section, include a clearly labeled subsection titled "Weather Report Analysis" that summarizes the fetched local weather.
5. In Weather Report Analysis, explicitly state the location and describe current temperature, conditions, humidity, and wind where available. Separately report rainfall observed in the previous hour and forecast rainfall plus maximum rain probability over the next 24 hours. Explain how these observations and forecast may affect this crop and field, and clearly distinguish observed conditions from forecast. Do not imply current or historical rainfall values are forecast values.
6. Under Irrigation Recommendation, explain whether watering is urgent, can wait, or needs reassessment; connect the recommendation to measured soil moisture and forecast rain. Give a practical way to recheck soil moisture and explain what change should trigger a reassessment. Do not invent irrigation volumes, intervals, or crop growth-stage requirements not supported by the inputs.
7. Under Crop Problem Analysis, restate the reported symptoms, list plausible causes as possibilities rather than diagnoses, explain simple field observations that can help distinguish them, and say when to seek a local extension officer or agronomist.
8. Under Recommended Actions, provide 4-6 prioritized, practical steps. For each step, explain briefly why it helps and what the farmer should monitor. Include immediate and near-term checks where relevant.
9. Under Important Precautions, include context-relevant cautions for weather, waterlogging or moisture stress, crop inspection, and chemical use. Do not prescribe pesticide/fertilizer products, mixes, or exact dosages without a confirmed diagnosis and local label guidance.
10. Write in plain, farmer-friendly English. Prefer concise bullets grouped by short labels where useful; provide enough explanation that a farmer can act without guessing.
11. Never fabricate measurements, crop growth stage, disease confirmation, local regulations, or forecast certainty. If important information is missing, state what to inspect or ask a qualified local advisor.
12. Do not use Markdown bold markers such as **text**.
13. Keep the response readable on a farm advisory dashboard.
"""

    def _parse_json_response(self, raw_text: str) -> dict[str, Any]:
        text = (raw_text or "").strip()
        if not text:
            raise ValueError("Empty Groq response")

        try:
            data = json.loads(text)
            if isinstance(data, dict) and data.get("success") is True:
                return data
            raise ValueError("Groq response was not a valid success object")
        except json.JSONDecodeError:
            cleaned = text.replace("```json", "").replace("```", "").strip()
            data = json.loads(cleaned)
            if isinstance(data, dict) and data.get("success") is True:
                return data
            raise ValueError("Groq response could not be decoded as JSON")
