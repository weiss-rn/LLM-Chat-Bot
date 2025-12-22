import json
import os
from google import genai
from google.genai import types
import toml

# Configuration
CONFIG_FILE = "config.toml"
HISTORY_FILE = "chat_history.json"
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def clamp(value, min_value, max_value):
    return max(min_value, min(value, max_value))


class ChatbotCLI:
    def __init__(self):
        self.chat_history = []
        self.api_key = self.load_or_request_api_key()
        self.client = None
        self.model_name = DEFAULT_MODEL
        self.generation_config = None
        self.setup_genai()
        self.load_chat_history()

    def load_or_request_api_key(self):
        """Load API key from config.toml, or ask user if not found."""
        if os.path.exists(CONFIG_FILE):
            try:
                config = toml.load(CONFIG_FILE)
                api_key = config.get("GOOGLE_API_KEY")
                if api_key:
                    print(f"[OK] API key loaded from {CONFIG_FILE}")
                    return api_key
            except Exception as exc:
                print(f"[WARN] Failed to read {CONFIG_FILE}: {exc}")

        print("[WARN] API key not found.")
        print("Please enter your Google API key")
        print(f"(It will be saved in {CONFIG_FILE} for next time)")
        api_key = input("\nAPI Key: ").strip()

        if not api_key:
            print("[ERROR] No API key provided. Exiting.")
            raise SystemExit(1)

        try:
            with open(CONFIG_FILE, "w") as f:
                toml.dump({"GOOGLE_API_KEY": api_key}, f)
            print(f"[OK] API key saved to {CONFIG_FILE}")
        except Exception as exc:
            print(f"[WARN] Could not save API key to {CONFIG_FILE}: {exc}")
            print("You may need to re-enter it next time.")

        return api_key

    def setup_genai(self):
        """Configure Google's GenAI client."""
        try:
            self.client = genai.Client(api_key=self.api_key)
            print("[OK] AI client is ready!\n")
        except Exception as exc:
            print(f"[ERROR] Failed to configure AI client: {exc}")
            raise SystemExit(1)

    def build_generation_config(
        self,
        temperature=0.7,
        top_p=0.8,
        top_k=40,
        max_output_tokens=1024,
    ):
        return types.GenerateContentConfig(
            temperature=clamp(float(temperature), 0.0, 2.0),
            top_p=clamp(float(top_p), 0.0, 1.0),
            top_k=clamp(int(top_k), 1, 100),
            max_output_tokens=clamp(int(max_output_tokens), 1, 2048),
        )

    def get_bot_response(self, user_input: str) -> str:
        """Generate response with context."""
        try:
            context = ""
            for msg in self.chat_history[-5:]:
                context += f"User: {msg['user']}\nAssistant: {msg['bot']}\n"

            full_prompt = f"{context}User: {user_input}\nAssistant:"
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=full_prompt,
                config=self.generation_config,
            )
            return response.text.strip() if response.text else "No response generated."
        except Exception as exc:
            return f"[ERROR] AI Error: {exc}"

    def load_chat_history(self, filename=HISTORY_FILE):
        """Load previous chat."""
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    self.chat_history = json.load(f)
                if not isinstance(self.chat_history, list):
                    self.chat_history = []
                print(f"[OK] Loaded {len(self.chat_history)} messages from history.\n")
            except Exception as exc:
                print(f"[WARN] Could not load chat history: {exc}")

    def save_chat_history(self, filename=HISTORY_FILE):
        """Save chat to file."""
        try:
            with open(filename, "w") as f:
                json.dump(self.chat_history, f, indent=2)
            print(f"\n[OK] Chat saved to {filename}")
        except Exception as exc:
            print(f"[ERROR] Save failed: {exc}")

    def display_menu(self):
        """Show available commands."""
        print("\n" + "=" * 50)
        print("AI CHATBOT (CLI) - Powered by Google GenAI")
        print("=" * 50)
        print("Commands:")
        print("  /save   - Save chat history")
        print("  /clear  - Clear current chat")
        print("  /config - Change AI settings")
        print("  /model  - Change model name")
        print("  /exit   - Exit and save")
        print("-" * 50)

    def configure_model(self):
        """Let user adjust generation settings."""
        print("\nModel Settings:")
        try:
            temperature = float(input("Temperature (0.0-2.0) [0.7]: ") or "0.7")
            top_p = float(input("Top P (0.0-1.0) [0.8]: ") or "0.8")
            top_k = int(input("Top K (1-100) [40]: ") or "40")
            max_tokens = int(input("Max Tokens (1-2048) [1024]: ") or "1024")
            self.generation_config = self.build_generation_config(
                temperature,
                top_p,
                top_k,
                max_tokens,
            )
            print("[OK] Model config updated!\n")
        except ValueError:
            print("[WARN] Invalid input. Using defaults.")
            self.generation_config = self.build_generation_config()

    def configure_model_name(self):
        """Let user change model name."""
        new_model = input(f"Model name [{self.model_name}]: ").strip()
        if new_model:
            self.model_name = new_model
            print(f"[OK] Model set to {self.model_name}\n")

    def run(self):
        """Main loop."""
        self.generation_config = self.build_generation_config()
        self.display_menu()

        print("Start chatting! Type a message or a command.\n")

        while True:
            try:
                user_input = input("YOU: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n[INFO] Exiting...")
                self.save_chat_history()
                break

            if not user_input:
                continue

            if user_input.lower() == "/exit":
                self.save_chat_history()
                print("Goodbye!")
                break

            if user_input.lower() == "/save":
                self.save_chat_history()
                continue

            if user_input.lower() == "/clear":
                self.chat_history.clear()
                print("[OK] Chat cleared.")
                continue

            if user_input.lower() == "/config":
                self.configure_model()
                continue

            if user_input.lower() == "/model":
                self.configure_model_name()
                continue

            bot_response = self.get_bot_response(user_input)
            print(f"BOT: {bot_response}")
            self.chat_history.append({"user": user_input, "bot": bot_response})


if __name__ == "__main__":
    app = ChatbotCLI()
    app.run()
