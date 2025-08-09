// src/auth/RequireAuth.jsx
import { useAuth } from "./AuthProvider.jsx";
import LoginForm from "../components/LoginForm.jsx";

export default function RequireAuth({ children }) {
  const { user, loading } = useAuth();
  if (loading) {
    console.debug("[RequireAuth] loading…");
    return <div className="p-4">Loading…</div>;
  }
  if (!user) {
    console.debug("[RequireAuth] guest → showing LoginForm");
    return <LoginForm />;
  }
  console.debug("[RequireAuth] authenticated → render app");
  return children;
}