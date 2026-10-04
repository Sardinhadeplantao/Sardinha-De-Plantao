import fs from "node:fs";
import path from "node:path";
import { freshness, type Freshness } from "./freshness";

export type Indicator = {
  id: string; name: string; perspective: string; layer: string; source: string; code: string; unit: string | null;
  frequency: string; rationale: string | null; source_url: string | null; stale_after_days: number;
  value: number | null; previous: number | null; ref_date: string | null; as_of: string | null;
  history: [string, number][]; status: Freshness | null;
};
export type Run = { source: string; started_at: string; status: string; rows: number; error: string | null };
export type Data = { generated_at: string | null; indicators: Indicator[]; runs: Run[] };

/** Reads data/data.json produced by the ingestion job (real data only). Missing file = empty state. */
export function loadData(): Data {
  const file = path.join(process.cwd(), "data", "data.json");
  if (!fs.existsSync(file)) return { generated_at: null, indicators: [], runs: [] };
  const raw = JSON.parse(fs.readFileSync(file, "utf8"));
  return {
    ...raw,
    indicators: raw.indicators.map((i: Indicator) => ({
      ...i, status: i.ref_date ? freshness(i.ref_date, i.stale_after_days) : null,
    })),
  };
}
