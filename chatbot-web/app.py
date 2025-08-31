from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import toml

app = Flask(__name__)

# --- Load API Key from config.toml ---
CONFIG_FILE = "config.toml"

def load_api_key():
    # Try 1: Load from config.toml
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                config = toml.load(f)
                api_key = config.get("GOOGLE_API_KEY")
                if api_key:
                    print(f"✅ API key loaded from {CONFIG_FILE}")
                    return api_key
        except Exception as e:
            print(f"Error reading {CONFIG_FILE}: {e}")

    # Try 2: Fallback to environment variable
    api_key = os.getenv("GOOGLE_API_KEY")
    if api_key:
        print("✅ API key loaded from environment variable (GOOGLE_API_KEY)")
        return api_key

    # Nothing worked
    print(f"No API key found!")
    print(f"Please create {CONFIG_FILE} with: GOOGLE_API_KEY = 'your-key'")
    print("Or set the GOOGLE_API_KEY environment variable.")
    return None

# Load key
API_KEY = load_api_key()

if not API_KEY:
    raise RuntimeError("Cannot start: No API key provided.")

# Configure GenAI
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("models/gemini-2.5-flash")

chat_history = []

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_input = request.json.get("message")
    try:
        response = model.generate_content(user_input)
        reply = response.text.strip() or "I couldn't generate a response."
        chat_history.append({"user": user_input, "bot": reply})
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"reply": f"Error: {str(e)}"})

@app.route("/clear", methods=["POST"])
def clear():
    global chat_history
    chat_history.clear()
    return jsonify({"status": "cleared"})

if __name__ == "__main__":
    print("🚀 Starting AI Chatbot...")
    app.run(host="0.0.0.0", port=5000, debug=True)