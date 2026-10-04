import fs from "node:fs";
import path from "node:path";
import { freshness } from "./freshness";
import type { Data, Indicator } from "./data";

const SPARK_POINTS = 60;

export const withStatus = (i: Indicator): Indicator => ({ ...i, status: i.ref_date ? freshness(i.ref_date, i.stale_after_days) : null });

/** Reads data/data.json produced by the ingestion job (real data only). Missing file = empty state. */
export function loadData(): Data {
  const file = path.join(process.cwd(), "data", "data.json");
  const empty: Data = { generated_at: null, methodology_version: null, indicators: [], indices: { usa: {} }, recessions: [],
    runs: [], backtest: {}, valuation: null, extremes: { usa: [] }, thresholds: {}, recession_watch: null, analogs: null, movers: [] };
  if (!fs.existsSync(file)) return empty;
  const raw = JSON.parse(fs.readFileSync(file, "utf8"));
  return { ...empty, ...raw, indicators: raw.indicators.map(withStatus) };
}

/** What the page embeds: full histories stay in /data.json and load when an indicator is opened. */
export function slim(data: Data): Data {
  return {
    ...data,
    indicators: data.indicators.map((i) => ({
      ...i, history: i.history.slice(-SPARK_POINTS), trend: [],
      view: i.view ? { ...i.view, history: [], trend: [] } : null,
    })),
  };
}
