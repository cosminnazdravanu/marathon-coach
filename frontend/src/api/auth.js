const API = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function csrf() {
  const r = await fetch(`${API}/auth/csrf`, { credentials: "include" });
  return (await r.json()).csrf;
}

export async function login(email, password) {
  const token = await csrf();
  const r = await fetch(`${API}/auth/login`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
    body: JSON.stringify({ email, password }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function register(email, password, name) {
  const token = await csrf();
  const r = await fetch(`${API}/auth/register`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": token },
    body: JSON.stringify({ email, password, name }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function me() {
  const r = await fetch(`${API}/auth/me`, { credentials: "include" });
  if (!r.ok) return null;
  return r.json();
}

export async function logout() {
  const token = await csrf();
  await fetch(`${API}/auth/logout`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": token },
  });
}
