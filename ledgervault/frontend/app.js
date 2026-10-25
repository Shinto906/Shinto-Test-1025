const API = (window.LEDGER_API || "http://localhost:8000");
let token = localStorage.getItem("token") || "";
let currentDoc = null;

function authHeaders() {
  return { "Content-Type": "application/json", Authorization: "Bearer " + token };
}

async function login() {
  const email = document.getElementById("email").value;
  const password = document.getElementById("password").value;
  const res = await fetch(API + "/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    document.getElementById("login-err").textContent = "Login failed";
    return;
  }
  const data = await res.json();
  token = data.access_token;
  localStorage.setItem("token", token);
  showApp();
}

async function showApp() {
  document.getElementById("login-view").style.display = "none";
  document.getElementById("app-view").style.display = "block";
  const me = await (await fetch(API + "/api/profile/me", { headers: authHeaders() })).json();
  document.getElementById("whoami").textContent = me.email + " (" + me.role + ")";
  loadDocs();
}

async function loadDocs() {
  const docs = await (await fetch(API + "/api/documents", { headers: authHeaders() })).json();
  const ul = document.getElementById("docs");
  ul.innerHTML = "";
  docs.forEach((d) => {
    const li = document.createElement("li");
    li.textContent = d.title;
    li.onclick = () => openDoc(d.id);
    ul.appendChild(li);
  });
}

async function openDoc(id) {
  currentDoc = id;
  const d = await (await fetch(API + "/api/documents/" + id, { headers: authHeaders() })).json();
  document.getElementById("doc-detail").textContent = d.title + " [" + d.visibility + "]";
  loadComments();
}

async function loadComments() {
  if (!currentDoc) return;
  const comments = await (
    await fetch(API + "/api/documents/" + currentDoc + "/comments", { headers: authHeaders() })
  ).json();
  const box = document.getElementById("comments");
  box.innerHTML = "";
  comments.forEach((c) => {
    const div = document.createElement("div");
    div.className = "comment";
    div.innerHTML = c.body;
    box.appendChild(div);
  });
}

async function addComment() {
  const body = document.getElementById("comment-body").value;
  await fetch(API + "/api/documents/" + currentDoc + "/comments", {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({ body }),
  });
  document.getElementById("comment-body").value = "";
  loadComments();
}

if (token) showApp();
