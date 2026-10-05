const SESSION_KEY = localStorage.getItem("session_key") || ("s_" + Date.now().toString(36) + Math.random().toString(36).slice(2, 8));
localStorage.setItem("session_key", SESSION_KEY);

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
let busy = false;

function addMessage(role, text) {
  const el = document.createElement("div");
  el.className = "msg " + role;
  el.textContent = text;
  messagesEl.appendChild(el);
  scrollBottom();
  return el;
}

function scrollBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function setTyping(on) {
  let el = messagesEl.querySelector(".typing");
  if (on) {
    if (!el) {
      el = document.createElement("div");
      el.className = "msg ai typing";
      el.textContent = "正在输入...";
      messagesEl.appendChild(el);
      scrollBottom();
    }
    return el;
  }
  if (el) el.remove();
}

sendBtn.addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

async function send() {
  const text = inputEl.value.trim();
  if (!text || busy) return;

  inputEl.value = "";
  addMessage("user", text);
  busy = true;
  sendBtn.disabled = true;

  const aiEl = addMessage("ai", "");
  setTyping(true);

  try {
    const resp = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, session_key: SESSION_KEY }),
    });

    if (!resp.ok) {
      const err = await resp.text();
      aiEl.textContent = "出错了：" + err;
      return;
    }

    const reader = resp.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let full = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      full += decoder.decode(value, { stream: true });
      aiEl.textContent = full;
      scrollBottom();
    }
  } catch (err) {
    aiEl.textContent = "网络错误，请重试";
  } finally {
    setTyping(false);
    busy = false;
    sendBtn.disabled = false;
    inputEl.focus();
  }
}
