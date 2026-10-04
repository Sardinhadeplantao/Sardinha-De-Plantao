import { test } from "node:test";
import assert from "node:assert";
import { bases, reading } from "./reading.ts";

const stats = { percentile: 40, zone: "neutro", since: "1996-12-01", ath: { date: "2008-12-01", value: 20 }, atl: { date: "2007-06-01", value: 2.4 },
  year_ago: 3.1, five_years_ago: 3.9, gap: -0.2 };
const base: any = { id: "x", perspective: "minsky", unit: "p.p.", value: 3.24, ref_date: "2026-10-01", polarity: 1, transform: "level", score: 42, stats, view: null };

test("reading describes position, movement, trend and scoring", () => {
  const r = reading(base);
  assert.equal(r.length, 4);
  assert.match(r[0], /percentil 40/);
  assert.match(r[2], /abaixo/);
  assert.match(r[3], /fragilidade/);
});

test("reading handles a series without data", () => {
  assert.deepEqual(reading({ ...base, stats: null, value: null }), ["Sem dados coletados para esta série."]);
});

test("trending series are read through their change first", () => {
  const view = { label: "Variação em 12 meses", unit: "%", value: 2.9, ref_date: "2026-08-01", stats: { ...stats, percentile: 47 }, history: [], trend: [] };
  const i = { ...base, unit: "índice", value: 334, transform: "chg12", view, stats: { ...stats, percentile: 100 } };
  const b = bases(i);
  assert.equal(b[0].label, "Variação em 12 meses");
  assert.match(reading(i)[0], /variação em 12 meses \(2,9 %/);
  assert.match(reading(i, b[1]).join(" "), /nível tende a ficar sempre perto da máxima/);
});
