const body = document.getElementById("body");
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
const bgUpload = document.getElementById("bg-upload");

const loaderText = [
  "                    __                ___  __ __",
  "    _______  _______/ /____  ____ ___ |__ \\\\/ // /",
  "   / ___/ / / / ___/ __/ _ \\\\/ __ `__ \\\\__/ / // /_",
  "  (__  ) /_/ (__  ) /_/  __/ / / / / / __/__  __/",
  "/____/\\\\__, /____/\\\\__/\\\\___/_/ /_/ /_/____/ /_/   ",
  "      /____/                                     "
].join("\n");

function setTheme(isDark) {
  body.classList.toggle("muted-dark", isDark);
  body.classList.toggle("muted-light", !isDark);
  themeToggle.textContent = isDark ? "THEME:DARK" : "THEME:LIGHT";
  localStorage.setItem("darkMode", String(isDark));
}

function syncEmptyState() {
  const hasMessages = chatBox.children.length > 0;
  chatBox.classList.toggle("is-empty", !hasMessages);
}

function loadSettings() {
  ["temperature", "top_p", "top_k", "max_tokens"].forEach(id => {
    const element = document.getElementById(id);
    const savedValue = localStorage.getItem(id);
    if (savedValue && element) {
      element.value = savedValue;
    }
  });
  updateValueSpans();
}

function updateValueSpans() {
  ["temperature", "top_p", "top_k", "max_tokens"].forEach(id => {
    const el = document.getElementById(id);
    const valEl = document.getElementById(`${id}-value`);
    if (el && valEl) {
      valEl.textContent = el.value;
    }
  });
}

function saveSettings() {
  ["temperature", "top_p", "top_k", "max_tokens"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      localStorage.setItem(id, el.value);
    }
  });
}

["temperature", "top_p", "top_k", "max_tokens"].forEach(id => {
  const element = document.getElementById(id);
  if (element) {
    element.addEventListener("input", () => {
      updateValueSpans();
      saveSettings();
    });
  }
});

themeToggle.addEventListener("click", () => {
  const isDark = !body.classList.contains("muted-dark");
  setTheme(isDark);
});

bgToggle.addEventListener("click", () => {
  bgModal.style.display = "block";
});

configToggleBtn.addEventListener("click", () => {
  const isVisible = configPanel.style.display === "block";
  configPanel.style.display = isVisible ? "none" : "block";
  configToggleBtn.setAttribute("aria-expanded", String(!isVisible));
});

function closeModal() {
  bgModal.style.display = "none";
}

window.closeModal = closeModal;

bgUpload.addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (file) {
    const reader = new FileReader();
    reader.onload = (ev) => {
      document.body.style.backgroundImage = `url(${ev.target.result})`;
    };
    reader.readAsDataURL(file);
  }
  closeModal();
});

document.querySelectorAll('input[name="bg"]').forEach(radio => {
  radio.addEventListener("change", () => {
    if (radio.value === "default") {
      document.body.style.backgroundImage = "";
      bgUpload.style.display = "none";
    } else {
      bgUpload.style.display = "inline-block";
    }
  });
});

fileInput.addEventListener("change", () => {
  fileName.textContent = fileInput.files[0]?.name || "";
});

function appendMessage(sender, text, file = null) {
  const div = document.createElement("div");
  div.className = `message ${sender}`;

  const label = sender === "user" ? "YOU" : "BOT";
  let content = `<span class="msg-label">${label}</span>`;
  content += `<span class="msg-text">${formatText(text)}</span>`;
  if (file) {
    content += `<span class="attachment">ATTACH ${file}</span>`;
  }

  div.innerHTML = content;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  syncEmptyState();
}

function appendLoadingMessage() {
  const div = document.createElement("div");
  div.className = "message bot loading";
  div.innerHTML = `
    <span class="msg-label">BOT</span>
    <pre class="loader-ascii">${loaderText}</pre>
    <div class="loader-bar"><span></span></div>
  `;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
  syncEmptyState();
  return div;
}

function formatText(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/(?:\r\n|\r|\n)/g, "<br>")
    .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
}

async function sendMessage() {
  const message = userInput.value.trim();
  const file = fileInput.files[0];

  if (!message && !file) {
    return;
  }

  appendMessage("user", message, file?.name);

  userInput.value = "";
  fileInput.value = "";
  fileName.textContent = "";

  const formData = new FormData();
  formData.append("message", message);
  if (file) {
    formData.append("file", file);
  }

  ["temperature", "top_p", "top_k", "max_tokens"].forEach(id => {
    const element = document.getElementById(id);
    if (element) {
      formData.append(id, element.value);
    }
  });

  const loadingEl = appendLoadingMessage();

  try {
    const res = await fetch("/chat", {
      method: "POST",
      body: formData,
    });

    let data = {};
    try {
      data = await res.json();
    } catch (err) {
      data.reply = "Invalid server response.";
    }

    loadingEl.remove();
    appendMessage("bot", data.reply || "No response generated.", data.file_preview);

    if (res.ok) {
      saveSettings();
    }
  } catch (err) {
    loadingEl.remove();
    appendMessage("bot", `Connection error: ${err.message}`);
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage();
});

clearBtn.addEventListener("click", () => {
  fetch("/clear", { method: "POST" })
    .then(() => {
      chatBox.innerHTML = "";
      syncEmptyState();
    })
    .catch(err => {
      console.error("Error clearing chat:", err);
    });
});

window.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  syncEmptyState();

  const isDark = localStorage.getItem("darkMode") === "true";
  setTheme(isDark);

  const defaultBg = document.querySelector('input[name="bg"][value="default"]');
  if (defaultBg && defaultBg.checked) {
    bgUpload.style.display = "none";
  }
});
