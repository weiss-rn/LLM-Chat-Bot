import streamlit as st
import json
import os
from google import genai
from google.genai import types
from typing import List, Dict


st.set_page_config(
    page_title="AI Chatbot",
    page_icon="AI",
    layout="wide",
)


class ChatbotApp:
    def __init__(self):
        self.client = None
        self.setup_genai()
        self.initialize_session_state()

    def setup_genai(self):
        """Configure Google's GenAI client."""
        api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not api_key:
            st.error("Please set your Google API Key in secrets.toml or as an environment variable")
            st.stop()

        self.client = genai.Client(api_key=api_key)

    def initialize_session_state(self):
        """Initialize session state variables."""
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        if "generation_config" not in st.session_state:
            st.session_state.generation_config = None

        if "model_name" not in st.session_state:
            st.session_state.model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    def build_generation_config(self, temperature: float, top_p: float, top_k: int, max_output_tokens: int):
        """Create a generation config with specified parameters."""
        return types.GenerateContentConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
        )

    def get_bot_response(self, user_input: str, chat_history: List[Dict]) -> str:
        """Generate bot response using the model."""
        try:
            context = ""
            for message in chat_history[-5:]:
                context += f"User: {message['user']}\nAssistant: {message['bot']}\n"

            full_prompt = f"{context}User: {user_input}\nAssistant:"
            response = self.client.models.generate_content(
                model=st.session_state.model_name,
                contents=full_prompt,
                config=st.session_state.generation_config,
            )
            return response.text.strip() if response.text else "No response generated."
        except Exception as exc:
            return f"Error generating response: {exc}"

    def save_chat_history(self, chat_history: List[Dict], filename: str = "chat_history.json"):
        """Save chat history to a JSON file."""
        try:
            with open(filename, "w") as f:
                json.dump(chat_history, f, indent=2)
            return True
        except Exception as exc:
            st.error(f"Error saving chat history: {exc}")
            return False

    def load_chat_history(self, filename: str = "chat_history.json") -> List[Dict]:
        """Load chat history from a JSON file."""
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    data = json.load(f)
                return data if isinstance(data, list) else []
            return []
        except Exception as exc:
            st.error(f"Error loading chat history: {exc}")
            return []

    def run(self):
        """Main application logic."""
        st.title("AI Chatbot with Google GenAI")

        with st.sidebar:
            st.header("Model Configuration")

            temperature = st.slider(
                "Temperature (Creativity)",
                min_value=0.0,
                max_value=2.0,
                value=0.7,
                step=0.1,
                help="Higher values make responses more creative but less focused",
            )

            top_p = st.slider(
                "Top P (Nucleus Sampling)",
                min_value=0.0,
                max_value=1.0,
                value=0.8,
                step=0.1,
                help="Cumulative probability cutoff for token selection",
            )

            top_k = st.slider(
                "Top K",
                min_value=1,
                max_value=100,
                value=40,
                step=1,
                help="Number of highest probability tokens to consider",
            )

            max_tokens = st.slider(
                "Max Output Tokens",
                min_value=1,
                max_value=2048,
                value=1024,
                step=50,
                help="Maximum length of the response",
            )

            st.header("Chat History")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Clear History"):
                    st.session_state.chat_history = []
                    st.rerun()

            with col2:
                if st.button("Save History"):
                    if self.save_chat_history(st.session_state.chat_history):
                        st.success("History saved!")

            if st.button("Load History"):
                loaded_history = self.load_chat_history()
                if loaded_history:
                    st.session_state.chat_history = loaded_history
                    st.success("History loaded!")
                    st.rerun()

            st.header("Chat Statistics")
            st.write(f"Total messages: {len(st.session_state.chat_history)}")
            if st.session_state.chat_history:
                avg_user_length = (
                    sum(len(msg["user"]) for msg in st.session_state.chat_history)
                    / len(st.session_state.chat_history)
                )
                st.write(f"Avg message length: {avg_user_length:.1f} chars")

            st.header("Model")
            model_name = st.text_input("Model name", value=st.session_state.model_name)
            if model_name and model_name != st.session_state.model_name:
                st.session_state.model_name = model_name

        current_config = (temperature, top_p, top_k, max_tokens)
        if st.session_state.generation_config is None or getattr(st.session_state, "last_config", None) != current_config:
            st.session_state.generation_config = self.build_generation_config(
                temperature, top_p, top_k, max_tokens
            )
            st.session_state.last_config = current_config

        st.header("Chat")

        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                with st.chat_message("user"):
                    st.write(message["user"])

                with st.chat_message("assistant"):
                    st.write(message["bot"])

        user_input = st.chat_input("Type your message here...")

        if user_input:
            with st.chat_message("user"):
                st.write(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    bot_response = self.get_bot_response(
                        user_input,
                        st.session_state.chat_history,
                    )
                st.write(bot_response)

            st.session_state.chat_history.append({
                "user": user_input,
                "bot": bot_response,
            })

            st.rerun()

        with st.expander("Current Model Configuration"):
            st.json({
                "model": st.session_state.model_name,
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_output_tokens": max_tokens,
            })


if __name__ == "__main__":
    app = ChatbotApp()
    app.run()
