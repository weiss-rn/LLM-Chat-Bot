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
const sessionListEl = document.getElementById("session-list");
const newSessionBtn = document.getElementById("new-session");
const importSessionBtn = document.getElementById("import-session");
const importFileInput = document.getElementById("import-file");
const exportAllBtn = document.getElementById("export-all");
const exportSessionBtn = document.getElementById("export-session");
const sessionTitleInput = document.getElementById("session-title");
const renameSessionBtn = document.getElementById("rename-session");
const providerSelect = document.getElementById("provider");
const modelInput = document.getElementById("model");
const openaiBaseUrlInput = document.getElementById("openai_base_url");
const showTokensToggle = document.getElementById("show-tokens");

const loaderText = [
  "                    __                ___  __ __",
  "    _______  _______/ /____  ____ ___ |__ \\\\/ // /",
  "   / ___/ / / / ___/ __/ _ \\\\/ __ `__ \\\\__/ / // /_",
  "  (__  ) /_/ (__  ) /_/  __/ / / / / / __/__  __/",
  "/____/\\\\__, /____/\\\\__/\\\\___/_/ /_/ /_/____/ /_/   ",
  "      /____/                                     "
].join("\n");

const state = {
  sessions: [],
  activeSessionId: null,
  activeSession: null,
};

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
  ["temperature", "top_p", "top_k", "max_tokens", "provider", "model", "openai_base_url"].forEach(id => {
    const element = document.getElementById(id);
    const savedValue = localStorage.getItem(id);
    if (savedValue && element) {
      element.value = savedValue;
    }
  });
  const showTokens = localStorage.getItem("show_tokens") === "true";
  showTokensToggle.checked = showTokens;
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
  ["temperature", "top_p", "top_k", "max_tokens", "provider", "model", "openai_base_url"].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      localStorage.setItem(id, el.value);
    }
  });
  localStorage.setItem("show_tokens", String(showTokensToggle.checked));
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

[providerSelect, modelInput, openaiBaseUrlInput, showTokensToggle].forEach(element => {
  if (element) {
    element.addEventListener("change", () => {
      saveSettings();
      if (element === showTokensToggle && state.activeSession) {
        renderMessages(state.activeSession.messages || []);
      }
      if (element === providerSelect) {
        updateProviderFields();
      }
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

function formatText(text) {
  if (!text) return "";
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/(?:\r\n|\r|\n)/g, "<br>")
    .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
}

function formatTokens(tokens) {
  if (!tokens) return "";
  const prompt = tokens.prompt ?? "-";
  const output = tokens.output ?? "-";
  const total = tokens.total ?? "-";
  return `TOKENS P:${prompt} O:${output} T:${total}`;
}

function appendMessage(message) {
  const div = document.createElement("div");
  div.className = `message ${message.role === "user" ? "user" : "bot"}`;

  const label = message.role === "user" ? "YOU" : "BOT";
  let content = `<span class="msg-label">${label}</span>`;
  content += `<span class="msg-text">${formatText(message.content)}</span>`;
  if (message.file) {
    content += `<span class="attachment">ATTACH ${message.file}</span>`;
  }
  if (showTokensToggle.checked && message.tokens) {
    content += `<span class="msg-meta">${formatTokens(message.tokens)}</span>`;
  }

  div.innerHTML = content;
  chatBox.appendChild(div);
  chatBox.scrollTop = chatBox.scrollHeight;
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

function renderMessages(messages) {
  chatBox.innerHTML = "";
  messages.forEach(msg => appendMessage(msg));
  syncEmptyState();
}

function renderSessions() {
  sessionListEl.innerHTML = "";
  state.sessions.forEach(session => {
    const item = document.createElement("div");
    item.className = "session-item";
    if (session.id === state.activeSessionId) {
      item.classList.add("active");
    }
    item.addEventListener("click", () => {
      loadSession(session.id);
    });

    const text = document.createElement("div");
    text.className = "session-title-text";
    text.textContent = session.title || "New Chat";

    const meta = document.createElement("div");
    meta.className = "session-meta";
    meta.textContent = `${session.provider || "google"} | ${session.model || ""}`.trim();

    item.appendChild(text);
    item.appendChild(meta);
    sessionListEl.appendChild(item);
  });
}

async function loadSessions() {
  const res = await fetch("/sessions");
  const data = await res.json();
  state.sessions = data.sessions || [];
  if (!state.activeSessionId && data.active_session_id) {
    state.activeSessionId = data.active_session_id;
  }
  renderSessions();
  if (state.activeSessionId) {
    await loadSession(state.activeSessionId);
  }
}

async function loadSession(sessionId) {
  const res = await fetch(`/sessions/${sessionId}`);
  if (!res.ok) return;
  const session = await res.json();
  state.activeSessionId = session.id;
  state.activeSession = session;
  sessionTitleInput.value = session.title || "";
  providerSelect.value = session.provider || providerSelect.value;
  modelInput.value = session.model || modelInput.value;
  renderMessages(session.messages || []);
  renderSessions();
  updateProviderFields();
}

async function createSession() {
  const res = await fetch("/sessions", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: "New Chat",
      provider: providerSelect.value,
      model: modelInput.value,
    }),
  });
  const session = await res.json();
  state.activeSessionId = session.id;
  state.activeSession = session;
  state.sessions.unshift(session);
  renderSessions();
  await loadSession(session.id);
}

async function renameSession() {
  if (!state.activeSessionId) return;
  const title = sessionTitleInput.value.trim();
  const res = await fetch(`/sessions/${state.activeSessionId}/rename`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ title }),
  });
  const session = await res.json();
  const idx = state.sessions.findIndex(item => item.id === session.id);
  if (idx >= 0) {
    state.sessions[idx] = session;
  }
  renderSessions();
}

async function clearSession() {
  if (!state.activeSessionId) return;
  const res = await fetch(`/sessions/${state.activeSessionId}/clear`, { method: "POST" });
  if (res.ok) {
    const session = await res.json();
    state.activeSession = session;
    renderMessages(session.messages || []);
  }
}

async function exportSession() {
  if (!state.activeSessionId) return;
  const res = await fetch(`/sessions/${state.activeSessionId}/export`);
  const data = await res.json();
  downloadJson(data, `chat-session-${state.activeSessionId}.json`);
}

async function exportAllSessions() {
  const res = await fetch("/sessions/export");
  const data = await res.json();
  downloadJson(data, "chat-sessions.json");
}

function downloadJson(data, filename) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

async function importSessions(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch("/sessions/import", {
    method: "POST",
    body: formData,
  });
  const data = await res.json();
  if (!res.ok) {
    appendMessage({ role: "assistant", content: data.error || "Import failed." });
    return;
  }
  state.sessions = data.sessions || [];
  state.activeSessionId = data.imported?.[0] || state.activeSessionId;
  renderSessions();
  if (state.activeSessionId) {
    await loadSession(state.activeSessionId);
  }
}

async function sendMessage() {
  const message = userInput.value.trim();
  const file = fileInput.files[0];

  if (!message && !file) {
    return;
  }

  if (!state.activeSessionId) {
    await createSession();
  }

  appendMessage({ role: "user", content: message, file: file?.name });

  userInput.value = "";
  fileInput.value = "";
  fileName.textContent = "";

  const formData = new FormData();
  formData.append("session_id", state.activeSessionId);
  formData.append("message", message);
  formData.append("provider", providerSelect.value);
  formData.append("model", modelInput.value);
  formData.append("openai_base_url", openaiBaseUrlInput.value);
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

    if (!res.ok) {
      appendMessage({ role: "assistant", content: data.reply || "Request failed." });
      return;
    }

    if (data.session) {
      state.activeSessionId = data.session.id;
      state.activeSession = data.session;
      const idx = state.sessions.findIndex(item => item.id === data.session.id);
      if (idx >= 0) {
        state.sessions[idx] = data.session;
      } else {
        state.sessions.unshift(data.session);
      }
      renderSessions();
      renderMessages(data.session.messages || []);
    } else {
      appendMessage({ role: "assistant", content: data.reply || "No response generated.", tokens: data.usage });
    }
  } catch (err) {
    loadingEl.remove();
    appendMessage({ role: "assistant", content: `Connection error: ${err.message}` });
  }
}

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage();
});

clearBtn.addEventListener("click", () => {
  clearSession();
});

newSessionBtn.addEventListener("click", () => {
  createSession();
});

renameSessionBtn.addEventListener("click", () => {
  renameSession();
});

exportSessionBtn.addEventListener("click", () => {
  exportSession();
});

exportAllBtn.addEventListener("click", () => {
  exportAllSessions();
});

importSessionBtn.addEventListener("click", () => {
  importFileInput.value = "";
  importFileInput.click();
});

importFileInput.addEventListener("change", () => {
  if (importFileInput.files.length) {
    importSessions(importFileInput.files[0]);
  }
});

function updateProviderFields() {
  const provider = providerSelect.value;
  if (provider === "openai") {
    openaiBaseUrlInput.parentElement.style.display = "block";
  } else {
    openaiBaseUrlInput.parentElement.style.display = "none";
  }
}

window.addEventListener("DOMContentLoaded", () => {
  loadSettings();
  syncEmptyState();

  const isDark = localStorage.getItem("darkMode") === "true";
  setTheme(isDark);

  const defaultBg = document.querySelector('input[name="bg"][value="default"]');
  if (defaultBg && defaultBg.checked) {
    bgUpload.style.display = "none";
  }

  updateProviderFields();
  loadSessions();
});
