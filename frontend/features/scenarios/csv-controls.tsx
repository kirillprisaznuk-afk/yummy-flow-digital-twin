import { useRef } from "react";
import { useWorkspace } from "./workspace";
import { parseCsv, exportCsv } from "./csv";
export function CsvControls() {
  const w = useWorkspace();
  const input = useRef<HTMLInputElement>(null);
  return (
    <section className="panel csv-controls">
      <h2>Assumptions CSV</h2>
      <p className="table-note">
        Export the selected draft as a template. Imports require all inputs and
        matching units; percentages use 25 for 25%. Imported data remains
        unsaved.
      </p>
      <div className="button-row">
        <button
          disabled={w.busy || !w.drafts}
          onClick={() => {
            try {
              const text = exportCsv(w.drafts![w.selected].assumptions);
              const url = URL.createObjectURL(
                new Blob([text], { type: "text/csv;charset=utf-8" }),
              );
              const link = document.createElement("a");
              link.href = url;
              link.download = "yummy-flow-synthetic-assumptions.csv";
              link.click();
              setTimeout(() => URL.revokeObjectURL(url), 1000);
            } catch (e) {
              w.reportError((e as Error).message);
            }
          }}
        >
          Export assumptions CSV
        </button>
        <button disabled={w.busy} onClick={() => input.current?.click()}>
          Import assumptions CSV
        </button>
        <input
          ref={input}
          type="file"
          accept=".csv,text/csv"
          aria-label="Import assumptions file"
          className="sr-only"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            e.target.value = "";
            if (!file) return;
            try {
              if (file.size > 64000)
                throw new Error("CSV exceeds the 64 KB assumptions limit.");
              await w.importAssumptions(parseCsv(await file.text()));
            } catch (error) {
              w.reportError((error as Error).message);
            }
          }}
        />
      </div>
    </section>
  );
}
