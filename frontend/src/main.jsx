import './index.css'
import './App.css'
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import { AuthProvider } from "./auth/AuthProvider.jsx";
import RequireAuth from "./auth/RequireAuth.jsx";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <RequireAuth>
        <App />
      </RequireAuth>
    </AuthProvider>
  </React.StrictMode>
);
