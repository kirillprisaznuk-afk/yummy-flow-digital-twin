import { fields, groups, shiftDecimal } from "./fields";
import { useWorkspace } from "./workspace";

export function ScenarioEditor() {
  const w = useWorkspace();
  if (!w.drafts) return null;
  const draft = w.drafts[w.selected];
  return (
    <form
      id="scenario-form"
      onInvalidCapture={(e) => {
        const details = (e.target as HTMLElement).closest("details");
        if (details) details.open = true;
      }}
      onSubmit={(e) => {
        e.preventDefault();
        void w.calculate();
      }}
    >
      <fieldset disabled={w.busy}>
        <div className="editor-toolbar">
          <div className="segmented" aria-label="Scenario to edit">
            {(["baseline", "alternative"] as const).map((slot) => (
              <button
                type="button"
                key={slot}
                aria-pressed={w.selected === slot}
                onClick={() => w.setSelected(slot)}
              >
                {slot === "baseline" ? "Baseline" : "Alternative"}
              </button>
            ))}
          </div>
          <span className="small-muted">
            {draft.dirty ? "Unsaved edits" : draft.id ? "Saved" : "Not saved"}
          </span>
        </div>
        <section className="panel identity-panel">
          <div className="field">
            <label htmlFor="scenario-name">Scenario name</label>
            <input
              id="scenario-name"
              required
              maxLength={120}
              value={draft.name}
              onChange={(e) => w.edit(w.selected, { name: e.target.value })}
            />
          </div>
          <div className="field">
            <label htmlFor="scenario-description">
              Decision to explore{" "}
              <span className="small-muted">(optional)</span>
            </label>
            <input
              id="scenario-description"
              maxLength={2000}
              placeholder="e.g. Can we serve more demand with the same team?"
              value={draft.description}
              onChange={(e) =>
                w.edit(w.selected, { description: e.target.value })
              }
            />
          </div>
          <p className="table-note">
            Rename here, then choose Update saved to persist it. Only explicitly
            saved values are restored after refresh.
          </p>
          <div className="button-row">
            <button type="button" onClick={() => w.reset(w.selected)}>
              Reset to synthetic defaults
            </button>
            {w.selected === "alternative" && (
              <button
                type="button"
                onClick={() => w.reset("alternative", true)}
              >
                Copy baseline inputs
              </button>
            )}
          </div>
        </section>
        <div className="assumption-sections">
          {groups.map((group, index) => (
            <details
              className="panel assumption-group"
              key={group}
              open={index < 2}
            >
              <summary>
                <span>
                  <span className="group-number">0{index + 1}</span>
                  {group}
                </span>
                <span className="small-muted">
                  {fields.filter((f) => f.group === group).length} inputs
                </span>
              </summary>
              <div className="input-grid">
                {fields
                  .filter((f) => f.group === group)
                  .map((field) => {
                    const raw = String(draft.assumptions[field.key]);
                    return (
                      <div className="field" key={field.key}>
                        <label htmlFor={field.key}>{field.label}</label>
                        <div className="input-with-unit">
                          <input
                            id={field.key}
                            type="number"
                            required
                            min={field.min}
                            max={field.max}
                            step={
                              field.integer
                                ? 1
                                : field.percent
                                  ? "0.0001"
                                  : "0.000001"
                            }
                            value={field.percent ? shiftDecimal(raw, 2) : raw}
                            aria-describedby={
                              field.help ? `${field.key}-help` : undefined
                            }
                            onChange={(e) => {
                              const value = /e/i.test(e.target.value)
                                ? String(Number(e.target.value))
                                : e.target.value;
                              w.edit(w.selected, {
                                assumptions: {
                                  ...draft.assumptions,
                                  [field.key]:
                                    field.integer && value !== ""
                                      ? Number(value)
                                      : field.percent
                                        ? shiftDecimal(value, -2)
                                        : value,
                                },
                              });
                            }}
                          />
                          <span>{field.unit}</span>
                        </div>
                        {field.help && (
                          <small id={`${field.key}-help`}>{field.help}</small>
                        )}
                      </div>
                    );
                  })}
              </div>
            </details>
          ))}
        </div>
        <div className="editor-actions">
          <span>Changes only affect results after calculation.</span>
          <button className="primary" type="submit">
            {w.busy ? "Working…" : "Calculate scenarios"}
          </button>
          <button
            type="button"
            onClick={(e) => {
              if (e.currentTarget.form?.reportValidity())
                void w.save(w.selected, false);
            }}
          >
            Save as new
          </button>
          {draft.id && (
            <button
              type="button"
              onClick={(e) => {
                if (e.currentTarget.form?.reportValidity())
                  void w.save(w.selected, true);
              }}
            >
              Update saved
            </button>
          )}
        </div>
      </fieldset>
    </form>
  );
}
