// src/components/PlanList.tsx
import React, { useEffect, useState } from "react";
import type { TrainingPlan } from "../api/models/TrainingPlan";
import { parseISO } from "date-fns";

type ClientTrainingPlan = Omit<TrainingPlan, "date" | "type"> & {
  date: Date;
  type: "planned" | "strava";
  originalType?: string | null;
};

const API = import.meta.env.VITE_API_URL;
if (!API) throw new Error("VITE_API_URL is not set");

export default function PlanList() {
  const [plans, setPlans] = useState<ClientTrainingPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    (async () => {
      try {
        setLoading(true);
        setErr(null);

        const res = await fetch(`${API}/plans`, {
          credentials: "include", // <-- send session cookie
        });

        if (res.status === 401) {
          // Not logged in (frontend should usually be gated, but play nice)
          if (!alive) return;
          setErr("Not authenticated");
          setPlans([]);
          return;
        }

        if (!res.ok) {
          const txt = await res.text();
          throw new Error(txt || "Failed to load plans");
        }

        const raw = (await res.json()) as TrainingPlan[];

        const parsed: ClientTrainingPlan[] = raw.map((p) => ({
          ...p,
          date: parseISO(String(p.date)), // backend returns ISO string
          type: "planned",                // normalize for UI
          originalType: (p as any).type ?? null,
        }));

        if (!alive) return;
        setPlans(parsed);
      } catch (e: any) {
        if (!alive) return;
        setErr(e?.message || "Failed to load plans");
      } finally {
        if (alive) setLoading(false);
      }
    })();

    return () => {
      alive = false;
    };
  }, []);

  if (loading) return <div className="p-3 text-sm text-gray-600">Loading plans…</div>;
  if (err) return <div className="p-3 text-sm text-red-600">{err}</div>;

  return (
    <ul className="p-3 space-y-2">
      {plans.map((p) => (
        <li key={p.id} className="text-sm">
          <strong>{p.originalType ?? "Planned"}</strong> on{" "}
          {p.date.toLocaleDateString()} — {p.description || ""}
        </li>
      ))}
      {plans.length === 0 && (
        <li className="text-sm text-gray-500">No plans yet.</li>
      )}
    </ul>
  );
}
