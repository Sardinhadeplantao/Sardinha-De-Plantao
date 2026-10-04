import "server-only";
import { freshness, type Freshness } from "./freshness";

export type Row = Record<string, any>;
const url = process.env.DATABASE_URL ?? "sqlite:///../jobs/kondratiev.db";

/** Read-only query. Postgres (Supabase) in production, SQLite for local runs. */
async function query(sql: string, params: unknown[] = []): Promise<Row[]> {
  if (url.startsWith("sqlite:")) {
    const { DatabaseSync } = await import("node:sqlite");
    const db = new DatabaseSync(url.replace(/^sqlite:\/+/, url.startsWith("sqlite:////") ? "/" : ""), { readOnly: true });
    try { return db.prepare(sql.replace(/\$\d+/g, "?")).all(...(params as any[])) as Row[]; } finally { db.close(); }
  }
  const { Pool } = await import("pg");
  const pool = new Pool({ connectionString: url, ssl: { rejectUnauthorized: false }, max: 2 });
  try { return (await pool.query(sql, params as any[])).rows; } finally { await pool.end(); }
}

const day = (v: unknown) => (v instanceof Date ? v.toISOString().slice(0, 10) : String(v).slice(0, 10));
const ts = (v: unknown) => (v instanceof Date ? v.toISOString() : String(v));

export type Indicator = {
  id: string; name: string; perspective: string; layer: string; source: string; code: string; unit: string | null;
  frequency: string; rationale: string | null; sourceUrl: string | null;
  value: number | null; previous: number | null; refDate: string | null; asOf: string | null; status: Freshness | null;
};

export async function loadIndicators(): Promise<Indicator[]> {
  const cat = await query("SELECT * FROM series_catalog ORDER BY perspective, id");
  const out: Indicator[] = [];
  for (const s of cat) {
    const obs = await query(
      "SELECT ref_date, value, as_of FROM observations WHERE series_id = $1 ORDER BY ref_date DESC LIMIT 2", [s.id]);
    const [last, prev] = obs;
    out.push({
      id: s.id, name: s.name, perspective: s.perspective, layer: s.layer, source: s.source, code: s.code, unit: s.unit,
      frequency: s.frequency, rationale: s.rationale, sourceUrl: s.source_url,
      value: last ? Number(last.value) : null, previous: prev ? Number(prev.value) : null,
      refDate: last ? day(last.ref_date) : null, asOf: last ? ts(last.as_of) : null,
      status: last ? freshness(day(last.ref_date), Number(s.stale_after_days)) : null,
    });
  }
  return out;
}

export async function loadRuns(): Promise<Row[]> {
  return (await query("SELECT source, started_at, status, rows, error FROM runs ORDER BY id DESC LIMIT 15"))
    .map((r) => ({ ...r, started_at: ts(r.started_at) }));
}
