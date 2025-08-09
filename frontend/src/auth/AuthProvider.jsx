import { createContext, useContext, useEffect, useState } from "react";
import * as api from "../api/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true); // block UI until we know

  useEffect(() => {
    let mounted = true;
    api.me().then(u => { if (mounted) setUser(u); }).finally(() => {
      if (mounted) setLoading(false);
    });
    return () => { mounted = false; };
  }, []);

  async function signIn(email, password) {
    const u = await api.login(email, password);
    setUser(u);
    return u;
  }

  async function signUp(email, password, name) {
    const u = await api.register(email, password, name);
    setUser(u);
    return u;
  }

  async function signOut() {
    await api.logout();
    setUser(null);
  }

  const value = { user, loading, signIn, signUp, signOut };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
