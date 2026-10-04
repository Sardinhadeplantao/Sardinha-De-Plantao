export type Freshness = "ok" | "atrasado" | "obsoleto";

/** ok: within limit; atrasado: up to 2x the limit; obsoleto: beyond. Mirrors jobs/kondratiev/freshness.py. */
export function freshness(latestRef: string, staleAfterDays: number, today = new Date()): Freshness {
  const age = Math.floor((today.getTime() - new Date(latestRef + "T00:00:00Z").getTime()) / 86400000);
  if (age <= staleAfterDays) return "ok";
  return age <= 2 * staleAfterDays ? "atrasado" : "obsoleto";
}
