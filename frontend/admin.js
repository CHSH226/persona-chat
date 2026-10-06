const store = (() => {
  try { const t = "__t__"; localStorage.setItem(t, "1"); localStorage.removeItem(t); return localStorage; }
  catch (e) { let m = {}; return { getItem: (k) => m[k] ?? null, setItem: (k, v) => { m[k] = String(v); }, removeItem: (k) => { delete m[k]; } }; }
})();

const token = store.getItem("token");
const me = JSON.parse(store.getItem("user") || "null");
if (!token || !me || !me.is_admin) location.href = "/";

const H = (method = "GET", body) => ({
  method,
  headers: { "Content-Type": "application/json", Authorization: "Bearer " + token },
  body: body ? JSON.stringify(body) : undefined,
});

async function api(url, method, body) {
  const resp = await fetch(url, H(method, body));
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) throw new Error(data.detail || "请求失败");
  return data;
}

// 顶部 tab
document.querySelectorAll(".admin-tabs button").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".admin-tabs button").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.add("hidden"));
    btn.classList.add("active");
    document.getElementById("tab-" + btn.dataset.tab).classList.remove("hidden");
    loadData(btn.dataset.tab);
  });
});

function loadData(tab) {
  if (tab === "codes") loadCodes();
  else if (tab === "users") loadUsers();
  else if (tab === "announce") loadAnn();
  else if (tab === "personas") loadPersonas();
}

document.getElementById("logoutBtn").addEventListener("click", () => {
  store.removeItem("token"); store.removeItem("user"); location.href = "/";
});

// ===== 兑换码 =====
async function loadCodes() {
  const d = document.getElementById("codeList");
  try {
    const list = await api("/api/admin/codes");
    if (!list.length) { d.innerHTML = '<div class="card">暂无兑换码</div>'; return; }
    d.innerHTML = `<table><tr><th>兑换码</th><th>积分</th><th>已用/上限</th><th>状态</th><th>操作</th></tr>` +
      list.map(c =>
        `<tr><td>${c.code}</td><td>${c.credit_amount}</td><td>${c.used_count}/${c.max_uses === 0 ? "∞" : c.max_uses}</td>
         <td>${c.is_active ? "启用" : "停用"}</td>
         <td class="actions"><button class="${c.is_active ? 'btn-red' : 'btn-green'}" onclick="toggleCode(${c.id})">${c.is_active ? "停用" : "启用"}</button></td></tr>`)
      .join("") + `</table>`;
  } catch (e) { d.innerHTML = `<div class="card">${e.message}</div>`; }
}
async function toggleCode(id) {
  try { await api("/api/admin/codes/" + id, "PATCH"); loadCodes(); }
  catch (e) { alert(e.message); }
}
document.getElementById("codeCreate").addEventListener("click", async () => {
  const err = document.getElementById("codeErr");
  const code = document.getElementById("codeStr").value.trim();
  const credit = parseInt(document.getElementById("codeCredit").value) || 0;
  const maxUses = parseInt(document.getElementById("codeMaxUses").value) || 0;
  if (!code) { err.textContent = "请输入兑换码"; return; }
  try {
    await api("/api/admin/codes", "POST", { code, credit_amount: credit, max_uses: maxUses });
    err.textContent = "";
    document.getElementById("codeStr").value = "";
    loadCodes();
  } catch (e) { err.textContent = e.message; }
});

// ===== 用户 =====
async function loadUsers() {
  const d = document.getElementById("userList");
  try {
    const list = await api("/api/admin/users");
    if (!list.length) { d.innerHTML = '<div class="card">暂无用户</div>'; return; }
    d.innerHTML = `<table><tr><th>ID</th><th>用户名</th><th>积分</th><th>管理员</th><th>状态</th><th>操作</th></tr>` +
      list.map(u =>
        `<tr><td>${u.id}</td><td>${u.username}</td><td>${u.credits}</td>
         <td>${u.is_admin ? "是" : "否"}</td><td>${u.is_active ? "正常" : "禁用"}</td>
         <td class="actions">
           <button class="btn-gray" onclick="showChats(${u.id},'${u.username}')">聊天记录</button>
           <button class="btn-gray" onclick="setCredits(${u.id},'${u.username}')">改积分</button>
           <button class="btn-gray" onclick="toggleUser(${u.id})">${u.is_active ? "禁用" : "启用"}</button>
           ${u.is_admin ? "" : `<button class="btn-red" onclick="delUser(${u.id},'${u.username}')">删除</button>`}
         </td></tr>`)
      .join("") + `</table>`;
  } catch (e) { d.innerHTML = `<div class="card">${e.message}</div>`; }
}
async function setCredits(id, name) {
  const mode = prompt("给用户 " + name + " 加积分 [输入：+100 加100分  /  s:100 设为100  /  -50 扣50分]");
  if (mode === null) return;
  const input = mode.trim();
  if (input === "") return;
  let payload = {};
  if (/^s:/i.test(input)) {
    const val = parseInt(input.slice(2));
    if (isNaN(val)) return;
    payload = { credits: Math.max(0, val), credits_action: "set" };
  } else if (/^[+-]?.?\d+$/.test(input)) {
    const val = parseInt(input);
    payload = { credits: val, credits_action: "add" };
  } else {
    alert("格式：+100 加分 / -50 扣分 / s:100 设为该值");
    return;
  }
  try { const r = await api("/api/admin/users/" + id, "PATCH", payload); alert("当前积分: " + r.credits); loadUsers(); }
  catch (e) { alert(e.message); }
}

async function toggleUser(id) {
  try {
    const u = await api("/api/admin/users/" + id);
    await api("/api/admin/users/" + id, "PATCH", { is_active: !u.is_active });
    loadUsers();
  } catch (e) { alert(e.message); }
}

async function delUser(id, name) {
  if (!confirm("确认删除用户 " + name + "？将同时删除其聊天记录，且不可恢复！")) return;
  try { await api("/api/admin/users/" + id, "DELETE"); toast("已删除用户 " + name); loadUsers(); }
  catch (e) { alert(e.message); }
}

async function exportAllChats() {
  try {
    const data = await api("/api/admin/chats/all");
    if (!data.length) { alert("暂无聊天记录"); return; }
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "chats_export_" + new Date().toISOString().slice(0, 10) + ".json";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast("已导出 " + data.length + " 条聊天记录");
  } catch (e) { alert(e.message); }
}
async function showChats(id, name) {
  try {
    const list = await api("/api/admin/users/" + id + "/chats");
    const d = document.getElementById("userList");
    d.innerHTML = `<button class="btn-gray" onclick="loadUsers()">返回列表</button><h2 style="margin-top:14px;">${name} 的聊天记录</h2>`;
    if (!list.length) { d.innerHTML += '<div class="card">暂无记录</div>'; return; }
    d.innerHTML += list.map(m =>
      `<div class="chatlog"><span class="who">${m.role === "user" ? "用户" : "AI"}:</span><div class="content">${esc(m.content)}</div><div style="color:#aaa;font-size:12px;">${m.created_at||""}</div></div>`)
      .join("");
  } catch (e) { alert(e.message); }
}

// ===== 公告 =====
async function loadAnn() {
  const d = document.getElementById("annList");
  try {
    const list = await api("/api/admin/announcements");
    if (!list.length) { d.innerHTML = '<div class="card">暂无公告</div>'; return; }
    d.innerHTML = list.map(a =>
      `<div class="card"><div style="margin-bottom:6px;">${esc(a.content)}</div>
       <span style="color:${a.is_active ? "green" : "red"};font-size:12px;">${a.is_active ? "显示中" : "已下线"} ${a.created_at||""}</span>
       <div class="actions" style="margin-top:8px;"><button class="${a.is_active ? 'btn-red' : 'btn-green'}" onclick="toggleAnn(${a.id})">${a.is_active ? "下线" : "显示"}</button></div></div>`)
      .join("");
  } catch (e) { d.innerHTML = `<div class="card">${e.message}</div>`; }
}
async function toggleAnn(id) {
  try { await api("/api/admin/announcements/" + id, "PATCH"); loadAnn(); }
  catch (e) { alert(e.message); }
}
document.getElementById("annCreate").addEventListener("click", async () => {
  const err = document.getElementById("annErr");
  const content = document.getElementById("annContent").value.trim();
  if (!content) { err.textContent = "请输入公告内容"; return; }
  try {
    await api("/api/admin/announcements", "POST", { content });
    err.textContent = "";
    document.getElementById("annContent").value = "";
    loadAnn();
  } catch (e) { err.textContent = e.message; }
});

// ===== 人格层 =====
async function loadPersonas() {
  const d = document.getElementById("pList");
  try {
    const list = await api("/api/admin/personas");
    if (!list.length) { d.innerHTML = '<div class="card">暂无人格层</div>'; return; }
    d.innerHTML = list.map(l =>
      `<div class="card"><b>${esc(l.name)}</b> (${l.type}, 权重${l.weight}, ${l.is_on_demand ? "按需" : "常驻"}, ${l.is_active ? "启用" : "停用"})
       <div style="color:#666;font-size:13px;margin:6px 0;white-space:pre-wrap;">${esc(l.content.slice(0, 200))}${l.content.length > 200 ? "..." : ""}</div>
       <div class="actions"><button class="btn-gray" onclick="editPersona(${l.id})">编辑</button>
       <button class="${l.is_active ? 'btn-gray' : 'btn-green'}" onclick="togglePersona(${l.id})">${l.is_active ? "停用" : "启用"}</button>
       <button class="btn-red" onclick="delPersona(${l.id})">删除</button></div></div>`)
      .join("");
  } catch (e) { d.innerHTML = `<div class="card">${e.message}</div>`; }
}
async function togglePersona(id) {
  try {
    const list = await api("/api/admin/personas");
    const l = list.find(x => x.id === id);
    await api("/api/admin/personas/" + id, "PATCH", { ...l, is_active: !l.is_active });
    loadPersonas();
  } catch (e) { alert(e.message); }
}
async function delPersona(id) {
  if (!confirm("确认删除该人格层？")) return;
  try { await api("/api/admin/personas/" + id, "DELETE"); loadPersonas(); }
  catch (e) { alert(e.message); }
}
async function editPersona(id) {
  const list = await api("/api/admin/personas");
  const l = list.find(x => x.id === id);
  document.getElementById("pName").value = l.name;
  document.getElementById("pType").value = l.type;
  document.getElementById("pWeight").value = l.weight;
  document.getElementById("pKeywords").value = l.keywords || "";
  document.getElementById("pContent").value = l.content;
  document.getElementById("pOnDemand").checked = l.is_on_demand;
  const btn = document.getElementById("pCreate");
  btn.textContent = "保存修改";
  btn.dataset.editId = l.id;
}
document.getElementById("pCreate").addEventListener("click", async () => {
  const err = document.getElementById("pErr");
  const body = {
    name: document.getElementById("pName").value.trim() || "未命名",
    type: document.getElementById("pType").value,
    weight: parseFloat(document.getElementById("pWeight").value) || 1,
    keywords: document.getElementById("pKeywords").value.trim() || null,
    content: document.getElementById("pContent").value,
    is_on_demand: document.getElementById("pOnDemand").checked,
  };
  if (!body.content) { err.textContent = "请输入内容"; return; }
  const btn = document.getElementById("pCreate");
  try {
    if (btn.dataset.editId) {
      await api("/api/admin/personas/" + btn.dataset.editId, "PATCH", body);
      delete btn.dataset.editId;
      btn.textContent = "新增人格层";
    } else {
      await api("/api/admin/personas", "POST", body);
    }
    err.textContent = "";
    document.getElementById("pName").value = ""; document.getElementById("pContent").value = "";
    document.getElementById("pKeywords").value = ""; document.getElementById("pOnDemand").checked = false;
    loadPersonas();
  } catch (e) { err.textContent = e.message; }
});

function esc(s) { return String(s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function toast(msg) { alert(msg); }

document.getElementById("who").textContent = me.username || "管理员";
document.getElementById("exportChatsBtn").addEventListener("click", exportAllChats);

loadCodes();
