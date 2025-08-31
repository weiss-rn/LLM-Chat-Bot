const chatBox = document.getElementById("chat-box");
const chatForm = document.getElementById("chat-form");
const userInput = document.getElementById("user-input");
const fileInput = document.getElementById("file-input");
const fileName = document.getElementById("file-name");
const themeToggle = document.getElementById("theme-toggle");
const bgToggle = document.getElementById("bg-toggle");
const configToggleBtn = document.getElementById("config-toggle");
const configPanel = document.getElementById("config-panel");
const clearBtn = document.getElementById("clear-btn");
const bgModal = document.getElementById("bg-modal");

// Sync UI with saved settings
function loadSettings() {
  ['temperature', 'top_p', 'top_k', 'max_tokens'].forEach(id => {
    const element = document.getElementById(id);
    const savedValue = localStorage.getItem(id);
    if (savedValue && element) {
      element.value = savedValue;
    }
  });
  updateValueSpans();
}

// Update displayed values
function updateValueSpans() {
  ['temperature', 'top_p', 'top_k', 'max_tokens'].forEach(id => {
    const el = document.getElementById(id);
    const valEl = document.getElementById(id + '-value');
    if (el && valEl) {
      valEl.textContent = el.value;
    }
  });
}

// Save settings
function saveSettings() {
  ['temperature', 'top_p', 'top_k', 'max_tokens'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      localStorage.setItem(id, el.value);
    }
  });
}

// Add event listeners for sliders to update values and save
['temperature', 'top_p', 'top_k', 'max_tokens'].forEach(id => {
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener('input', () => {
      updateValueSpans();
      saveSettings();
    });
  }
});

// Theme toggle
themeToggle.addEventListener("click", () => {
  const body = document.getElementById("body");
  const isDark = body.classList.toggle("muted-dark");
  body.classList.remove("muted-light");
  if (!isDark) {
    body.classList.add("muted-light");
  }
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

// Background upload
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

// Config panel toggle
configToggleBtn.addEventListener("click", () => {
  const isVisible = configPanel.style.display === "block";
  configPanel.style.display = isVisible ? "none" : "block";
});

// Radio button logic for background
document.querySelectorAll('input[name="bg"]').forEach(radio => {
  radio.addEventListener("change", () => {
    if (radio.value === "default") {
      document.body.style.backgroundImage = "none";
      document.body.classList.add("no-bg");
      document.getElementById("bg-upload").style.display = "none";
    } else {
      document.getElementById("bg-upload").style.display = "inline-block";
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

  // Prevent empty submission
  if (!message && !file) {
    return;
  }

  // Show user message
  appendMessage("user", message, file?.name);
  
  // Clear inputs
  userInput.value = "";
  fileInput.value = "";
  fileName.textContent = "";

  // Prepare form data
  const formData = new FormData();
  formData.append("message", message);
  if (file) {
    formData.append("file", file);
  }

  // Add config parameters
  ['temperature', 'top_p', 'top_k', 'max_tokens'].forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      formData.append(id, element.value);
    }
  });

  try {
    const res = await fetch("/chat", {
      method: "POST",
      body: formData,
    });
    
    const data = await res.json();
    
    // Show bot response
    appendMessage("bot", data.reply, data.file_preview);
    
    if (res.ok) {
      saveSettings();
    }
  } catch (err) {
    console.error("Error:", err);
    appendMessage("bot", "❌ Connection error.");
  }
});

// Append message to chat
function appendMessage(sender, text, file = null) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;
  
  let content = `<strong>${sender === "user" ? "You" : "Bot"}:</strong> ${formatText(text)}`;
  if (file) {
    content += `<br><em>📎 ${file}</em>`;
  }
  
  div.innerHTML = content;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
}

// Format text with basic HTML escaping
function formatText(text) {
  if (!text) return "";
  
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/(?:\r\n|\r|\n)/g, '<br>')
    .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
}

// Clear chat
clearBtn.addEventListener("click", () => {
  fetch("/clear", { method: "POST" })
    .then(() => {
      chatBox.innerHTML = "";
    })
    .catch(err => {
      console.error("Error clearing chat:", err);
    });
});

// Load settings on page load
window.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  
  // Apply saved theme
  const isDark = localStorage.getItem("darkMode") === "true";
  if (isDark) {
    document.getElementById("body").classList.remove("muted-light");
    document.getElementById("body").classList.add("muted-dark");
    themeToggle.textContent = "☀️";
  }
});