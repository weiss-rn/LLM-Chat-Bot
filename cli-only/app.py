import json
import os
import google.generativeai as genai
import toml

# Configuration
CONFIG_FILE = "config.toml"
HISTORY_FILE = "chat_history.json"

class ChatbotCLI:
    def __init__(self):
        self.chat_history = []
        self.model = None
        self.api_key = self.load_or_request_api_key()
        self.setup_genai()
        self.load_chat_history()

    def load_or_request_api_key(self):
        """Load API key from config.toml, or ask user if not found"""
        # Try to load from config.toml
        if os.path.exists(CONFIG_FILE):
            try:
                config = toml.load(CONFIG_FILE)
                api_key = config.get("GOOGLE_API_KEY")
                if api_key:
                    print(f"✅ API key loaded from {CONFIG_FILE}")
                    return api_key
            except Exception as e:
                print(f"⚠️  Failed to read {CONFIG_FILE}: {e}")

        # If not found, prompt user
        print("🔐 API key not found.")
        print(f"Please enter your Google Generative AI API key")
        print("(It will be saved in {CONFIG_FILE} for next time)")
        api_key = input("\nAPI Key: ").strip()

        if not api_key:
            print("❌ No API key provided. Exiting.")
            exit(1)

        # Save to config.toml for future
        try:
            with open(CONFIG_FILE, "w") as f:
                toml.dump({"GOOGLE_API_KEY": api_key}, f)
            print(f"✅ API key saved to {CONFIG_FILE}")
        except Exception as e:
            print(f"⚠️  Could not save API key to {CONFIG_FILE}: {e}")
            print("You may need to re-enter it next time.")

        return api_key

    def setup_genai(self):
        """Configure Google's Generative AI"""
        try:
            genai.configure(api_key=self.api_key)
            print("🚀 AI model is ready!\n")
        except Exception as e:
            print(f"❌ Failed to configure AI: {e}")
            exit(1)

    def create_model_with_config(self, temperature=0.7, top_p=0.8, top_k=40, max_output_tokens=1024):
        """Create generative model with config"""
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
        )
        return genai.GenerativeModel(
            model_name="models/gemini-2.5-flash",
            generation_config=generation_config
        )

    def get_bot_response(self, user_input: str) -> str:
        """Generate response with context"""
        try:
            # Use last 5 messages as context
            context = ""
            for msg in self.chat_history[-5:]:
                context += f"User: {msg['user']}\nAssistant: {msg['bot']}\n"

            full_prompt = f"{context}User: {user_input}\nAssistant:"
            response = self.model.generate_content(full_prompt)
            return response.text.strip()
        except Exception as e:
            return f"❌ AI Error: {str(e)}"

    def load_chat_history(self, filename=HISTORY_FILE):
        """Load previous chat"""
        if os.path.exists(filename):
            try:
                with open(filename, "r") as f:
                    self.chat_history = json.load(f)
                print(f"📂 Loaded {len(self.chat_history)} messages from history.\n")
            except Exception as e:
                print(f"⚠️  Could not load chat history: {e}")

    def save_chat_history(self, filename=HISTORY_FILE):
        """Save chat to file"""
        try:
            with open(filename, "w") as f:
                json.dump(self.chat_history, f, indent=2)
            print(f"\n💾 Chat saved to {filename}")
        except Exception as e:
            print(f"❌ Save failed: {e}")

    def display_menu(self):
        """Show available commands"""
        print("\n" + "="*50)
        print("🤖 AI CHATBOT (CLI) - Powered by Google's Gemini")
        print("="*50)
        print("Commands:")
        print("  /save   - Save chat history")
        print("  /clear  - Clear current chat")
        print("  /config - Change AI settings")
        print("  /exit   - Exit and save")
        print("-" * 50)

    def configure_model(self):
        """Let user adjust generation settings"""
        print("\n🔧 Model Settings:")
        try:
            temperature = float(input(f"Temperature (0.0–2.0) [0.7]: ") or "0.7")
            top_p = float(input(f"Top P (0.0–1.0) [0.8]: ") or "0.8")
            top_k = int(input(f"Top K (1–100) [40]: ") or "40")
            max_tokens = int(input(f"Max Tokens (50–2048) [1024]: ") or "1024")

            self.model = self.create_model_with_config(temperature, top_p, top_k, max_tokens)
            print("✅ Model updated!\n")
        except ValueError:
            print("❌ Invalid input. Using defaults.")
            self.model = self.create_model_with_config()

    def run(self):
        """Main loop"""
        self.model = self.create_model_with_config()  # default config
        self.display_menu()

        print("💬 Start chatting! Type a message or a command.\n")

        while True:
            user_input = input("🧑 YOU: ").strip()

            if not user_input:
                continue

            if user_input.lower() == "/exit":
                self.save_chat_history()
                print("👋 Goodbye!")
                break

            elif user_input.lower() == "/save":
                self.save_chat_history()

            elif user_input.lower() == "/clear":
                self.chat_history.clear()
                print("🗑️  Chat cleared.")

            elif user_input.lower() == "/config":
                self.configure_model()

            else:
                # Generate response
                bot_response = self.get_bot_response(user_input)
                print(f"🤖 BOT: {bot_response}")

                # Save to history
                self.chat_history.append({"user": user_input, "bot": bot_response})

if __name__ == "__main__":
    app = ChatbotCLI()
    app.run()