export type Format =
  "money" | "unitmoney" | "number" | "percent" | "months" | "points";
export function format(
  value: string | number | null,
  kind: Format = "number",
): string {
  if (value === null) return "—";
  const n = Number(value);
  if (!Number.isFinite(n)) return "—";
  if (kind === "money" || kind === "unitmoney")
    return new Intl.NumberFormat("en-IE", {
      style: "currency",
      currency: "EUR",
      minimumFractionDigits: kind === "unitmoney" ? 2 : 0,
      maximumFractionDigits: kind === "unitmoney" ? 2 : 0,
    }).format(n);
  if (kind === "percent")
    return new Intl.NumberFormat("en-IE", {
      style: "percent",
      maximumFractionDigits: 1,
    }).format(n);
  if (kind === "points")
    return `${new Intl.NumberFormat("en-IE", { maximumFractionDigits: 1 }).format(n * 100)} pp`;
  return (
    new Intl.NumberFormat("en-IE", { maximumFractionDigits: 1 }).format(n) +
    (kind === "months" ? " months" : "")
  );
}
export function signed(value: string | null, kind: Format): string {
  return value === null
    ? "Not comparable"
    : `${Number(value) > 0 ? "+" : ""}${format(value, kind)}`;
}
