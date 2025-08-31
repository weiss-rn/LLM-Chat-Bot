# LLM‑Chat‑Bot

A lightweight chatbot powered by large language models (LLMs) that can be integrated into various applications for natural language interactions.

## Features
- **LLM integration** – Connects to popular LLM like Gemini.
- **Modular architecture** – Easy to extend with custom prompts and handlers.  
- **Simple CLI** – Quick testing from the command line.  
- **Configurable** – Settings stored in a JSON/YAML file.

## Prerequisites
- Python 3.9+ (or Node.js if using the JavaScript version)  
- Access token/API key from Google Studio.
- `git` for cloning the repository  

## Installation
```bash
# Clone the repository
git clone https://github.com/weiss-rn/LLM-Chat-Bot.git
cd LLM-Chat-Bot

# Install dependencies (Python example)
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
```bash
# Run the chatbot (Python example)
python main.py --config config.yaml
```
Edit `config.yaml` to set your API key and model preferences.

## License

This project is licensed under the Apache 2.0 – see the [LICENSE](LICENSE) file for details.
