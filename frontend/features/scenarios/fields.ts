import type { Assumptions } from "@/types/model";
export type Field = {
  key: keyof Assumptions;
  label: string;
  unit: string;
  group: string;
  min?: number;
  max?: number;
  integer?: boolean;
  percent?: boolean;
  help?: string;
};
const field = (
  key: keyof Assumptions,
  label: string,
  unit: string,
  group: string,
  extra: Partial<Field> = {},
): Field => ({ key, label, unit, group, min: 0, max: 1e9, ...extra });
export const fields: Field[] = [
  field("orders_per_day", "Orders per day", "orders/day", "Demand"),
  field("operating_days_per_month", "Operating days", "days/month", "Demand", {
    min: 1,
    max: 31,
    integer: true,
  }),
  field("operating_hours_per_day", "Opening hours", "hours/day", "Demand", {
    min: 0.000001,
    max: 24,
  }),
  field(
    "average_order_value",
    "Average order value",
    "€/order",
    "Customer economics",
  ),
  field(
    "delivery_fee",
    "Delivery fee charged",
    "€/order",
    "Customer economics",
  ),
  field("gross_margin", "Product gross margin", "%", "Customer economics", {
    percent: true,
    max: 100,
  }),
  field(
    "payment_fee_rate",
    "Payment processing rate",
    "%",
    "Customer economics",
    { percent: true, max: 100 },
  ),
  field(
    "payment_fee_per_order",
    "Fixed payment fee",
    "€/order",
    "Customer economics",
  ),
  field(
    "customer_acquisition_cost",
    "Customer acquisition cost",
    "€/customer",
    "Customer economics",
  ),
  field(
    "new_customer_order_share",
    "New-customer order share",
    "%",
    "Customer economics",
    { percent: true, max: 100 },
  ),
  field("monthly_rent", "Monthly rent", "€/month", "Dark-store economics"),
  field("monthly_utilities", "Utilities", "€/month", "Dark-store economics"),
  field(
    "monthly_software_admin",
    "Software & administration",
    "€/month",
    "Dark-store economics",
  ),
  field(
    "store_orders_per_hour",
    "Store throughput ceiling",
    "orders/hour",
    "Dark-store economics",
  ),
  field("fulfilment_workers", "Fulfilment staff", "FTE", "Fulfilment", {
    integer: true,
    max: 100000,
    help: "Monthly paid-hour budgets, not simultaneous workers.",
  }),
  field(
    "worker_paid_hours_per_month",
    "Paid hours per worker",
    "hours/month",
    "Fulfilment",
    { min: 0.000001, max: 240 },
  ),
  field(
    "worker_hourly_cost",
    "Fully loaded worker cost",
    "€/hour",
    "Fulfilment",
  ),
  field(
    "worker_productive_fraction",
    "Worker productive time",
    "%",
    "Fulfilment",
    { percent: true, min: 0.0001, max: 100 },
  ),
  field(
    "picking_minutes_per_order",
    "Picking time",
    "minutes/order",
    "Fulfilment",
    { min: 0.000001 },
  ),
  field(
    "packing_minutes_per_order",
    "Packing time",
    "minutes/order",
    "Fulfilment",
  ),
  field(
    "variable_fulfilment_cost_per_order",
    "Packaging & consumables",
    "€/order",
    "Fulfilment",
    { help: "Incremental cost only; excludes fixed payroll." },
  ),
  field("riders", "Number of riders", "FTE", "Delivery", {
    integer: true,
    max: 100000,
  }),
  field(
    "rider_paid_hours_per_month",
    "Paid hours per rider",
    "hours/month",
    "Delivery",
    { min: 0.000001, max: 240 },
  ),
  field("rider_hourly_cost", "Fully loaded rider cost", "€/hour", "Delivery"),
  field("rider_productive_fraction", "Rider productive time", "%", "Delivery", {
    percent: true,
    min: 0.0001,
    max: 100,
  }),
  field(
    "average_delivery_distance_km",
    "One-way delivery distance",
    "km",
    "Delivery",
  ),
  field(
    "rider_average_speed_kmh",
    "Average rider speed",
    "km/hour",
    "Delivery",
    { min: 0.000001 },
  ),
  field(
    "delivery_handoff_minutes",
    "Delivery handoff time",
    "minutes/order",
    "Delivery",
    { min: 0.000001 },
  ),
  field(
    "variable_delivery_cost_per_order",
    "Incremental delivery cost",
    "€/order",
    "Delivery",
    {
      help: "Excludes rider payroll. Do not enter an all-inclusive courier fee.",
    },
  ),
  field(
    "shrinkage_rate",
    "Shrinkage / wastage",
    "% of sales",
    "Inventory / losses",
    { percent: true, max: 100 },
  ),
  field(
    "stockout_rate",
    "Orders lost to stockouts",
    "% of demand",
    "Inventory / losses",
    { percent: true, max: 100 },
  ),
  field("starting_cash", "Starting cash balance", "€", "Cash"),
];
export const groups = [...new Set(fields.map((field) => field.group))];

// Decimal shifts are presentation conversions only; preserve input precision exactly.
export function shiftDecimal(value: string, places: number): string {
  if (!/^\d+(\.\d*)?$/.test(value)) return value;
  const [whole, fraction = ""] = value.split(".");
  const digits = whole + fraction;
  const point = whole.length + places;
  const shifted =
    point <= 0
      ? `0.${"0".repeat(-point)}${digits}`
      : point >= digits.length
        ? digits + "0".repeat(point - digits.length)
        : `${digits.slice(0, point)}.${digits.slice(point)}`;
  return shifted
    .replace(/^0+(?=\d)/, "")
    .replace(/(\.\d*?)0+$/, "$1")
    .replace(/\.$/, "");
}

export const sameAssumption = (a: string | number, b: string | number) =>
  shiftDecimal(String(a), 0) === shiftDecimal(String(b), 0);
