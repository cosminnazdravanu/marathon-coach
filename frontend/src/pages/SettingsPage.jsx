import React, { useEffect, useState } from "react";
import { Tab } from "@headlessui/react";
import { useAuth } from "../auth/AuthProvider.jsx";
import { updateMe } from "../api/auth.js";

function classNames(...classes) {
  return classes.filter(Boolean).join(" ");
}

function UserSettingsTab() {
  const { user, loading, refresh } = useAuth();
  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [saving, setSaving] = useState(false);
  const [msg, setMsg] = useState("");

  useEffect(() => {
    if (!loading) {
      setName(user?.name || "");
      setEmail(user?.email || "");
    }
  }, [user, loading]);

  async function onSubmit(e) {
    e.preventDefault();
    setMsg("");
    setSaving(true);
    try {
      const updated = await updateMe({ name, email });
      await refresh(); // Refresh user data from /auth/me
      setMsg("Saved!");
      // Note: AuthProvider doesn't auto-refresh /auth/me here.
      // If you want the top-right avatar initials to reflect new name immediately,
      // you can force a soft reload or add a setUser(...) in AuthContext via a new method.
      setTimeout(() => setMsg(""), 2500);
    } catch (err) {
      setMsg(typeof err?.message === "string" ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={onSubmit} className="max-w-xl space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700">Name</label>
        <input
          type="text"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Your name"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Email</label>
        <input
          type="email"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="you@example.com"
        />
      </div>

      <div className="flex items-center gap-3">
        <button
          type="submit"
          disabled={saving}
          className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
        >
          {saving ? "Saving…" : "Save changes"}
        </button>
        {msg && <span className="text-sm text-gray-600">{msg}</span>}
      </div>
    </form>
  );
}

function AccountTab() {
  return (
    <div className="text-gray-600 text-sm">
      <p>Plan, billing, password and security (coming soon).</p>
    </div>
  );
}

const API = import.meta.env.VITE_API_URL;

function PartnersTab() {
  return (
    <div className="grid sm:grid-cols-2 gap-4 max-w-3xl">
      {/* Strava card */}
      <div className="rounded-2xl border bg-white p-4 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold">Strava</h3>
            <p className="text-sm text-gray-500">Connect to import activities</p>
          </div>
          <img
            alt="Strava"
            src="https://upload.wikimedia.org/wikipedia/commons/9/9c/Strava_Logo.svg"
            className="h-6"
          />
        </div>
        <div className="mt-3 flex gap-2">
          <a
            href={`${API}/connect_strava`}
            className="px-3 py-1.5 rounded-lg bg-orange-500 text-white hover:bg-orange-600"
          >
            Connect
          </a>
          <button
            onClick={async () => {
              // POST /disconnect_strava with CSRF would be ideal—hook it later when you want.
              // For now just open the backend route in a new tab if needed.
              window.open(`${API}/disconnect_strava`, "_self");
            }}
            className="px-3 py-1.5 rounded-lg border hover:bg-gray-50"
          >
            Disconnect
          </button>
        </div>
      </div>

      {/* Garmin placeholder */}
      <div className="rounded-2xl border bg-white p-4 shadow-sm opacity-60">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-semibold">Garmin Connect</h3>
            <p className="text-sm text-gray-500">Coming soon</p>
          </div>
          <div className="h-6 w-16 bg-gray-200 rounded" />
        </div>
      </div>
    </div>
  );
}

export default function SettingsPage() {
  const tabs = ["User Settings", "Your Account", "Partner Integrations"];

  return (
    <div className="p-4">
      <div className="mb-4">
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-gray-500">
          Manage your profile, account, and integrations.
        </p>
      </div>

      <Tab.Group>
        <Tab.List className="flex space-x-2 rounded-xl bg-gray-100 p-1 max-w-xl">
          {tabs.map((t) => (
            <Tab
              key={t}
              className={({ selected }) =>
                classNames(
                  "w-full rounded-lg py-2.5 text-sm font-medium focus:outline-none",
                  selected
                    ? "bg-white shadow text-gray-900"
                    : "text-gray-600 hover:bg-white/70"
                )
              }
            >
              {t}
            </Tab>
          ))}
        </Tab.List>
        <Tab.Panels className="mt-4">
          <Tab.Panel className="rounded-xl bg-white p-4 shadow">
            <UserSettingsTab />
          </Tab.Panel>
          <Tab.Panel className="rounded-xl bg-white p-4 shadow">
            <AccountTab />
          </Tab.Panel>
          <Tab.Panel className="rounded-xl bg-white p-4 shadow">
            <PartnersTab />
          </Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
}
