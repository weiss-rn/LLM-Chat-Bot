# LLM‑Chat‑Bot

A lightweight chatbot powered by **Google Gemini** (via `google-generativeai`) that can be used through:

* a **CLI** (`cli-only` folder)  
* a **Flask web UI** (`chatbot-web/app.py`)  
* a **Streamlit UI** (`streamlit_app_v2.py`)

---

## Table of Contents
- [Features](#features)  
- [Directory Structure](#directory-structure)  
- [Prerequisites](#prerequisites)  
- [Installation](#installation)  
- [Generating Secrets](#generating-secrets)  
- [Running the Applications](#running-the-applications)  
  - [CLI Only](#cli-only)  
  - [Flask Web UI](#flask-web-ui)  
  - [Streamlit UI](#streamlit-ui)  
- [License](#license)  

---

## Features
- **Google Gemini integration** – uses the latest `gemini-2.5-flash` model.  
- **Multiple front‑ends** – CLI, Flask, and Streamlit.  
- **Configurable generation parameters** (temperature, top‑p, top‑k, max tokens).  
- **Chat history persistence** (JSON files).  
- **Cross‑platform scripts** for Windows (`.bat`) and Linux/macOS (`.sh`).  

---

## Directory Structure
```
LLM-Chat-Bot/
│
├─ cli-only/                # Pure command‑line interface
│   ├─ app.py
│   └─ generate_secrets.py
│
├─ chatbot-web/             # Flask web UI
│   ├─ app.py
│   └─ generate_secrets.py
│
├─ streamlit_app_v2.py      # Streamlit UI
├─ generate_secrets.py      # Top‑level helper for Streamlit
│
├─ Streamlit-run-Linux.sh   # Bash script (Linux/macOS) → Streamlit
├─ Streamlit-run-NT.bat     # Batch script (Windows) → Streamlit
├─ Windows-run-webui.bat    # Batch script → Flask UI
├─ linux-run-webui.sh       # Bash script → Flask UI
├─ Windows-run-cli-only.bat # Bash script → CLI Only
├─ linux-run-cli-only.sh       # Bash script → CLI Only
│
└─ README.md
```

---

## Prerequisites
- **Python 3.9+** (recommended: use a virtual environment)  
- **Google Gemini API key** (obtain from Google AI Studio)  
- Required Python packages (see `requirements.txt`)  

---

## Installation
```bash
# Clone the repo
git clone https://github.com/weiss-rn/LLM-Chat-Bot.git
cd LLM-Chat-Bot

# Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

## Generating Secrets
The project expects a `secrets.toml` (for Streamlit) or `config.toml` (for CLI/Flask) containing:

```toml
GOOGLE_API_KEY = "YOUR_API_KEY"
```

You can create this file automatically:

### Windows
```bat
# For Streamlit
python generate_secrets.py
# For CLI / Flask
python cli-only\generate_secrets.py   # or chatbot-web\generate_secrets.py
```

### Linux / macOS
```bash
python3 generate_secrets.py          # Streamlit
python3 cli-only/generate_secrets.py # CLI / Flask
```

The scripts will prompt for the API key and write the appropriate `secrets.toml` / `config.toml`.

---

## Running the Applications

### CLI Only
```bash
# Windows
Windows-run-cli-only.bat   # (you can add the same commands as the Linux script)

# Linux / macOS
bash linux-run-cli-only.sh
```
*Or run manually:*
```bash
cd cli-only
python app.py
```

### Flask Web UI
```bat
# Windows
Windows-run-webui.bat
```
```bash
# Linux / macOS
bash linux-run-webui.sh
```
The Flask server starts at `http://0.0.0.0:5000`.

### Streamlit UI
```bat
# Windows
Streamlit-run-NT.bat
```
```bash
# Linux / macOS
bash Streamlit-run-Linux.sh
```
The Streamlit app will be available at `http://localhost:8501`.

---

## License
This project is licensed under the **Apache 2.0 License** – see the [LICENSE](LICENSE) file for details.
