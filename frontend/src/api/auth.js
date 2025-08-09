const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

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
  // assumes you already have: const API = import.meta.env.VITE_API_URL || "http://localhost:8000";
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort("timeout"), 4500);

  try {
    const r = await fetch(`${API}/auth/me`, {
      credentials: "include",
      headers: { Accept: "application/json" },
      signal: ctrl.signal,
    });

    if (!r.ok) return null;

    // Prefer JSON if declared; otherwise try to parse text safely.
    const ct = r.headers.get("content-type") || "";
    if (ct.includes("application/json")) {
      return await r.json();
    }

    const text = await r.text();
    if (!text) return null;
    try { return JSON.parse(text); } catch { return null; }
  } catch {
    return null;
  } finally {
    clearTimeout(timeout);
  }
}

export async function logout() {
  const token = await csrf();
  await fetch(`${API}/auth/logout`, {
    method: "POST",
    credentials: "include",
    headers: { "X-CSRF-Token": token },
  });
}
