import streamlit as st
import json
import os
import google.generativeai as genai
from typing import List, Dict


# Configure the page
st.set_page_config(
    page_title="AI Chatbot",
    page_icon="AI",
    layout="wide",
)


class ChatbotApp:
    def __init__(self):
        self.setup_genai()
        self.initialize_session_state()

    def setup_genai(self):
        """Configure Google's Generative AI"""
        # You'll need to set your API key
        # Either set it as an environment variable or directly here
        api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not api_key:
            st.error("Please set your Google API Key in secrets.toml or as an environment variable")
            st.stop()

        genai.configure(api_key=api_key)

    def initialize_session_state(self):
        """Initialize session state variables"""
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        if "model" not in st.session_state:
            st.session_state.model = None

    def create_model_with_config(self, temperature: float, top_p: float, top_k: int, max_output_tokens: int):
        """Create a generative model with specified configuration"""
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            max_output_tokens=max_output_tokens,
        )

        model = genai.GenerativeModel(
            model_name="models/gemini-2.5-flash",
            generation_config=generation_config,
        )

        return model

    def get_bot_response(self, user_input: str, model, chat_history: List[Dict]) -> str:
        """Generate bot response using the model"""
        try:
            # Prepare conversation context
            context = ""
            for message in chat_history[-5:]:  # Use last 5 messages for context
                context += f"User: {message['user']}\nAssistant: {message['bot']}\n"

            # Add current user input
            full_prompt = f"{context}User: {user_input}\nAssistant:"

            response = model.generate_content(full_prompt)
            return response.text.strip() if response.text else "No response generated."

        except Exception as e:
            return f"Error generating response: {str(e)}"

    def save_chat_history(self, chat_history: List[Dict], filename: str = "chat_history.json"):
        """Save chat history to a JSON file"""
        try:
            with open(filename, "w") as f:
                json.dump(chat_history, f, indent=2)
            return True
        except Exception as e:
            st.error(f"Error saving chat history: {str(e)}")
            return False

    def load_chat_history(self, filename: str = "chat_history.json") -> List[Dict]:
        """Load chat history from a JSON file"""
        try:
            if os.path.exists(filename):
                with open(filename, "r") as f:
                    return json.load(f)
            return []
        except Exception as e:
            st.error(f"Error loading chat history: {str(e)}")
            return []

    def run(self):
        """Main application logic"""
        st.title("AI Chatbot with Google Generative AI")

        # Sidebar for configuration
        with st.sidebar:
            st.header("Model Configuration")

            # Sampling parameters
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
                min_value=50,
                max_value=2048,
                value=1024,
                step=50,
                help="Maximum length of the response",
            )

            # Chat history management
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

            # Display chat statistics
            st.header("Chat Statistics")
            st.write(f"Total messages: {len(st.session_state.chat_history)}")
            if st.session_state.chat_history:
                avg_user_length = (
                    sum(len(msg["user"]) for msg in st.session_state.chat_history)
                    / len(st.session_state.chat_history)
                )
                st.write(f"Avg message length: {avg_user_length:.1f} chars")

        # Create or update model when parameters change
        current_config = (temperature, top_p, top_k, max_tokens)
        if st.session_state.model is None or getattr(st.session_state, "last_config", None) != current_config:
            st.session_state.model = self.create_model_with_config(temperature, top_p, top_k, max_tokens)
            st.session_state.last_config = current_config

        # Main chat interface
        st.header("Chat")

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.chat_history:
                # User message
                with st.chat_message("user"):
                    st.write(message["user"])

                # Bot message
                with st.chat_message("assistant"):
                    st.write(message["bot"])

        # Chat input
        user_input = st.chat_input("Type your message here...")

        if user_input:
            # Display user message immediately
            with st.chat_message("user"):
                st.write(user_input)

            # Generate and display bot response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    bot_response = self.get_bot_response(
                        user_input,
                        st.session_state.model,
                        st.session_state.chat_history,
                    )
                st.write(bot_response)

            # Add to chat history
            st.session_state.chat_history.append({
                "user": user_input,
                "bot": bot_response,
            })

            # Rerun to update the display
            st.rerun()

        # Display model info
        with st.expander("Current Model Configuration"):
            st.json({
                "model": "models/gemini-2.5-flash",
                "temperature": temperature,
                "top_p": top_p,
                "top_k": top_k,
                "max_output_tokens": max_tokens,
            })


# Run the app
if __name__ == "__main__":
    app = ChatbotApp()
    app.run()
