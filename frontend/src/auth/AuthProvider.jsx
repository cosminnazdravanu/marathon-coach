// frontend/src/auth/AuthProvider.jsx
import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { me as apiMe, login as apiLogin, register as apiRegister, logout as apiLogout } from "../api/auth.js";

const AuthContext = createContext(null);
export const useAuth = () => useContext(AuthContext);

export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let done = false;
    const safety = setTimeout(() => {
      if (!done) {
        console.warn("[AuthProvider] /auth/me timed out; assuming guest");
        setUser(null);
        setLoading(false);
      }
    }, 5000);

    (async () => {
      try {
        console.log("[AuthProvider] fetching /auth/me …");
        const u = await apiMe();
        console.log("[AuthProvider] /auth/me result:", u);
        setUser(u);
      } catch (e) {
        console.error("[AuthProvider] /auth/me error:", e);
        setUser(null);
      } finally {
        done = true;
        clearTimeout(safety);
        setLoading(false);
      }
    })();

    return () => clearTimeout(safety);
  }, []);

  const value = useMemo(() => ({
    user,
    loading,
    async login(email, password) {
      const u = await apiLogin(email, password);
      setUser(u);
      return u;
    },
    async register(email, password, name) {
      const u = await apiRegister(email, password, name);
      setUser(u);
      return u;
    },
    async logout() {
      await apiLogout();
      setUser(null);
    },
  }), [user, loading]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
