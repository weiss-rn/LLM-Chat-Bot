const chatBox = document.getElementById("chat-box");
const userInput = document.getElementById("user-input");
const themeToggle = document.getElementById("theme-toggle");
const clearBtn = document.getElementById("clear-btn");

// Toggle dark mode
themeToggle.addEventListener("click", () => {
  const isDark = document.body.classList.toggle("dark");
  themeToggle.textContent = isDark ? "☀️" : "🌙";
  localStorage.setItem("darkMode", isDark);
});

// Load saved theme
window.addEventListener("DOMContentLoaded", () => {
  const isDark = localStorage.getItem("darkMode") === "true";
  if (isDark) {
    document.body.classList.add("dark");
    themeToggle.textContent = "☀️";
  }
});

// Clear chat
clearBtn.addEventListener("click", () => {
  fetch("/clear", { method: "POST" })
    .then(() => (chatBox.innerHTML = ""))
    .catch(err => console.error("Clear failed:", err));
});

// Send message
function sendMessage() {
  const message = userInput.value.trim();
  if (!message) return;

  appendMessage("user", message);
  userInput.value = "";

  fetch("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  })
    .then(res => res.json())
    .then(data => appendMessage("bot", data.reply))
    .catch(() => appendMessage("bot", "❌ Connection error."));
}

// Append message to chat
function appendMessage(sender, text) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  div.innerHTML = `<strong>${sender === "user" ? "You" : "Bot"}:</strong> ${formatText(text)}`;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Allow line breaks and links
function formatText(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '<')
    .replace(/>/g, '>')
    .replace(/(?:\r\n|\r|\n)/g, '<br>')
    .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
}

// Send on Enter key
userInput.addEventListener("keypress", e => {
  if (e.key === "Enter") sendMessage();
});