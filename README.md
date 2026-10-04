# AgriGuide AI

AgriGuide AI is an intelligent agriculture decision-support system created for farmers and agronomy advisors. It uses a Python Flask backend, the OpenWeather API for location-based current weather and forecasts, specialized crop analysis tools, and the Groq API to produce structured recommendations.

## Problem statement

Farmers often have to depend on fragmented advice and manual interpretation of soil and weather information. Daily field decisions are affected by crop type, moisture level, temperature, rainfall, season, and crop symptoms. A fast and accurate decision-support agent can help farmers understand crop suitability, irrigation needs, weather impact, and probable field stress before taking action.

## Solution

AgriGuide AI brings these inputs together in one analytical system. A farmer enters crop, soil, season, location, and crop symptoms. The backend fetches current weather and the next 24-hour precipitation forecast from OpenWeather, then combines these with the farmer's crop and soil information and specialized analysis tools. Groq generates a structured agricultural report in simple farming language.

## Features

- Crop suitability and condition analysis
- Irrigation recommendations based on soil moisture and forecast weather
- Location-based current weather and 24-hour precipitation forecast
- Crop problem and symptom analysis
- Recommended actions for farmers
- Safety precautions for risky field decisions
- Multilingual translation support in English, Telugu, Hindi, Tamil, and Kannada
- Responsive single-page frontend
- Flask backend with REST API endpoints

## Architecture

Farmer -> Web UI -> Flask Backend -> OpenWeather current conditions and forecast -> Agriculture AI Agent and analysis tools -> Groq LLM -> Structured Report -> Translation

## AI Agent workflow

1. The farmer submits crop, soil, season, location, and crop symptoms.
2. The backend validates the request and fetches current weather and the next 24-hour forecast for the location.
3. The Agriculture Agent combines live weather data with crop, irrigation, and crop-health analysis.
4. Tool outputs are merged into a detailed prompt.
5. Groq generates a structured agricultural report.
6. The farmer can translate the original report into a regional language.

## Agriculture report sections

Each AI report contains five detailed sections in a consistent order:

1. Agriculture Analysis — crop, soil, and season context, including a clearly labeled Weather Report Analysis subsection for local current conditions, observed recent rainfall, and the separate 24-hour forecast.
2. Irrigation Recommendation — moisture- and forecast-aware guidance with cues for reassessment.
3. Crop Problem Analysis — cautious possible causes, field observations, and when to seek local expertise.
4. Recommended Actions — prioritized immediate and near-term steps with reasons and monitoring cues.
5. Important Precautions — relevant weather, field, and safe-input-use cautions.

Recommendations must use the supplied farm data and must not invent a diagnosis, crop stage, or unsupported input dosage.

## Technology stack

- Frontend: HTML5, CSS3, JavaScript, Fetch API
- Backend: Python, Flask
- AI: Groq API using its OpenAI-compatible chat completions endpoint
- Environment: VS Code, Python virtual environment, .env file

## Folder structure

```text
AgriGuide-AI/
├── public/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── app.py
├── backend/
│   ├── app.py
│   ├── agent.py
│   ├── tools.py
│   ├── requirements.txt
│   ├── .env.example
│   └── .env
├── README.md
└── .gitignore
```

## Installation

Open a terminal in the project folder and run:

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

Then install dependencies:

```bash
pip install -r backend/requirements.txt
```

## Environment variables

Create a file named `backend/.env` using the example template:

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
OPENWEATHER_API_KEY=your_openweather_api_key_here
```

## How to run

Start the application:

```bash
python backend/app.py
```

Then open the app in a browser at:

```text
http://127.0.0.1:5000
```

The frontend is served through the Flask server as requested.

## Deploy to Vercel

Vercel uses the root `app.py` as the Flask entrypoint and serves the files in `public/` from its CDN. The root `requirements.txt` installs the backend dependencies for Vercel's Python runtime.

1. Sign in to Vercel from a terminal with `vercel login`.
2. From the project root, run `vercel --prod`.
3. In the Vercel project settings, add `GROQ_API_KEY` and `OPENWEATHER_API_KEY` as environment variables. Optionally set `GROQ_MODEL` to select another supported Groq model. Do not upload or commit `backend/.env`.
4. Redeploy after adding the environment variable.

The deployment excludes local virtual environments and `.env` files. Analysis requires both `GROQ_API_KEY` and `OPENWEATHER_API_KEY` to be set in Vercel.

## API endpoints

### GET /api/health
Returns a service health status.

### POST /api/analyze
Accepts farm condition data and returns a structured AI agriculture report.

### POST /api/translate
Accepts the original report and desired language and returns the translated report.

## Future improvements

- Add historical field and crop data tracking
- Include satellite or weather-feed integration
- Add user authentication and saved reports
- Extend crop recommendations by state or district
- Add downloadable PDF reports for farmers

## How this project satisfies FAI requirements

This project is designed as a clear and practical FAI implementation. It addresses a real agricultural problem by assisting farmers with crop health, irrigation, and seasonal planning. The system uses an AI agent built with multiple specialized tools instead of a single generic chatbot prompt. The agent performs targeted analysis through:

- Crop Analysis Tool
- Irrigation Analysis Tool
- Weather Analysis Tool
- Crop Problem/Health Analysis Tool

These tool outputs are then combined and passed to the Groq LLM for final reasoning. The result is a structured field advisory report in farmer-friendly language. Multilingual support is included using the same original English report as the source for translation into Telugu, Hindi, Tamil, and Kannada. This demonstrates both tool-based AI reasoning and multilingual AI behavior in a working application.

## Notes

- The app does not expose the Groq API key to the frontend.
- All analysis requests are processed through the Flask backend.
- The translation feature always uses the original AI report as the source and never translates an already translated version.
