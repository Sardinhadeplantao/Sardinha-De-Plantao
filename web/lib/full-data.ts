import { freshness } from "./freshness";
import type { Indicator } from "./data";

let full: Promise<Indicator[] | null> | null = null;

/** Full indicator histories, fetched once from the published data.json (the page itself only embeds a summary). */
export function loadFullIndicators(base: string): Promise<Indicator[] | null> {
  full ??= fetch(`${base}/data.json`)
    .then((r) => (r.ok ? r.json() : null))
    .then((d) => (d ? (d.indicators as Indicator[]).map((i) => ({ ...i, status: i.ref_date ? freshness(i.ref_date, i.stale_after_days) : null })) : null))
    .catch(() => null);
  return full;
}
