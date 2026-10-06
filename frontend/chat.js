const store = (() => {
  try {
    const t = "__t__";
    localStorage.setItem(t, "1");
    localStorage.removeItem(t);
    return localStorage;
  } catch (e) {
    let m = {};
    return {
      getItem: (k) => m[k] ?? null,
      setItem: (k, v) => { m[k] = String(v); },
      removeItem: (k) => { delete m[k]; },
    };
  }
})();

const token = store.getItem("token");
let me = JSON.parse(store.getItem("user") || "null");
if (!token) location.href = "/";

const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("send");
let busy = false;

async function refreshMe() {
  try {
    const resp = await fetch("/api/auth/me", {
      headers: { Authorization: "Bearer " + token },
    });
    if (!resp.ok) { location.href = "/"; return; }
    me = await resp.json();
    store.setItem("user", JSON.stringify(me));
    document.getElementById("creditsPill").textContent = me.credits + " 积分";
  } catch (e) {}
}

async function loadAnnounce() {
  try {
    const resp = await fetch("/api/announcements/active");
    const list = await resp.json();
    const el = document.getElementById("announce");
    if (list && list.length) {
      el.textContent = list.map(a => a.content).join(" | ");
      el.style.display = "block";
    } else {
      el.style.display = "none";
    }
  } catch (e) {}
}

function addMessage(role, text) {
  const el = document.createElement("div");
  el.className = "msg " + role;
  el.textContent = text;
  messagesEl.appendChild(el);
  scrollBottom();
  return el;
}
function scrollBottom() { messagesEl.scrollTop = messagesEl.scrollHeight; }

sendBtn.addEventListener("click", send);
inputEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
});
document.getElementById("logoutBtn").addEventListener("click", () => {
  store.removeItem("token"); store.removeItem("user"); location.href = "/";
});

// 兑换码弹窗
const redeemMask = document.getElementById("redeemMask");
document.getElementById("redeemBtn").addEventListener("click", () => {
  document.getElementById("redeemInput").value = "";
  document.getElementById("redeemErr").textContent = "";
  redeemMask.classList.remove("hidden");
});
document.getElementById("redeemCancel").addEventListener("click", () => redeemMask.classList.add("hidden"));
document.getElementById("redeemOk").addEventListener("click", async () => {
  const code = document.getElementById("redeemInput").value.trim();
  const errEl = document.getElementById("redeemErr");
  if (!code) { errEl.textContent = "请输入兑换码"; return; }
  try {
    const resp = await fetch("/api/codes/redeem", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify({ code }),
    });
    const data = await resp.json();
    if (!resp.ok) { errEl.textContent = data.detail || "兑换失败"; return; }
    redeemMask.classList.add("hidden");
    toast("成功兑换 +" + data.added + " 积分");
    refreshMe();
  } catch (e) { errEl.textContent = "网络错误"; }
});

function toast(msg) {
  const el = document.createElement("div");
  el.className = "toast";
  el.textContent = msg;
  document.body.appendChild(el);
  setTimeout(() => el.remove(), 2200);
}

async function send() {
  const text = inputEl.value.trim();
  if (!text || busy) return;
  if (me.credits <= 0) {
    toast("积分不足，欢迎点右上角「兑换码」输入邀请码");
    return;
  }
  inputEl.value = "";
  addMessage("user", text);
  busy = true;
  sendBtn.disabled = true;

  const aiEl = addMessage("ai", "");
  const typing = addMessage("ai", "正在输入...");
  typing.classList.add("typing");

  try {
    const resp = await fetch("/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
      body: JSON.stringify({ message: text }),
    });
    if (resp.status === 402) {
      typing.remove();
      aiEl.textContent = "积分不足，请先兑换积分";
      toast("积分不足，请兑换");
      return;
    }
    if (!resp.ok) {
      typing.remove();
      aiEl.textContent = "出错了：" + (await resp.text());
      return;
    }
    typing.remove();
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
    refreshMe(); // 刷新扣积分后的余额
  } catch (e) {
    typing.remove();
    aiEl.textContent = "网络错误，请重试";
  } finally {
    busy = false;
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

refreshMe();
loadAnnounce();
