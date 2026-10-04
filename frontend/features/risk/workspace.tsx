"use client";
import { useEffect, useState } from "react";
import { api } from "@/api/client";
import { useWorkspace } from "@/features/scenarios/workspace";
import { format } from "@/lib/format";
import type {
  SensitivityResult,
  SimulationResult,
  SimulationSettings,
} from "@/types/model";
import { SensitivityResults } from "./sensitivity-results";
import { SimulationResults } from "./simulation-results";
import { inputs } from "./fields";

export function RiskWorkspace() {
  const w = useWorkspace();
  const [settings, setSettings] = useState<SimulationSettings | null>(null);
  const [sensitivity, setSensitivity] = useState<{
    key: string;
    data: SensitivityResult;
  } | null>(null);
  const [simulation, setSimulation] = useState<{
    key: string;
    data: SimulationResult;
  } | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    let active = true;
    api
      .riskDefaults()
      .then((value) => {
        if (active) {
          setSettings(value);
          setError("");
        }
      })
      .catch(() => {
        if (active)
          setError(
            "Analysis settings could not be loaded. Check the API connection and retry.",
          );
      });
    return () => {
      active = false;
    };
  }, [attempt]);
  const a = w.drafts?.[w.selected].assumptions;
  const scenarioKey = JSON.stringify([w.selected, a]);
  const simulationKey = JSON.stringify([scenarioKey, settings]);
  const s = sensitivity?.key === scenarioKey ? sensitivity.data : null;
  const m = simulation?.key === simulationKey ? simulation.data : null;
  async function run(kind: "sensitivity" | "simulation") {
    if (!a || !settings) return;
    setBusy(kind);
    setError("");
    try {
      if (kind === "sensitivity")
        setSensitivity({ key: scenarioKey, data: await api.sensitivity(a) });
      else
        setSimulation({
          key: simulationKey,
          data: await api.simulate(a, settings),
        });
    } catch (e) {
      setError(
        e instanceof Error
          ? e.message
          : "Analysis could not be completed. Please retry.",
      );
    } finally {
      setBusy("");
    }
  }
  return (
    <>
      <section className="model-note">
        <h2>Model-based uncertainty, not a forecast</h2>
        <p>
          Each draw is one hypothetical steady-state month. Staffing, stockouts
          and physical capacity remain fixed. Independent input draws do not
          capture correlations, daily volatility, growth or queues. Existing
          saved assumptions are never changed by analysis.
        </p>
      </section>
      {error && (
        <div role="alert" className="alert error section-space">
          {error}
          {!settings && (
            <button onClick={() => setAttempt((v) => v + 1)}>
              Retry analysis settings
            </button>
          )}
        </div>
      )}
      <section
        className="panel section-space"
        aria-label="Sensitivity analysis"
      >
        <div className="panel-heading">
          <div>
            <span className="eyebrow">
              DETERMINISTIC · ONE VARIABLE AT A TIME
            </span>
            <h2>Sensitivity analysis</h2>
          </div>
          <button
            className="primary"
            disabled={!!busy || !a || !settings}
            onClick={() => void run("sensitivity")}
          >
            {busy === "sensitivity" ? "Calculating…" : "Run sensitivity"}
          </button>
        </div>
        <p className="table-note">
          Tests −20%, −10%, baseline, +10%, +20% relative changes. Gross margin
          here changes relatively: 25% +20% becomes 30%, not 45%. Labour means
          the fulfilment hourly rate; delivery means incremental cost excluding
          rider payroll. Other inputs stay fixed.
        </p>
        {!s ? (
          <p className="empty-library">
            Run sensitivity for the selected scenario. Previous results are
            hidden when assumptions or selection change.
          </p>
        ) : (
          <SensitivityResults s={s} />
        )}
      </section>
      <section
        className="panel section-space"
        aria-label="Monte Carlo simulation"
      >
        <span className="eyebrow">SIMULATED · BOUNDED TRIANGULAR INPUTS</span>
        <h2>Monte Carlo simulation</h2>
        {!settings ? (
          <p role="status">Loading uncertainty settings…</p>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void run("simulation");
            }}
          >
            <fieldset disabled={!!busy || !a}>
              <p className="table-note">
                Baseline is the most-likely value. Width defines
                minimum/maximum, not a standard deviation. Gross margin uses
                percentage points; other inputs use relative percentages. Bounds
                stop at zero, 100% margin and the model input ceiling. Near a
                boundary the distribution becomes asymmetric. Zero relative
                inputs stay zero.
              </p>
              <div className="risk-inputs section-space">
                {inputs.map(([key, label, unit]) => (
                  <div className="field" key={key}>
                    <label htmlFor={`risk-${key}`}>{label} uncertainty</label>
                    <input
                      id={`risk-${key}`}
                      type="number"
                      required
                      min="0"
                      max="100"
                      step="0.000001"
                      value={settings.uncertainty[key]}
                      onChange={(e) =>
                        setSettings({
                          ...settings,
                          uncertainty: {
                            ...settings.uncertainty,
                            [key]: e.target.value,
                          },
                        })
                      }
                    />
                    <small>
                      {unit} · Baseline{" "}
                      {a
                        ? format(
                            a[key],
                            key === "gross_margin"
                              ? "percent"
                              : key === "orders_per_day"
                                ? "number"
                                : "unitmoney",
                          )
                        : "—"}
                    </small>
                  </div>
                ))}
              </div>
              <div className="risk-inputs section-space">
                <div className="field">
                  <label htmlFor="risk-runs">Simulation runs</label>
                  <select
                    id="risk-runs"
                    value={settings.runs}
                    onChange={(e) =>
                      setSettings({ ...settings, runs: Number(e.target.value) })
                    }
                  >
                    {[1000, 5000, 10000].map((n) => (
                      <option value={n} key={n}>
                        {n.toLocaleString("en-IE")}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="field">
                  <label htmlFor="risk-seed">Random seed (optional)</label>
                  <input
                    id="risk-seed"
                    type="number"
                    min="0"
                    max="4294967295"
                    step="1"
                    value={settings.seed ?? ""}
                    onChange={(e) =>
                      setSettings({
                        ...settings,
                        seed:
                          e.target.value === "" ? null : Number(e.target.value),
                      })
                    }
                  />
                  <small>
                    Blank generates a seed that is returned with results.
                  </small>
                </div>
              </div>
              <div className="button-row section-space">
                <button className="primary" type="submit">
                  {busy === "simulation" ? "Simulating…" : "Run simulation"}
                </button>
                <button
                  type="button"
                  onClick={() =>
                    setSettings({
                      ...settings,
                      uncertainty: {
                        orders_per_day: "0",
                        average_order_value: "0",
                        gross_margin: "0",
                        variable_delivery_cost_per_order: "0",
                        variable_fulfilment_cost_per_order: "0",
                      },
                    })
                  }
                >
                  Set zero uncertainty
                </button>
              </div>
            </fieldset>
          </form>
        )}
        {busy && (
          <p role="status" className="table-note">
            Calculating on the backend. Leaving this page does not cancel an
            active server calculation.
          </p>
        )}
        {!m ? (
          <p className="empty-library">
            Run the simulation to see outcomes for these exact settings. No
            stale simulation values are shown.
          </p>
        ) : (
          <SimulationResults m={m} />
        )}
      </section>
    </>
  );
}
