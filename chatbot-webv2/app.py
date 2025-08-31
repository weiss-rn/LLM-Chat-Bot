from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import toml
from pathlib import Path
import uuid

app = Flask(__name__)

# --- Configuration ---
CONFIG_FILE = "config.toml"
UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_api_key():
    """Load API key from config.toml or environment"""
    # Try 1: config.toml
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = toml.load(f)
                api_key = config.get("GOOGLE_API_KEY")
                if api_key:
                    print(f"✅ API key loaded from {CONFIG_FILE}")
                    return api_key
        except Exception as e:
            print(f"❌ Error reading {CONFIG_FILE}: {e}")

    # Try 2: Environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("✅ API key loaded from environment variable (GOOGLE_API_KEY)")
        return api_key

    # Nothing worked
    print("❌ No API key found!")
    print(f"Please create {CONFIG_FILE} with: GOOGLE_API_KEY = 'your-key'")
    print("Or set the GOOGLE_API_KEY environment variable.")
    return None

# Load and validate API key
API_KEY = load_api_key()
if not API_KEY:
    raise RuntimeError("Cannot start: No API key provided.")

# Configure Google Generative AI
genai.configure(api_key=API_KEY)
model_name = "models/gemini-1.5-flash-latest"
model = genai.GenerativeModel(model_name)

# Chat history (in-memory, per session)
chat_history = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        # Get form data
        user_message = request.form.get("message", "").strip()
        temperature = float(request.form.get("temperature", 0.7))
        top_p = float(request.form.get("top_p", 0.8))
        top_k = int(request.form.get("top_k", 40))
        max_tokens = int(request.form.get("max_tokens", 1024))

        # Handle file upload
        uploaded_file = request.files.get("file")
        temp_file_path = None
        uploaded_gemini_file = None

        # Prevent empty submission (backend check)
        if not user_message and (not uploaded_file or uploaded_file.filename == ''):
            return jsonify({"reply": "❌ Please enter a message or attach a file."}), 400

        if uploaded_file and uploaded_file.filename != '':
            # Save uploaded file temporarily
            file_extension = Path(uploaded_file.filename).suffix
            temp_filename = f"{uuid.uuid4()}{file_extension}"
            temp_file_path = os.path.join(UPLOAD_FOLDER, temp_filename)
            uploaded_file.save(temp_file_path)

            # Upload to Gemini
            try:
                uploaded_gemini_file = genai.upload_file(temp_file_path)
            except Exception as e:
                # Clean up temp file
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)
                return jsonify({"reply": f"❌ Failed to process file: {str(e)}"}), 400
            
            # Clean up temp file after upload
            if temp_file_path and os.path.exists(temp_file_path):
                os.remove(temp_file_path)

        # Build generation config
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_tokens,
        )

        # Prepare content
        contents = []
        if user_message:
            contents.append(user_message)
        if uploaded_gemini_file:
            contents.append(uploaded_gemini_file)

        # Generate response
        response = model.generate_content(
            contents,
            generation_config=generation_config
        )

        reply = response.text.strip() if response.text else "No response generated."

        # Save to chat history
        chat_history.append({
            "user": user_message,
            "file": uploaded_file.filename if uploaded_file else None,
            "bot": reply
        })

        return jsonify({
            "reply": reply,
            "file_preview": uploaded_file.filename if uploaded_file else None
        })

    except Exception as e:
        return jsonify({"reply": f"❌ Error: {str(e)}"}), 500

@app.route("/clear", methods=["POST"])
def clear():
    global chat_history
    chat_history.clear()
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    print("🚀 Starting AI Chatbot...")
    app.run(host="0.0.0.0", port=5000, debug=True)