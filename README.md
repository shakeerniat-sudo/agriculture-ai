# AgriGuide AI

AgriGuide AI is an intelligent agriculture decision-support system created for farmers and agronomy advisors. It uses a Python Flask backend, multiple specialized AI analysis tools, and the Google Gemini API to produce structured agricultural recommendations based on crop, soil, weather, and crop-health inputs.

## Problem statement

Farmers often have to depend on fragmented advice and manual interpretation of soil and weather information. Daily field decisions are affected by crop type, moisture level, temperature, rainfall, season, and crop symptoms. A fast and accurate decision-support agent can help farmers understand crop suitability, irrigation needs, weather impact, and probable field stress before taking action.

## Solution

AgriGuide AI brings these inputs together in one analytical system. A farmer enters crop details and field conditions into a clean web form. The backend AI agent uses multiple specialized analysis tools for crop, irrigation, weather, and crop health. These tool results are combined and sent to Gemini, which generates a structured agricultural report in simple farming language.

## Features

- Crop suitability and condition analysis
- Irrigation recommendation based on moisture and rainfall
- Weather and season assessment
- Crop problem and symptom analysis
- Recommended actions for farmers
- Safety precautions for risky field decisions
- Multilingual translation support in English, Telugu, Hindi, Tamil, and Kannada
- Responsive single-page frontend
- Flask backend with REST API endpoints

## Architecture

Farmer -> Web UI -> JavaScript -> Flask Backend -> Agriculture AI Agent -> Crop Analysis Tool, Irrigation Analysis Tool, Weather Analysis Tool, Crop Health Analysis Tool -> Gemini LLM -> Structured Report -> Translation

## AI Agent workflow

1. The farmer submits field conditions and crop symptoms.
2. The backend validates the request.
3. The Agriculture Agent calls the four specialized analysis tools.
4. Tool outputs are merged into a detailed prompt.
5. Gemini generates a structured agricultural report.
6. The farmer can translate the original report into a regional language.

## Technology stack

- Frontend: HTML5, CSS3, JavaScript, Fetch API
- Backend: Python, Flask
- AI: Google Gemini via the google-genai Python SDK
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
GEMINI_API_KEY=your_gemini_api_key_here
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
3. In the Vercel project settings, add `GEMINI_API_KEY` as an environment variable. Do not upload or commit `backend/.env`.
4. Redeploy after adding the environment variable.

The deployment excludes local virtual environments and `.env` files. The AI endpoints will return a configuration error until `GEMINI_API_KEY` is set in Vercel.

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

These tool outputs are then combined and passed to the Gemini LLM for final reasoning. The result is a structured field advisory report in farmer-friendly language. Multilingual support is included using the same original English report as the source for translation into Telugu, Hindi, Tamil, and Kannada. This demonstrates both tool-based AI reasoning and multilingual AI behavior in a working application.

## Notes

- The app does not expose the Gemini API key to the frontend.
- All analysis requests are processed through the Flask backend.
- The translation feature always uses the original AI report as the source and never translates an already translated version.
