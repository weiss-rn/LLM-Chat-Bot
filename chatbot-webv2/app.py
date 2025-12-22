from flask import Flask, render_template, request, jsonify
from google import genai
from google.genai import types
import os
import toml
from pathlib import Path
import uuid

app = Flask(__name__)

# --- Configuration ---
CONFIG_FILE = "config.toml"
UPLOAD_FOLDER = os.path.join("static", "uploads")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def load_api_key():
    """Load API key from config.toml or environment."""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = toml.load(f)
                api_key = config.get("GOOGLE_API_KEY")
                if api_key:
                    print(f"[OK] API key loaded from {CONFIG_FILE}")
                    return api_key
        except Exception as exc:
            print(f"[WARN] Error reading {CONFIG_FILE}: {exc}")

    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("[OK] API key loaded from environment variable (GOOGLE_API_KEY)")
        return api_key

    print("[ERROR] No API key found.")
    print(f"Create {CONFIG_FILE} with: GOOGLE_API_KEY = 'your-key'")
    print("Or set the GOOGLE_API_KEY environment variable.")
    return None


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


API_KEY = load_api_key()
if not API_KEY:
    raise RuntimeError("Cannot start: No API key provided.")

client = genai.Client(api_key=API_KEY)

# Chat history (in-memory, per process)
chat_history = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    try:
        user_message = request.form.get("message", "").strip()
        temperature = parse_float(request.form.get("temperature"), 0.7, 0.0, 2.0)
        top_p = parse_float(request.form.get("top_p"), 0.8, 0.0, 1.0)
        top_k = parse_int(request.form.get("top_k"), 40, 1, 100)
        max_tokens = parse_int(request.form.get("max_tokens"), 1024, 1, 2048)

        uploaded_file = request.files.get("file")
        file_part = None
        file_name = None

        if not user_message and (not uploaded_file or uploaded_file.filename == ""):
            return jsonify({"reply": "Please enter a message or attach a file."}), 400

        if uploaded_file and uploaded_file.filename:
            file_name = uploaded_file.filename
            file_extension = Path(file_name).suffix
            temp_filename = f"{uuid.uuid4()}{file_extension}"
            temp_file_path = os.path.join(UPLOAD_FOLDER, temp_filename)

            uploaded_file.save(temp_file_path)
            try:
                uploaded_gemini_file = client.files.upload(path=temp_file_path)
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

        generation_config = types.GenerateContentConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_tokens,
        )

        contents = []
        if user_message:
            contents.append(user_message)
        if file_part:
            contents.append(file_part)

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=generation_config,
        )

        reply = response.text.strip() if response.text else "No response generated."

        chat_history.append({
            "user": user_message,
            "file": file_name,
            "bot": reply,
        })

        return jsonify({
            "reply": reply,
            "file_preview": file_name,
        })

    except Exception as exc:
        return jsonify({"reply": f"Error: {exc}"}), 500


@app.route("/clear", methods=["POST"])
def clear():
    chat_history.clear()
    return jsonify({"status": "cleared"})


if __name__ == "__main__":
    print("[INFO] Starting AI Chatbot...")
    app.run(host="0.0.0.0", port=5000, debug=True)
