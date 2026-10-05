const mode = { login: true };

function setMode(which) {
  mode.login = which === "login";
  document.getElementById("tab-login").classList.toggle("active", mode.login);
  document.getElementById("tab-register").classList.toggle("active", !mode.login);
  document.getElementById("submit").textContent = mode.login ? "登录" : "注册";
  document.getElementById("err").textContent = "";
}
document.getElementById("tab-login").addEventListener("click", () => setMode("login"));
document.getElementById("tab-register").addEventListener("click", () => setMode("register"));

document.getElementById("submit").addEventListener("click", async () => {
  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value;
  const err = document.getElementById("err");
  if (!username || !password) { err.textContent = "请输入用户名和密码"; return; }

  const url = mode.login ? "/api/auth/login" : "/api/auth/register";
  try {
    const resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    const data = await resp.json();
    if (!resp.ok) { err.textContent = data.detail || "操作失败"; return; }
    const store = safeStore();
    store.setItem("token", data.token);
    store.setItem("user", JSON.stringify(data.user));
    location.href = data.user.is_admin ? "/admin" : "/chat";
  } catch (e) {
    err.textContent = "网络错误，请重试";
  }
});

function safeStore() {
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
}
