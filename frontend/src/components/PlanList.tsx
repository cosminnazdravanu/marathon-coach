// src/components/PlanList.tsx
import React, { useEffect, useState } from "react";
import { TrainingPlansService } from "../api/services/TrainingPlansService";
import type { TrainingPlan } from "../api/models/TrainingPlan";
import { parseISO } from "date-fns";

type ClientTrainingPlan =
  Omit<TrainingPlan, "date" | "type"> & {
    date: Date;
    type: "planned" | "strava";
    originalType?: string | null;
  };

export default function PlanList() {
  const [plans, setPlans] = useState<ClientTrainingPlan[]>([]);

  useEffect(() => {
    (async () => {
      const raw = await TrainingPlansService.getAllPlansPlansGet();

      const parsed: ClientTrainingPlan[] = raw.map((p) => ({
        ...p,
        // backend returns ISO date string -> convert to Date for UI
        date: parseISO(String(p.date)),
        // normalize so your UI treats these as “planned”
        type: "planned",
        originalType: p.type ?? null,
      }));

      setPlans(parsed);
    })();
  }, []);

  return (
    <ul>
      {plans.map((p) => (
        <li key={p.id}>
          <strong>{p.originalType ?? "Planned"}</strong> on{" "}
          {p.date.toLocaleDateString()} — {p.description}
        </li>
      ))}
    </ul>
  );
}
