# LLM-Chat-Bot

A lightweight chatbot powered by Google Gemini (via `google-genai`) that can be used through:

- a CLI (`cli-only` folder)
- a Flask web UI (`chatbot-webv2` folder)
- a Streamlit UI (`streamlit_app_v2.py`)

## Features
- Google Gemini integration (default model: `gemini-2.0-flash`, configurable via `GEMINI_MODEL`)
- Multiple interfaces: CLI, Flask, and Streamlit
- Configurable generation parameters (temperature, top_p, top_k, max tokens)
- Chat history persistence (JSON files)

## Directory Structure
```
LLM-Chat-Bot/
  cli-only/
    app.py
    generate_secrets.py
  chatbot-webv2/
    app.py
    generate_secrets.py
    static/
      style.css
      script.js
    templates/
      index.html
  streamlit_app_v2.py
  generate_secrets.py
  requirements.txt
  README.md
```

## Prerequisites
- Python 3.9+ (use a virtual environment if possible)
- Google Gemini API key (from Google AI Studio)
- Required Python packages (see `requirements.txt`)

## Installation
```bash
git clone https://github.com/weiss-rn/LLM-Chat-Bot.git
cd LLM-Chat-Bot
python -m venv venv
```

Windows:
```bat
venv\Scripts\activate
```

macOS / Linux:
```bash
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Generating Secrets
The project expects a `secrets.toml` (for Streamlit) or `config.toml` (for CLI/Flask) containing:
```toml
GOOGLE_API_KEY = "YOUR_API_KEY"
```

Windows:
```bat
python generate_secrets.py
python cli-only\generate_secrets.py
python chatbot-webv2\generate_secrets.py
```

Linux / macOS:
```bash
python3 generate_secrets.py
python3 cli-only/generate_secrets.py
python3 chatbot-webv2/generate_secrets.py
```

## Running the Applications

CLI only:
```bash
cd cli-only
python app.py
```

Flask web UI:
```bash
cd chatbot-webv2
python app.py
```
The Flask server starts at `http://0.0.0.0:5000`.

Streamlit UI:
```bash
streamlit run streamlit_app_v2.py
```
The Streamlit app will be available at `http://localhost:8501`.

## License
Apache 2.0. See `LICENSE`.
