"""Specialized agriculture analysis tools for AgriGuide AI."""

from __future__ import annotations


def crop_analysis(
    crop: str,
    soil_type: str,
    season: str,
    temperature: float | None,
    moisture: float,
) -> str:
    """Assess crop suitability and present a concise agriculture summary."""
    crop_name = (crop or "crop").strip().title()
    soil_name = (soil_type or "soil").strip().title()
    season_name = (season or "season").strip().title()

    suitability = "generally suitable"
    if moisture < 20:
        suitability = "likely stressed due to dry soil"
    elif moisture > 70:
        suitability = "at risk of waterlogging and poor root oxygen"

    if temperature is not None and temperature > 38:
        suitability += ", especially in high heat"
    elif temperature is not None and temperature < 12:
        suitability += ", especially in cool conditions"

    if soil_name == "Sandy":
        note = "Sandy soil drains quickly and may need more frequent irrigation."
    elif soil_name == "Clay":
        note = "Clay soil holds water longer, so avoid overwatering and watch drainage."
    else:
        note = "Loamy soil is usually favorable for balanced moisture retention and aeration."

    temperature_note = (
        f"Temperature is {temperature}°C. "
        if temperature is not None
        else "Current temperature is unavailable. "
    )
    return (
        f"Crop suitability: {crop_name} is {suitability} for {season_name} conditions. "
        f"The current soil type is {soil_name}. {note} "
        f"{temperature_note}Soil moisture is {moisture}%."
    )


def irrigation_analysis(
    soil_moisture: float,
    rainfall: float | None,
    rain_probability: float | None,
) -> str:
    """Recommend irrigation based on moisture, rainfall, and forecast probability."""
    moisture = float(soil_moisture)
    rain = float(rainfall) if rainfall is not None else None
    rain_prob = float(rain_probability) if rain_probability is not None else None

    if moisture < 25:
        recommendation = "Irrigation is strongly recommended soon."
    elif moisture < 40:
        recommendation = "Supplemental irrigation may be needed, especially during hot hours."
    elif moisture > 60 and (rain_prob is None or rain_prob < 50):
        recommendation = "Irrigation is not urgent, but soil should be monitored closely."
    elif rain is None or rain_prob is None:
        recommendation = (
            "Current moisture is not critically low based on this reading, but the forecast "
            "is unavailable. Recheck the field and consult a local forecast before deciding."
        )
    else:
        recommendation = "Current moisture is acceptable, and irrigation can be delayed if rainfall continues."

    if rain_prob is not None and rain is not None and rain_prob >= 70 and rain > 25:
        recommendation += " Forecast conditions suggest good natural rainfall, which may reduce irrigation demand."
    elif rain_prob is not None and rain is not None and rain_prob >= 60 and rain <= 15:
        recommendation += " Some rainfall is possible, but the soil should still be checked before irrigation is skipped."
    elif rain is None or rain_prob is None:
        recommendation += " Forecast rainfall information is unavailable; check a local forecast before deciding."

    return recommendation


def weather_analysis(
    temperature: float | None,
    rainfall: float | None,
    rain_probability: float | None,
    season: str,
    description: str = "",
    humidity: float | None = None,
) -> str:
    """Summarize weather conditions and their relevance to crop health."""
    season_name = (season or "season").strip().title()
    temp = float(temperature) if temperature is not None else None
    rain = float(rainfall) if rainfall is not None else None

    details = []
    if temp is None:
        details.append("Current temperature information is unavailable.")
    elif temp > 35:
        details.append("High temperatures may increase heat stress and crop water demand.")
    elif temp < 15:
        details.append("Cool conditions may slow crop growth and reduce evapotranspiration.")
    else:
        details.append("Temperature is within a manageable range for many crops in this season.")

    if rain is None:
        details.append("Forecast rainfall information is unavailable.")
    elif rain > 40:
        details.append("Rainfall is relatively high and may improve soil moisture, but excess water could affect root health.")
    elif rain < 10:
        details.append("Rainfall is low, so irrigation planning is important to avoid stress.")
    else:
        details.append("Rainfall is moderate and should support field conditions if distributed evenly.")

    if description:
        details.append(f"Current local conditions are {description}.")
    if humidity is not None:
        details.append(f"Current relative humidity is {humidity}%.")
    if rain is not None and rain_probability is not None:
        details.append(
            f"The next 24-hour forecast indicates up to {rain:.1f} mm of rain "
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
    temperature_value = payload.get("temperature")
    temperature = float(temperature_value) if temperature_value is not None else None
    moisture = float(payload.get("soil_moisture", 0))
    rainfall_value = payload.get("rainfall")
    rainfall = float(rainfall_value) if rainfall_value is not None else None
    probability_value = payload.get("rain_probability")
    rain_probability = float(probability_value) if probability_value is not None else None
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


def future_weather_analysis(
    crop: str,
    soil_type: str,
    season: str,
    soil_moisture: float,
    location: str,
    forecast_days: list[dict],
) -> str:
    """Explain the existing API forecast in the context of this farmer's field."""
    if not forecast_days:
        return """### 🌦️ Future Weather Analysis
- 📅 Upcoming Weather: Forecast data is currently unavailable; no future conditions are assumed.
- 🌡️ Temperature Trend: Not available.
- 🌧️ Rainfall Forecast: Not available.
- 💧 Rain Probability: Not available.
- 🌾 Expected Impact on Current Crop: Check a local forecast before making weather-dependent crop decisions.
- 💧 Future Irrigation Requirement: Recheck soil moisture and use an up-to-date local forecast; no irrigation schedule is inferred here.
- ⚠️ Possible Weather Risks: Future weather risks cannot be assessed without forecast data.
- 🌱 Recommended Preparation: Monitor field moisture and drainage, and review the local forecast when available."""

    location_name = location.strip() or "the farm"
    crop_name = crop.strip() or "the current crop"
    soil_name = soil_type.strip() or "the reported soil"
    moisture = float(soil_moisture)

    daily_lines = []
    for day in forecast_days:
        date = str(day.get("date", "Date unavailable"))
        conditions = ", ".join(day.get("conditions", [])) or "conditions unavailable"
        low = day.get("min_temperature")
        high = day.get("max_temperature")
        if low is not None and high is not None:
            temperatures = f"{float(low):.1f}–{float(high):.1f}°C"
        else:
            temperatures = "temperature unavailable"
        rain = day.get("rainfall_mm")
        rain_text = f"{float(rain):.1f} mm forecast" if rain is not None else "rainfall unavailable"
        probability = day.get("rain_probability_pct")
        probability_text = (
            f"up to {float(probability):.0f}% rain probability"
            if probability is not None
            else "rain probability unavailable"
        )
        daily_lines.append(
            f"- {date}: {conditions}; {temperatures}; {rain_text}; {probability_text}."
        )

    temperatures = [
        (
            float(day["min_temperature"]) + float(day["max_temperature"])
        ) / 2
        for day in forecast_days
        if day.get("min_temperature") is not None and day.get("max_temperature") is not None
    ]
    if len(temperatures) > 1:
        temperature_change = temperatures[-1] - temperatures[0]
        if temperature_change >= 2:
            temperature_trend = (
                f"Forecast daily midpoint temperatures trend warmer by about "
                f"{temperature_change:.1f}°C across the available period."
            )
        elif temperature_change <= -2:
            temperature_trend = (
                f"Forecast daily midpoint temperatures trend cooler by about "
                f"{abs(temperature_change):.1f}°C across the available period."
            )
        else:
            temperature_trend = "Forecast daily midpoint temperatures are broadly steady across the available period."
    elif temperatures:
        temperature_trend = "Only one forecast day has usable temperature ranges, so a multi-day trend is unavailable."
    else:
        temperature_trend = "Temperature ranges are unavailable in the returned forecast."

    total_rainfall = sum(float(day.get("rainfall_mm", 0) or 0) for day in forecast_days)
    maximum_probability = max(
        (
            float(day.get("rain_probability_pct", 0) or 0)
            for day in forecast_days
            if day.get("rain_probability_pct") is not None
        ),
        default=None,
    )
    high_rainfall_days = [
        day
        for day in forecast_days
        if float(day.get("rainfall_mm", 0) or 0) >= 25
    ]
    likely_rain_days = [
        day
        for day in forecast_days
        if float(day.get("rain_probability_pct", 0) or 0) >= 70
    ]
    dry_days = [
        day
        for day in forecast_days
        if float(day.get("rainfall_mm", 0) or 0) < 2
        and float(day.get("max_temperature") or 0) >= 32
    ]

    rainfall_context = f"{total_rainfall:.1f} mm across the listed forecast days."
    probability_context = (
        f"Maximum daily probability in this forecast: {maximum_probability:.0f}%."
        if maximum_probability is not None
        else "Rain probability is unavailable in the returned forecast."
    )

    if high_rainfall_days or likely_rain_days:
        impact = (
            f"Rain is possible during the listed forecast period. For {crop_name}, the actual "
            "effect depends on crop stage and field drainage, which were not provided. "
        )
        if high_rainfall_days:
            risk = "Higher forecast rainfall may increase excess-moisture or waterlogging risk."
            preparation = "Monitor drainage and root-zone moisture after forecast rain; avoid adding irrigation while the soil remains wet."
        else:
            risk = "Rain probability is high on some forecast days, but rainfall amounts remain uncertain."
            preparation = "Monitor the forecast and check drainage and root-zone moisture if rain occurs."
        irrigation = "Recheck soil moisture after forecast rain and delay irrigation if the root zone is already adequately moist."
        if soil_name.casefold() == "clay" and high_rainfall_days:
            impact += "Clay soil can drain slowly, so check for standing water."
    elif dry_days:
        impact = (
            f"Hot, low-rain forecast periods may raise water demand for {crop_name}. "
            f"The entered soil moisture is {moisture:g}%; check the root zone rather than relying on the forecast alone."
        )
        risk = "Heat and limited forecast rain may contribute to crop water stress, especially if soil moisture declines."
        preparation = "Check soil moisture and plants during hot, dry periods and keep water available if field checks show increasing stress."
        irrigation = "Monitor the root-zone moisture; consider irrigation only if field checks and crop needs indicate it, and reassess if rain arrives."
    else:
        impact = (
            f"The forecast has changing or moderate conditions for {crop_name}. "
            f"Interpret the outlook with the entered soil moisture ({moisture:g}%) and field observations."
        )
        risk = "Conditions may change across forecast days; continue checking for either drying soil or excessive wetness."
        preparation = "Review the forecast daily and check field moisture and drainage after significant weather changes."
        irrigation = "Decide from root-zone moisture and the latest forecast; reassess after rainfall or warmer, drier conditions."

    return "\n".join(
        [
            "### 🌦️ Future Weather Analysis",
            "- 📅 Upcoming Weather:",
            *daily_lines,
            f"- 🌡️ Temperature Trend: {temperature_trend}",
            f"- 🌧️ Rainfall Forecast: {rainfall_context}",
            f"- 💧 Rain Probability: {probability_context}",
            f"- 🌾 Expected Impact on Current Crop: {impact}",
            f"- 💧 Future Irrigation Requirement: {irrigation}",
            f"- ⚠️ Possible Weather Risks: {risk}",
            f"- 🌱 Recommended Preparation: For {location_name} in the {season or 'current'} season, {preparation}",
        ]
    )
