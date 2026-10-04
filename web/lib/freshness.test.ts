import { test } from "node:test";
import assert from "node:assert";
import { freshness } from "./freshness.ts";

const t = new Date("2026-10-04T00:00:00Z");
test("freshness thresholds", () => {
  assert.equal(freshness("2026-10-01", 7, t), "ok");
  assert.equal(freshness("2026-09-20", 7, t), "atrasado");
  assert.equal(freshness("2026-08-01", 7, t), "obsoleto");
});
