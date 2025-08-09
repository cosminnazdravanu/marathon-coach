import { useState, useEffect, useMemo, useRef } from "react";
import { login, register, me, logout } from "../api/auth";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000"; // ← make sure this is localhost:8000

function getNextPath() {
  const raw = new URLSearchParams(window.location.search).get("next") || "/";
  try {
    const u = new URL(raw, window.location.origin);
    return u.pathname + u.search + u.hash;
  } catch {
    return "/";
  }
}

export default function LoginForm() {
  const [user, setUser] = useState(null);
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [err, setErr] = useState("");

  const nextPath = useMemo(getNextPath, []);
  const redirected = useRef(false);

  useEffect(() => {
    me()
      .then(u => {
        setUser(u);
        // If already logged in when landing here, bounce once to backend (even if next === "/")
        if (u && !redirected.current) {
          redirected.current = true;
          window.location.assign(`${API}${nextPath}`);
        }
      })
      .catch(() => {});
  }, [nextPath]);

  async function onSubmit(e) {
    e.preventDefault();
    setErr("");
    try {
      const u = mode === "login"
        ? await login(email, password)
        : await register(email, password, name || null);
      setUser(u);
      // Always go to backend next ("/" included)
      if (!redirected.current) {
        redirected.current = true;
        window.location.assign(`${API}${nextPath}`);
      }
    } catch (e) {
      setErr("Authentication failed");
      console.error(e);
    }
  }

  async function onLogout() {
    await logout();
    setUser(null);
    redirected.current = false;
  }

  if (user) {
    return (
      <div className="p-4 border rounded-lg bg-white shadow space-y-3">
        <p>Signed in as <b>{user.email}</b>{user.name ? ` (${user.name})` : ""}</p>
        <div className="flex gap-2">
          <button className="px-3 py-1 border rounded" onClick={() => {
            if (!redirected.current) {
              redirected.current = true;
              window.location.assign(`${API}${nextPath}`);
            }
          }}>
            Continue
          </button>
          <button className="px-3 py-1 border rounded" onClick={onLogout}>Logout</button>
        </div>
      </div>
    );
  }

  return (
    <form onSubmit={onSubmit} className="p-4 border rounded-lg bg-white shadow max-w-sm">
      <div className="flex gap-2 mb-3">
        <button type="button" className={`px-3 py-1 border rounded ${mode==='login'?'font-bold':''}`} onClick={() => setMode("login")}>Login</button>
        <button type="button" className={`px-3 py-1 border rounded ${mode==='register'?'font-bold':''}`} onClick={() => setMode("register")}>Register</button>
      </div>
      {mode === "register" && (
        <div className="mb-2">
          <label className="block text-sm mb-1">Name</label>
          <input className="w-full border rounded px-2 py-1" value={name} onChange={e=>setName(e.target.value)} />
        </div>
      )}
      <div className="mb-2">
        <label className="block text-sm mb-1">Email</label>
        <input required type="email" className="w-full border rounded px-2 py-1" value={email} onChange={e=>setEmail(e.target.value)} />
      </div>
      <div className="mb-3">
        <label className="block text-sm mb-1">Password</label>
        <input required type="password" className="w-full border rounded px-2 py-1" value={password} onChange={e=>setPassword(e.target.value)} />
      </div>
      {err && <p className="text-red-600 text-sm mb-2">{err}</p>}
      <button className="px-3 py-1 border rounded w-full" type="submit">
        {mode === "login" ? "Login" : "Create account"}
      </button>
    </form>
  );
}
