import type { Assumptions } from "@/types/model";
import { fields, shiftDecimal } from "./fields";

function readRows(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let cell = "";
  let quoted = false;
  let closed = false;
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (quoted) {
      if (ch === '"' && text[i + 1] === '"') {
        cell += '"';
        i++;
      } else if (ch === '"') {
        quoted = false;
        closed = true;
      } else cell += ch;
    } else if (ch === '"') {
      if (cell || closed) throw new Error("CSV has an unexpected quote.");
      quoted = true;
    } else if (ch === "," || ch === "\n" || ch === "\r") {
      row.push(cell);
      cell = "";
      closed = false;
      if (ch !== ",") {
        if (row.some((v) => v.trim())) rows.push(row);
        row = [];
        if (ch === "\r" && text[i + 1] === "\n") i++;
      }
    } else {
      if (closed) throw new Error("Unexpected text after a quoted CSV value.");
      cell += ch;
    }
  }
  if (quoted) throw new Error("CSV contains an unclosed quote.");
  row.push(cell);
  if (row.some((v) => v.trim())) rows.push(row);
  return rows;
}
export function parseCsv(text: string): Assumptions {
  if (text.length > 64000)
    throw new Error("CSV exceeds the 64 KB assumptions limit.");
  const [header, ...rows] = readRows(text.replace(/^\uFEFF/, ""));
  if (header?.join(",") !== "Assumption,Value,Unit")
    throw new Error(
      "Expected CSV header: Assumption,Value,Unit. Export a template first.",
    );
  const values: Record<string, string | number> = {};
  for (const row of rows) {
    if (row.length !== 3)
      throw new Error("Every CSV row must have exactly three columns.");
    const [label, value, unit] = row.map((v) => v.trim());
    const field = fields.find((f) => f.label === label);
    if (!field) throw new Error(`Unknown assumption: ${label.slice(0, 80)}`);
    if (field.key in values) throw new Error(`Duplicate assumption: ${label}`);
    if (unit !== field.unit)
      throw new Error(`${label}: expected unit ${field.unit}.`);
    const decimals = field.integer ? 0 : field.percent ? 4 : 6;
    if (
      !/^\d+(?:\.\d+)?$/.test(value) ||
      (value.split(".")[1]?.length || 0) > decimals
    )
      throw new Error(
        `${label}: enter a nonnegative plain number with at most ${decimals} decimal places. No formulas or scientific notation.`,
      );
    const n = Number(value);
    if (!Number.isFinite(n) || n < (field.min ?? 0) || n > (field.max ?? 1e9))
      throw new Error(`${label}: value is outside the supported range.`);
    values[field.key] = field.integer
      ? n
      : field.percent
        ? shiftDecimal(value, -2)
        : value;
  }
  const missing = fields.filter((f) => !(f.key in values));
  if (missing.length)
    throw new Error(
      `Missing assumptions: ${missing.map((f) => f.label).join(", ")}. Import a complete template; defaults are never silently filled.`,
    );
  return values as Assumptions;
}
export function exportCsv(assumptions: Assumptions): string {
  const quote = (value: string) => `"${value.replaceAll('"', '""')}"`;
  const csv =
    "Assumption,Value,Unit\r\n" +
    fields
      .map((f) =>
        [
          f.label,
          f.percent
            ? shiftDecimal(String(assumptions[f.key]), 2)
            : String(assumptions[f.key]),
          f.unit,
        ]
          .map(quote)
          .join(","),
      )
      .join("\r\n") +
    "\r\n";
  parseCsv(csv); // Do not export incomplete or invalid edited assumptions.
  return csv;
}
