import type { Freshness } from "./freshness";

export type Stats = {
  percentile: number; zone: string; zscore: number; ath: { date: string; value: number }; atl: { date: string; value: number };
  mean: number; since: string; year_ago: number | null; five_years_ago: number | null; gap: number;
};
/** A series read through its change (e.g. 12-month inflation) instead of its ever-rising level. */
export type View = {
  label: string; unit: string | null; value: number; ref_date: string; stats: Stats;
  history: [string, number][]; trend: number[];
};
export type Indicator = {
  id: string; name: string; scope: "usa" | "global"; perspective: string; layer: string; source: string; code: string; unit: string | null;
  frequency: string; rationale: string | null; source_url: string | null; stale_after_days: number;
  value: number | null; previous: number | null; ref_date: string | null; as_of: string | null;
  history: [string, number][]; trend: number[]; stats: Stats | null; score: number | null; polarity: number; transform: string | null;
  view: View | null; status: Freshness | null;
};
export type Driver = { id: string; name: string; score: number; ref_date: string; group: string };
export type Index = {
  label: string; state: string | null; value: number | null; n: number; total: number; change_12m?: number | null;
  as_of: string | null; stale: boolean; history: [string, number, number][]; drivers: Driver[]; summary: string;
};
export type Extreme = { id: string; name: string; percentile: number; basis: string; direction: string };
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
  backtest: Record<string, Backtest>; valuation: Valuation | null; extremes: Record<"usa" | "global", Extreme[]>;
};
