import type { components } from "./schema";
export type Assumptions = components["schemas"]["Assumptions-Output"];
export type Evaluation = components["schemas"]["Evaluation"];
export type Comparison = components["schemas"]["Comparison"];
export type Scenario = components["schemas"]["ScenarioRead"];
export type Slot = "baseline" | "alternative";
export type Draft = {
  name: string;
  description: string;
  assumptions: Assumptions;
  id?: string;
  dirty: boolean;
};

export type SimulationSettings = Required<
  components["schemas"]["SimulationSettings-Output"]
>;
export type SimulationResult = components["schemas"]["SimulationResult"];
export type SensitivityResult = components["schemas"]["SensitivityResult"];
