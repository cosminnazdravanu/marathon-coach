// src/api/types.ts
import type { components } from "./models";

// 1) The raw API shape
export type APITrainingPlan = components["schemas"]["TrainingPlan"];

// 2) A UI‐friendly version with `date: Date`
export type UITrainingPlan = Omit<APITrainingPlan, "date"> & {
  date: Date;
};
