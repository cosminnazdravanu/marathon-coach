// src/components/LoginForm.jsx
import { useState, useEffect, useRef } from "react";
import { useAuth } from "../auth/AuthProvider.jsx";

// keep API because you referenced it; prefer localhost for cookie consistency
const API = import.meta.env.VITE_API_URL;
if (!API) throw new Error("VITE_API_URL is not set");

// New helper: decide *where* to go after auth
function buildRedirectUrl() {
  const params = new URLSearchParams(window.location.search);
  const hasNext = params.has("next");     // <— key change
  const raw = hasNext ? params.get("next") : null;
  // No next param at all → stay on the current (frontend) origin
  if (!hasNext || !raw) {
    return window.location.origin + "/";
  }

  // 1) Absolute URL? (http/https…)
  if (/^[a-zA-Z][a-zA-Z0-9+.-]*:/.test(raw)) {
    return raw; // trust explicit absolute targets
  }
  // 2) Backend path? (starts with /) → go to backend
  if (raw.startsWith("/")) {
    return `${API}${raw}`;
  }
  // 3) Fallback: relative to current (frontend) origin
  try {
    const u = new URL(raw, window.location.origin);
    return u.href;
  } catch {
    return window.location.origin + "/";
  }
}

export default function LoginForm() {
  const { user, login: authLogin, register: authRegister, logout } = useAuth(); //new
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [err, setErr] = useState("");

  const redirected = useRef(false);

  // Redirect whenever the *context* user becomes available (after login or a refresh)
  useEffect(() => {
    if (user && !redirected.current) {
      redirected.current = true;
      window.location.assign(buildRedirectUrl());
    }
  }, [user]);

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    try {
    if (mode === "login") await authLogin(email, password);
    else await authRegister(email, password, name);
    if (!redirected.current) {
      redirected.current = true;
      window.location.assign(buildRedirectUrl());
    }
    } catch (e) {
      setErr(e?.message || "Authentication failed");
    }
  }

  async function onLogout() {
    await logout();
    redirected.current = false;
  }

  if (user) {
    return (
      <div className="p-4 border rounded-lg bg-white shadow space-y-3">
        <p>
          Signed in as <b>{user.email}</b>
          {user.name ? ` (${user.name})` : ""}
        </p>
        <div className="flex gap-2">
          <button
            className="px-3 py-1 border rounded"
            onClick={() => {
              if (!redirected.current) {
                redirected.current = true;
                window.location.assign(buildRedirectUrl());
              }
            }}
          >
            Continue
          </button>
          <button className="px-3 py-1 border rounded" onClick={onLogout}>
            Logout
          </button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="p-4 border rounded-lg bg-white shadow max-w-sm">
      <div className="flex gap-2 mb-3">
        <button
          type="button"
          className={`px-3 py-1 border rounded ${mode === "login" ? "font-bold" : ""}`}
          onClick={() => setMode("login")}
        >
          Login
        </button>
        <button
          type="button"
          className={`px-3 py-1 border rounded ${mode === "register" ? "font-bold" : ""}`}
          onClick={() => setMode("register")}
        >
          Register
        </button>
      </div>

      {mode === "register" && (
        <div className="mb-2">
          <label className="block text-sm mb-1">Name</label>
          <input className="w-full border rounded px-2 py-1" value={name} onChange={e => setName(e.target.value)} />
        </div>
      )}

      <div className="mb-2">
        <label className="block text-sm mb-1">Email</label>
        <input required type="email" className="w-full border rounded px-2 py-1" value={email} onChange={e => setEmail(e.target.value)} />
      </div>

      <div className="mb-3">
        <label className="block text-sm mb-1">Password</label>
        <input required type="password" className="w-full border rounded px-2 py-1" value={password} onChange={e => setPassword(e.target.value)} />
      </div>

      {err && <p className="text-red-600 text-sm mb-2">{err}</p>}

      <button className="px-3 py-1 border rounded w-full" type="submit">
        {mode === "login" ? "Login" : "Create account"}
      </button>
    </form>
  );
}
