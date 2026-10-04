import type {
  Assumptions,
  Comparison,
  Scenario,
  Evaluation,
  SimulationSettings,
  SimulationResult,
  SensitivityResult,
} from "@/types/model";
import { fields } from "@/features/scenarios/fields";

async function request<T>(
  path: string,
  method = "GET",
  body?: unknown,
): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`/api/backend/${path}`, {
      method,
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: AbortSignal.timeout(
        path.startsWith("analytics/") ? 65000 : 20000,
      ),
    });
  } catch {
    throw new Error(
      "The connection was interrupted or timed out. Your edits are preserved; please retry.",
    );
  }
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => {
    throw new Error(
      "The service returned an unexpected response. Please retry.",
    );
  });
  if (!response.ok) {
    const detail = data.detail;
    const message = Array.isArray(detail)
      ? detail
          .map((item: { loc: string[]; msg: string }) => {
            const key = item.loc.at(-1);
            const field = fields.find((field) => field.key === key);
            const side = item.loc.includes("baseline")
              ? "Baseline · "
              : item.loc.includes("alternative")
                ? "Alternative · "
                : "";
            return `${side}${field?.label || "Scenario"}: ${item.msg}`;
          })
          .join(". ")
      : typeof detail === "string"
        ? detail
        : "The request could not be completed. Please retry.";
    throw new Error(message);
  }
  return data as T;
}
export const api = {
  riskDefaults: () => request<SimulationSettings>("analytics/defaults"),
  sensitivity: (assumptions: Assumptions) =>
    request<SensitivityResult>("analytics/sensitivity", "POST", {
      assumptions,
    }),
  simulate: (assumptions: Assumptions, settings: SimulationSettings) =>
    request<SimulationResult>("analytics/simulation", "POST", {
      assumptions,
      settings,
    }),
  evaluate: (assumptions: Assumptions) =>
    request<Evaluation>("evaluate", "POST", assumptions),
  remove: (id: string) => request<void>(`scenarios/${id}`, "DELETE"),
  defaults: () => request<Assumptions>("defaults"),
  compare: (baseline: Assumptions, alternative: Assumptions) =>
    request<Comparison>("compare", "POST", { baseline, alternative }),
  list: (offset = 0) =>
    request<Scenario[]>(`scenarios?limit=50&offset=${offset}`),
  load: (id: string) =>
    request<{ scenario: Scenario }>(`scenarios/${id}/evaluation`),
  save: (
    draft: { name: string; description: string; assumptions: Assumptions },
    id?: string,
  ) =>
    request<Scenario>(
      id ? `scenarios/${id}` : "scenarios",
      id ? "PUT" : "POST",
      draft,
    ),
};
