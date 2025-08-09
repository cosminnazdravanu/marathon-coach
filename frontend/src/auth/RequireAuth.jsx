import { useAuth } from "./AuthProvider";
import LoginForm from "../components/LoginForm"; // your earlier component

export default function RequireAuth({ children }) {
  const { user, loading } = useAuth();

  if (loading) {
    return <div style={{ padding: 24 }}>Loading…</div>;
  }
  if (!user) {
    // no app for you until signed in
    return (
      <div className="min-h-screen grid place-items-center bg-gray-50">
        <LoginForm />
      </div>
    );
  }
  return children;
}
