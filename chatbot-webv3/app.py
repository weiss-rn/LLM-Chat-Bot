from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
import os
import toml
from pathlib import Path
import uuid
from datetime import datetime

app = Flask(__name__)

# --- Configuration ---
CONFIG_FILE = "config.toml"
UPLOAD_FOLDER = os.path.join("static", "uploads")
DEFAULT_PROVIDER = "google"
DEFAULT_MODEL = "gemini-2.5-flash"
MAX_HISTORY_MESSAGES = 30
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_config():
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = toml.load(f)
        except Exception as exc:
            print(f"[WARN] Error reading {CONFIG_FILE}: {exc}")

    def get_value(key, default=None):
        return os.getenv(key) or config.get(key, default)

    return {
        "google_api_key": get_value("GOOGLE_API_KEY"),
        "openai_api_key": get_value("OPENAI_API_KEY"),
        "openai_base_url": get_value("OPENAI_BASE_URL"),
        "anthropic_api_key": get_value("ANTHROPIC_API_KEY"),
        "default_provider": get_value("CHAT_PROVIDER", DEFAULT_PROVIDER),
        "default_model": get_value("GEMINI_MODEL", DEFAULT_MODEL),
    }


def iso_now():
    return datetime.utcnow().isoformat() + "Z"


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


def parse_float(value, default, min_value, max_value):
    try:
        return clamp(float(value), min_value, max_value)
    except (TypeError, ValueError):
        return default


def parse_int(value, default, min_value, max_value):
    try:
        return int(clamp(int(value), min_value, max_value))
    except (TypeError, ValueError):
        return default


def estimate_tokens(text):
    if not text:
        return 0
    return max(1, len(text.split()))


CONFIG = load_config()

google_client = None
if CONFIG["google_api_key"]:
    google_client = genai.Client(api_key=CONFIG["google_api_key"])


def get_openai_client(base_url=None):
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI SDK not installed. Install openai in requirements.") from exc

    api_key = CONFIG["openai_api_key"]
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured.")

    return OpenAI(api_key=api_key, base_url=base_url or CONFIG["openai_base_url"])


def get_anthropic_client():
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Anthropic SDK not installed. Install anthropic in requirements.") from exc

    api_key = CONFIG["anthropic_api_key"]
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured.")

    return anthropic.Anthropic(api_key=api_key)


def create_session(title=None, provider=None, model=None):
    session_id = str(uuid.uuid4())
    now = iso_now()
    session_title = title or "New Chat"
    sessions[session_id] = {
        "id": session_id,
        "title": session_title,
        "provider": provider or CONFIG["default_provider"],
        "model": model or CONFIG["default_model"],
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }
    return sessions[session_id]


def list_sessions():
    return sorted(
        sessions.values(),
        key=lambda item: item["updated_at"],
        reverse=True,
    )


def session_summary(session):
    return {
        "id": session["id"],
        "title": session["title"],
        "provider": session["provider"],
        "model": session["model"],
        "created_at": session["created_at"],
        "updated_at": session["updated_at"],
        "message_count": len(session["messages"]),
    }


def normalize_messages(messages):
    if not isinstance(messages, list):
        return []
    normalized = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role")
        content = msg.get("content", "")
        if role not in ("user", "assistant"):
            continue
        normalized.append({
            "role": role,
            "content": content,
            "timestamp": msg.get("timestamp") or iso_now(),
            "file": msg.get("file"),
            "tokens": msg.get("tokens"),
        })
    return normalized


def build_google_contents(history, user_text, file_part):
    contents = []
    for msg in history:
        role = "user" if msg["role"] == "user" else "model"
        contents.append(types.Content(
            role=role,
            parts=[types.Part.from_text(msg["content"])]
        ))

    parts = []
    if user_text:
        parts.append(types.Part.from_text(user_text))
    if file_part:
        parts.append(file_part)
    if parts:
        contents.append(types.Content(role="user", parts=parts))
    return contents


def build_openai_messages(history, user_text):
    messages = []
    for msg in history:
        messages.append({
            "role": "assistant" if msg["role"] == "assistant" else "user",
            "content": msg["content"],
        })
    messages.append({"role": "user", "content": user_text})
    return messages


def build_anthropic_messages(history, user_text):
    messages = []
    for msg in history:
        messages.append({
            "role": "assistant" if msg["role"] == "assistant" else "user",
            "content": msg["content"],
        })
    messages.append({"role": "user", "content": user_text})
    return messages


def maybe_autotitle(session, user_message):
    if not user_message:
        return
    if session["title"] != "New Chat":
        return
    words = user_message.strip().split()
    if not words:
        return
    session["title"] = " ".join(words[:6])


sessions = {}
create_session()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/sessions", methods=["GET"])
def get_sessions():
    sessions_list = list_sessions()
    return jsonify({
        "sessions": [session_summary(item) for item in sessions_list],
        "active_session_id": sessions_list[0]["id"] if sessions_list else None,
    })


@app.route("/sessions", methods=["POST"])
def create_session_route():
    data = request.get_json(silent=True) or {}
    session = create_session(
        title=data.get("title"),
        provider=data.get("provider"),
        model=data.get("model"),
    )
    return jsonify(session)


@app.route("/sessions/<session_id>", methods=["GET"])
def get_session_route(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    return jsonify(session)


@app.route("/sessions/<session_id>/rename", methods=["POST"])
def rename_session(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if title:
        session["title"] = title
        session["updated_at"] = iso_now()
    return jsonify(session)


@app.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    session = sessions.pop(session_id, None)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    if not sessions:
        create_session()
    return jsonify({
        "status": "deleted",
        "sessions": [session_summary(item) for item in list_sessions()],
    })


@app.route("/sessions/<session_id>/clear", methods=["POST"])
def clear_session(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    session["messages"] = []
    session["updated_at"] = iso_now()
    return jsonify(session)


@app.route("/sessions/<session_id>/export", methods=["GET"])
def export_session(session_id):
    session = sessions.get(session_id)
    if not session:
        return jsonify({"error": "Session not found."}), 404
    return jsonify({
        "version": "v3",
        "sessions": [session],
    })


@app.route("/sessions/export", methods=["GET"])
def export_all_sessions():
    return jsonify({
        "version": "v3",
        "sessions": list_sessions(),
    })


@app.route("/sessions/import", methods=["POST"])
def import_sessions():
    data = None
    if "file" in request.files:
        try:
            data = request.files["file"].read().decode("utf-8")
        except Exception as exc:
            return jsonify({"error": f"Failed to read file: {exc}"}), 400

    if data:
        try:
            import json
            payload = json.loads(data)
        except Exception as exc:
            return jsonify({"error": f"Invalid JSON: {exc}"}), 400
    else:
        payload = request.get_json(silent=True) or {}

    sessions_data = []
    if isinstance(payload, dict):
        if "sessions" in payload:
            sessions_data = payload.get("sessions") or []
        elif "messages" in payload:
            sessions_data = [payload]
    elif isinstance(payload, list):
        sessions_data = payload

    if not sessions_data:
        return jsonify({"error": "No sessions found to import."}), 400

    imported_ids = []
    for entry in sessions_data:
        if not isinstance(entry, dict):
            continue
        new_session = create_session(
            title=entry.get("title") or "Imported Chat",
            provider=entry.get("provider"),
            model=entry.get("model"),
        )
        new_session["messages"] = normalize_messages(entry.get("messages", []))
        new_session["created_at"] = entry.get("created_at") or iso_now()
        new_session["updated_at"] = entry.get("updated_at") or iso_now()
        imported_ids.append(new_session["id"])

    return jsonify({
        "imported": imported_ids,
        "sessions": [session_summary(item) for item in list_sessions()],
    })


@app.route("/chat", methods=["POST"])
def chat():
    try:
        session_id = request.form.get("session_id")
        session = sessions.get(session_id)
        if not session:
            session = create_session()
            session_id = session["id"]

        provider = (request.form.get("provider") or session["provider"]).strip()
        if not provider:
            provider = CONFIG["default_provider"]
        model_name = (request.form.get("model") or session["model"]).strip()
        openai_base_url = (request.form.get("openai_base_url") or "").strip()

        user_message = request.form.get("message", "").strip()
        temperature = parse_float(request.form.get("temperature"), 0.7, 0.0, 2.0)
        top_p = parse_float(request.form.get("top_p"), 0.8, 0.0, 1.0)
        top_k = parse_int(request.form.get("top_k"), 40, 1, 100)
        max_tokens = parse_int(request.form.get("max_tokens"), 1024, 1, 4096)

        uploaded_file = request.files.get("file")
        file_part = None
        file_name = None

        if not user_message and (not uploaded_file or uploaded_file.filename == ""):
            return jsonify({"reply": "Please enter a message or attach a file."}), 400

        if uploaded_file and uploaded_file.filename:
            if provider != "google":
                return jsonify({"reply": "File uploads are only supported for Google GenAI."}), 400

            file_name = uploaded_file.filename
            file_extension = Path(file_name).suffix
            temp_filename = f"{uuid.uuid4()}{file_extension}"
            temp_file_path = os.path.join(UPLOAD_FOLDER, temp_filename)
            uploaded_file.save(temp_file_path)
            try:
                if not google_client:
                    raise RuntimeError("GOOGLE_API_KEY is not configured.")
                uploaded_gemini_file = google_client.files.upload(path=temp_file_path)
                mime_type = uploaded_gemini_file.mime_type or "application/octet-stream"
                file_part = types.Part.from_uri(
                    uploaded_gemini_file.uri,
                    mime_type=mime_type,
                )
            except Exception as exc:
                return jsonify({"reply": f"Failed to process file: {exc}"}), 400
            finally:
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        history = session["messages"][-MAX_HISTORY_MESSAGES:]

        generation_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_tokens,
        )

        reply = ""
        usage = None

        if provider == "google":
            if not google_client:
                return jsonify({"reply": "GOOGLE_API_KEY is not configured."}), 400
            model_name = model_name or CONFIG["default_model"]
            contents = build_google_contents(history, user_message, file_part)
            response = google_client.models.generate_content(
                model=model_name,
                contents=contents,
                config=generation_config,
            )
            reply = response.text.strip() if response.text else "No response generated."
            usage_metadata = getattr(response, "usage_metadata", None)
            if usage_metadata:
                usage = {
                    "prompt": getattr(usage_metadata, "prompt_token_count", None),
                    "output": getattr(usage_metadata, "candidates_token_count", None),
                    "total": getattr(usage_metadata, "total_token_count", None),
                }
        elif provider == "openai":
            if uploaded_file:
                return jsonify({"reply": "File uploads are not supported for OpenAI compatible providers."}), 400
            client = get_openai_client(base_url=openai_base_url or None)
            messages = build_openai_messages(history, user_message)
            model_name = model_name or "gpt-4o-mini"
            response = client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
            )
            reply = response.choices[0].message.content.strip()
            if response.usage:
                usage = {
                    "prompt": getattr(response.usage, "prompt_tokens", None),
                    "output": getattr(response.usage, "completion_tokens", None),
                    "total": getattr(response.usage, "total_tokens", None),
                }
        elif provider == "anthropic":
            if uploaded_file:
                return jsonify({"reply": "File uploads are not supported for Anthropic."}), 400
            client = get_anthropic_client()
            messages = build_anthropic_messages(history, user_message)
            model_name = model_name or "claude-3-5-sonnet-20241022"
            response = client.messages.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                messages=messages,
            )
            reply = "".join(block.text for block in response.content if block.type == "text").strip()
            usage = {
                "prompt": getattr(response.usage, "input_tokens", None),
                "output": getattr(response.usage, "output_tokens", None),
                "total": getattr(response.usage, "input_tokens", 0) + getattr(response.usage, "output_tokens", 0),
            }
        else:
            return jsonify({"reply": "Unknown provider selected."}), 400

        if not usage:
            usage = {
                "prompt": estimate_tokens(user_message),
                "output": estimate_tokens(reply),
                "total": None,
            }

        user_entry = {
            "role": "user",
            "content": user_message,
            "timestamp": iso_now(),
            "file": file_name,
        }
        session["messages"].append(user_entry)
        session["messages"].append({
            "role": "assistant",
            "content": reply,
            "timestamp": iso_now(),
            "tokens": usage,
        })
        session["provider"] = provider
        session["model"] = model_name
        session["updated_at"] = iso_now()
        maybe_autotitle(session, user_message)

        return jsonify({
            "reply": reply,
            "file_preview": file_name,
            "session_id": session_id,
            "session": session,
            "usage": usage,
        })

    except Exception as exc:
        return jsonify({"reply": f"Error: {exc}"}), 500


if __name__ == "__main__":
    print("[INFO] Starting AI Chatbot V3...")
    app.run(host="0.0.0.0", port=5001, debug=True)
