"""Specialized agriculture analysis tools for AgriGuide AI."""

from __future__ import annotations


def crop_analysis(crop: str, soil_type: str, season: str, temperature: float, moisture: float) -> str:
    """Assess crop suitability and present a concise agriculture summary."""
    crop_name = (crop or "crop").strip().title()
    soil_name = (soil_type or "soil").strip().title()
    season_name = (season or "season").strip().title()

    suitability = "generally suitable"
    if moisture < 20:
        suitability = "likely stressed due to dry soil"
    elif moisture > 70:
        suitability = "at risk of waterlogging and poor root oxygen"

    if temperature > 38:
        suitability += ", especially in high heat"
    elif temperature < 12:
        suitability += ", especially in cool conditions"

    if soil_name == "Sandy":
        note = "Sandy soil drains quickly and may need more frequent irrigation."
    elif soil_name == "Clay":
        note = "Clay soil holds water longer, so avoid overwatering and watch drainage."
    else:
        note = "Loamy soil is usually favorable for balanced moisture retention and aeration."

    return (
        f"Crop suitability: {crop_name} is {suitability} for {season_name} conditions. "
        f"The current soil type is {soil_name}. {note} "
        f"Temperature is {temperature}°C and soil moisture is {moisture}%."
    )


def irrigation_analysis(soil_moisture: float, rainfall: float, rain_probability: float) -> str:
    """Recommend irrigation based on moisture, rainfall, and forecast probability."""
    moisture = float(soil_moisture)
    rainfall = float(rainfall)
    rain_prob = float(rain_probability)

    if moisture < 25:
        recommendation = "Irrigation is strongly recommended soon."
    elif moisture < 40:
        recommendation = "Supplemental irrigation may be needed, especially during hot hours."
    elif moisture > 60 and rain_prob < 50:
        recommendation = "Irrigation is not urgent, but soil should be monitored closely."
    else:
        recommendation = "Current moisture is acceptable, and irrigation can be delayed if rainfall continues."

    if rain_prob >= 70 and rainfall > 25:
        recommendation += " Forecast conditions suggest good natural rainfall, which may reduce irrigation demand."
    elif rain_prob >= 60 and rainfall <= 15:
        recommendation += " Some rainfall is possible, but the soil should still be checked before irrigation is skipped."

    return recommendation


def weather_analysis(
    temperature: float,
    rainfall: float,
    rain_probability: float,
    season: str,
    description: str = "",
    humidity: float | None = None,
) -> str:
    """Summarize weather conditions and their relevance to crop health."""
    season_name = (season or "season").strip().title()
    temp = float(temperature)
    rain = float(rainfall)

    details = []
    if temp > 35:
        details.append("High temperatures may increase heat stress and crop water demand.")
    elif temp < 15:
        details.append("Cool conditions may slow crop growth and reduce evapotranspiration.")
    else:
        details.append("Temperature is within a manageable range for many crops in this season.")

    if rain > 40:
        details.append("Rainfall is relatively high and may improve soil moisture, but excess water could affect root health.")
    elif rain < 10:
        details.append("Rainfall is low, so irrigation planning is important to avoid stress.")
    else:
        details.append("Rainfall is moderate and should support field conditions if distributed evenly.")

    if description:
        details.append(f"Current local conditions are {description}.")
    if humidity is not None:
        details.append(f"Current relative humidity is {humidity}%.")
    details.append(
        f"The next 24-hour forecast indicates up to {float(rainfall):.1f} mm of rain "
        f"with a maximum precipitation probability of {float(rain_probability):.0f}%."
    )
    details.append(f"Seasonal context: {season_name} is being considered in the decision process.")
    return " ".join(details)


def crop_health_analysis(crop: str, crop_problem: str) -> str:
    """Review visible symptoms and provide a cautious plant-health assessment."""
    crop_name = (crop or "crop").strip().title()
    problem = (crop_problem or "").strip()
    if not problem:
        return f"No crop problem details were provided. A field inspection is recommended to confirm current crop health for {crop_name}."

    problem_lower = problem.lower()
    causes = []

    if any(keyword in problem_lower for keyword in ["yellow", "chlorosis", "pale green"]):
        causes.append("yellowing symptoms may indicate nutrient stress, water stress, or a mild nutrient deficiency.")
    if any(keyword in problem_lower for keyword in ["wilting", "drooping", "dry", "curling"]):
        causes.append("wilting can be caused by soil moisture stress, root stress, or high temperature.")
    if any(keyword in problem_lower for keyword in ["leaf spot", "brown spot", "dark spot", "fungal", "lesion"]):
        causes.append("leaf spots may be linked to fungal pressure or repeated leaf wetness in humid conditions.")
    if any(keyword in problem_lower for keyword in ["necrosis", "burnt", "scorch", "damaged"]):
        causes.append("damage can result from severe stress, chemical burn, or disease pressure.")
    if any(keyword in problem_lower for keyword in ["blight", "mold", "powdery", "rust"]):
        causes.append("blight or fungal growth symptoms suggest the need for field inspection and protective crop management.")

    if not causes:
        causes.append("The symptoms show possible stress conditions, but no definite diagnosis can be made without field inspection and crop history.")

    return (
        f"For {crop_name}, the reported issue is: '{problem}'. "
        f"Possible explanations include: {' '.join(causes)} "
        "These symptoms should be checked against field conditions before deciding on fertilizer or pesticide action."
    )


def build_analysis_summary(payload: dict) -> dict:
    """Return a structured dict from the specialized tools."""
    crop = payload.get("crop", "")
    soil_type = payload.get("soil_type", "")
    season = payload.get("season", "")
    temperature = float(payload.get("temperature", 0))
    moisture = float(payload.get("soil_moisture", 0))
    rainfall = float(payload.get("rainfall", 0))
    rain_probability = float(payload.get("rain_probability", 0))
    crop_problem = payload.get("crop_problem", "")

    return {
        "crop": crop_analysis(crop, soil_type, season, temperature, moisture),
        "irrigation": irrigation_analysis(moisture, rainfall, rain_probability),
        "weather": weather_analysis(
            temperature,
            rainfall,
            rain_probability,
            season,
            payload.get("weather", {}).get("description", ""),
            payload.get("weather", {}).get("humidity"),
        ),
        "health": crop_health_analysis(crop, crop_problem),
    }
