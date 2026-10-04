import fs from "node:fs";
import path from "node:path";
import { freshness, type Freshness } from "./freshness";

export type Stats = {
  percentile: number; zone: string; zscore: number; ath: { date: string; value: number }; atl: { date: string; value: number };
  mean: number; since: string; year_ago: number | null; five_years_ago: number | null; gap: number;
};
export type Indicator = {
  id: string; name: string; scope: "usa" | "global"; perspective: string; layer: string; source: string; code: string; unit: string | null;
  frequency: string; rationale: string | null; source_url: string | null; stale_after_days: number;
  value: number | null; previous: number | null; ref_date: string | null; as_of: string | null;
  history: [string, number][]; trend: number[]; stats: Stats | null; score: number | null; polarity: number; transform: string | null;
  status: Freshness | null;
};
export type Driver = { id: string; name: string; score: number; ref_date: string };
export type Index = {
  label: string; state: string | null; value: number | null; n: number; total: number; change_12m?: number | null;
  history: [string, number, number][]; drivers: Driver[]; summary: string;
};
export type Backtest = {
  recessions: number; avg_before: number | null; avg_other: number | null; window_months: number; difference?: number;
  threshold?: number; hits?: number; hit_rate?: number; false_alarm_rate?: number | null; flagged_months?: number;
};
export type Valuation = {
  current: number; current_date: string; percentile: number; band: [number, number]; since: string;
  horizons: { years: number; similar: Record<string, number>; all: Record<string, number> }[];
};
export type Run = { source: string; started_at: string; status: string; rows: number; error: string | null };
export type Data = {
  generated_at: string | null; methodology_version: string | null; indicators: Indicator[];
  indices: Record<"usa" | "global", Record<string, Index>>; recessions: [string, string][]; runs: Run[];
  backtest: Record<string, Backtest>; valuation: Valuation | null;
};

/** Reads data/data.json produced by the ingestion job (real data only). Missing file = empty state. */
export function loadData(): Data {
  const file = path.join(process.cwd(), "data", "data.json");
  const empty: Data = { generated_at: null, methodology_version: null, indicators: [], indices: { usa: {}, global: {} }, recessions: [], runs: [], backtest: {}, valuation: null };
  if (!fs.existsSync(file)) return empty;
  const raw = JSON.parse(fs.readFileSync(file, "utf8"));
  return {
    ...empty, ...raw,
    indicators: raw.indicators.map((i: Indicator) => ({ ...i, status: i.ref_date ? freshness(i.ref_date, i.stale_after_days) : null })),
  };
}
