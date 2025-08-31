const chatBox = document.getElementById("chat-box");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const fileInput = document.getElementById("file-input");
const fileName = document.getElementById("file-name");
const themeToggle = document.getElementById("theme-toggle");
const bgToggle = document.getElementById("bg-toggle");
const configToggle = document.getElementById("config-panel");
const clearBtn = document.getElementById("clear-btn");
const bgModal = document.getElementById("bg-modal");

// Sync UI with saved settings
function loadSettings() {
  document.getElementById("temperature").value = localStorage.getItem("temp") || 0.7;
  document.getElementById("top_p").value = localStorage.getItem("top_p") || 0.8;
  document.getElementById("top_k").value = localStorage.getItem("top_k") || 40;
  document.getElementById("max_tokens").value = localStorage.getItem("max_tokens") || 1024;
  updateValueSpans();
}

// Update displayed values
function updateValueSpans() {
  ['temperature', 'top_p', 'top_k', 'max_tokens'].forEach(id => {
    const el = document.getElementById(id);
    const valEl = document.getElementById(id + '-value');
    if (el && valEl) valEl.textContent = el.value;
  });
}

// Save settings
function saveSettings() {
  ['temperature', 'top_p', 'top_k', 'max_tokens'].forEach(id => {
    const el = document.getElementById(id);
    if (el) localStorage.setItem(id, el.value);
  });
}

// Theme toggle
themeToggle.addEventListener("click", () => {
  const body = document.getElementById("body");
  const isDark = body.classList.toggle("muted-dark");
  themeToggle.textContent = isDark ? "☀️" : "🌙";
  localStorage.setItem("darkMode", isDark);
});

// Background toggle
bgToggle.addEventListener("click", () => {
  bgModal.style.display = "block";
});

function closeModal() {
  bgModal.style.display = "none";
}

document.getElementById("bg-upload").addEventListener("change", (e) => {
  const file = e.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (ev) => {
      document.body.style.backgroundImage = `url(${ev.target.result})`;
      document.body.classList.remove("no-bg");
    };
    reader.readAsDataURL(file);
  }
  closeModal();
});

// Radio button logic
document.querySelectorAll('input[name="bg"]').forEach(radio => {
  radio.addEventListener("change", () => {
    if (radio.value === "default") {
      document.body.style.backgroundImage = "url('/static/default-bg.jpg')";
      document.body.classList.remove("no-bg");
    } else {
      document.body.classList.add("no-bg");
    }
  });
});

// File name display
fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "";
});

// Send message
chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const message = userInput.value.trim();
  const file = fileInput.files[0];

  if (!message && !file) return;

  appendMessage("user", message, file?.name);
  userInput.value = "";
  fileInput.value = "";
  fileName.textContent = "";

  const formData = new FormData(chatForm);
  formData.append("message", message);
  formData.append("file", file);

  // Add config
['temperature', 'top_p', 'top_k', 'max_tokens'].forEach(id => {
  formData.append(id, document.getElementById(id).value);
});

  try {
    const res = await fetch("/chat", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    appendMessage("bot", data.reply, data.file_preview);
    saveSettings();
  } catch (err) {
    appendMessage("bot", "❌ Connection error.");
  }
});

// Append message
function appendMessage(sender, text, file = null) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  let content = `<strong>${sender === "user" ? "You" : "Bot"}:</strong> ${formatText(text)}`;
  if (file) content += `<br><em>📎 ${file}</em>`;
  div.innerHTML = content;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Format text
function formatText(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '<')
    .replace(/>/g, '>')
    .replace(/(?:\r\n|\r|\n)/g, '<br>')
    .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
}

// Clear chat
clearBtn.addEventListener("click", () => {
  fetch("/clear", { method: "POST" }).then(() => {
    chatBox.innerHTML = "";
  });
});

// Load on start
window.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  const isDark = localStorage.getItem("darkMode") === "true";
  if (isDark) {
    document.getElementById("body").classList.add("muted-dark");
    themeToggle.textContent = "☀️";
  }
});