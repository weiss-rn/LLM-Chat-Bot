# Chatbot Web V3

System24-styled chat UI with multi-session support, import/export, model switching, and optional multi-provider backends.

## Features
- Chat sessions with separate histories (ChatGPT-style)
- Import/export chats in JSON
- Model switcher and provider selection
- Optional token usage display
- Supports Google GenAI, OpenAI-compatible, and Anthropic SDKs

## Requirements
Install dependencies from `requirements.txt`:
```bash
pip install -r requirements.txt
```

## Configuration
Create `config.toml` in this folder:
```toml
GOOGLE_API_KEY = "your-google-key"
OPENAI_API_KEY = "your-openai-key"
OPENAI_BASE_URL = "https://api.openai.com/v1"
ANTHROPIC_API_KEY = "your-anthropic-key"
CHAT_PROVIDER = "google"
GEMINI_MODEL = "gemini-2.0-flash"
```

Only the keys for your selected provider are required. You can generate a config file via:
```bash
python generate_secrets.py
```

## Run
```bash
python app.py
```
The server runs on `http://0.0.0.0:5001`.

## Import/Export Format
Exports are JSON with the following shape:
```json
{
  "version": "v3",
  "sessions": [
    {
      "id": "uuid",
      "title": "Chat title",
      "provider": "google",
      "model": "gemini-2.0-flash",
      "created_at": "2025-01-01T00:00:00Z",
      "updated_at": "2025-01-01T00:00:00Z",
      "messages": [
        {
          "role": "user",
          "content": "Hello",
          "timestamp": "2025-01-01T00:00:00Z"
        },
        {
          "role": "assistant",
          "content": "Hi!",
          "timestamp": "2025-01-01T00:00:00Z",
          "tokens": { "prompt": 5, "output": 5, "total": 10 }
        }
      ]
    }
  ]
}
```
