// src/components/PlanList.tsx
import React, { useEffect, useState } from "react";
import { TrainingPlansService } from "../api/services/TrainingPlansService";
import type { TrainingPlan } from "../api/models/TrainingPlan";
import { parseISO } from "date-fns";

// extend so TS knows date is a Date once we parse it
interface ClientTrainingPlan extends Omit<TrainingPlan, "date"> {
  date: Date;
}

const raw = await TrainingPlansService.getAllPlansPlansGet();

export function PlanList() {
  const [plans, setPlans] = useState<ClientTrainingPlan[]>([]);

  useEffect(() => {
    (async () => {
      // ⚓ call the correct generated method
      const raw = await TrainingPlansService.getAllPlansPlansGet();

      // parse and cast to ClientTrainingPlan
      const parsed: ClientTrainingPlan[] = raw.map((p) => ({
        ...p,
        date: parseISO(p.date),
      }));

      setPlans(parsed);
    })();
  }, []);

  return (
    <ul>
      {plans.map((p) => (
        <li key={p.id}>
          <strong>{p.type}</strong> on {p.date.toLocaleDateString()} —{" "}
          {p.description}
        </li>
      ))}
    </ul>
  );
}

