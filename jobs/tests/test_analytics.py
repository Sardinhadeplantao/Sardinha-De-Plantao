from datetime import date
import numpy as np
from kondratiev import analytics as A


def monthly(values, start=(2000, 1)):
    out, y, m = [], *start
    for v in values:
        out.append((date(y, m, 1), float(v)))
        m += 1
        if m > 12:
            y, m = y + 1, 1
    return out


def test_expanding_percentile_has_no_look_ahead():
    base = monthly(range(100))
    changed = base[:60] + [(d, v * 1000 - 5000) for d, v in base[60:]]  # alter only the future
    a = A.expanding_percentile(base, 10)
    b = A.expanding_percentile(changed, 10)
    assert a[:50] == b[:50]  # past percentiles unchanged by future data


def test_percentile_extremes():
    h = monthly([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    assert A.expanding_percentile(h, 3)[-1][1] > 90          # new high -> top of the range
    assert A.percentile_of([1, 2, 3, 4], 1) < 20


def test_hp_trend_of_a_line_is_the_line():
    y = np.arange(50, dtype=float) * 2 + 1
    assert np.allclose(A.hp_trend(y, 1600), y, atol=1e-6)


def test_hp_trend_smooths_noise():
    rng = np.random.default_rng(0)
    y = np.arange(120) + rng.normal(0, 5, 120)
    assert np.std(np.diff(A.hp_trend(y, 129600))) < np.std(np.diff(y))


def test_transform_chg12_pct_and_diff():
    h = monthly([100] * 12 + [110] * 12)
    t = A.transform(h, "chg12", "pct")
    assert abs(t[-1][1] - 10) < 1e-9 and t[0][0] == date(2001, 1, 1)
    assert A.transform(monthly([1] * 12 + [3]), "chg12", "diff")[-1][1] == 2


def test_to_monthly_keeps_last_of_month():
    obs = [(date(2026, 1, 2), 1.0), (date(2026, 1, 30), 2.0), (date(2026, 2, 3), 3.0)]
    assert A.to_monthly(obs, "daily") == [(date(2026, 1, 30), 2.0), (date(2026, 2, 3), 3.0)]
    assert A.to_monthly(obs, "annual") == obs


def test_composite_requires_minimum_members_and_applies_lag():
    hist = monthly(range(200))
    members = {f"s{i}": A.member_scores("fred_unrate", hist, "monthly") for i in range(3)}
    freqs = {k: "monthly" for k in members}
    series, drivers = A.composite(members, freqs, A.month_key(date(2016, 8, 1)))
    assert series and all(n >= 3 for _, _, n in series) and len(drivers) == 3
    # polarity -1 on an always-rising series -> low score
    assert series[-1][1] < 10
    only_two = {k: members[k] for k in list(members)[:2]}
    assert A.composite(only_two, freqs, A.month_key(date(2016, 8, 1)))[0] == []


def test_state_rules():
    assert A.state_for("minsky", 80) == "Fragilidade alta"
    assert A.state_for("minsky", 50) == "Fragilidade média"
    assert A.state_for("minsky", 10) == "Fragilidade baixa"
    assert A.state_for("kondratiev", 50) == "Transição"
    assert A.state_for("perez", 80).startswith("Frenesi")


def test_describe_stats():
    h = monthly([5, 1, 9, 3, 7, 2, 8, 4, 6, 10, 0, 5])
    d = A.describe(h, "monthly")
    assert d["ath"]["value"] == 10 and d["atl"]["value"] == 0 and 0 <= d["percentile"] <= 100


def test_export_build_runs_end_to_end(tmp_path):
    """Synthetic data, test-only: guards the export against runtime errors."""
    import json
    from datetime import datetime
    from kondratiev import db, export
    from kondratiev.catalog import CATALOG
    engine = db.get_engine(f"sqlite:///{tmp_path/'x.db'}")
    rng = np.random.default_rng(1)
    keep = [c for c in CATALOG if c["scope"] in ("usa", "context") and c["id"] in
            {"fred_baa10y", "fred_hy", "fred_nfci", "fred_tdsp", "fred_t10y2y", "fred_usrec", "wb_usa_fs_ast_prvt_gd_zs"}]
    db.upsert(engine, db.series_catalog, keep, ["id"])
    rows = []
    for c in keep:
        n = 300 if c["frequency"] != "annual" else 40
        for i in range(n):
            if c["frequency"] == "annual":
                d = date(1985 + i, 12, 31)
            else:
                y, m = divmod(2000 * 12 + i, 12)
                d = date(y, m + 1, 1)
            v = float(i % 7 in (3, 4)) if c["id"] == "fred_usrec" else float(rng.normal(5, 1))
            rows.append(dict(series_id=c["id"], ref_date=d, vintage="latest", value=v, as_of=datetime(2026, 1, 1), is_provisional=False))
    db.upsert(engine, db.observations, rows, ["series_id", "ref_date", "vintage"])
    data = export.build(engine)
    json.dumps(data)
    assert data["recessions"] and data["indices"]["usa"]["minsky"]["state"] is not None
    assert data["indices"]["usa"]["kondratiev"]["state"] is None          # no members -> honest "insufficient data"
    ind = next(i for i in data["indicators"] if i["id"] == "fred_hy")
    assert len(ind["history"]) == len(ind["trend"]) and ind["stats"]["percentile"] is not None
    assert all(i["scope"] != "context" for i in data["indicators"])


def test_backtest_finds_signal_before_recessions():
    labels = [f"{2000 + m // 12}-{m % 12 + 1:02d}" for m in range(240)]
    vals = [80 if 50 <= m < 72 or 150 <= m < 173 else 30 for m in range(240)]  # elevated in the 2 years before each recession
    rec = [("2006-01-01", "2006-12-01"), ("2014-06-01", "2015-01-01")]
    out = A.backtest(list(zip(labels, vals)), rec, threshold=60)
    assert out["recessions"] == 2 and out["difference"] > 20 and out["hit_rate"] == 100


def test_forward_returns_uses_only_realized_windows():
    cape = monthly([10 + (i % 20) for i in range(400)], (1980, 1))
    price = monthly([100 * 1.005 ** i for i in range(400)], (1980, 1))
    out = A.forward_returns(cape, price)
    assert out and out["horizons"][0]["similar"]["median"] > 0
    ten = next(h for h in out["horizons"] if h["years"] == 10)
    assert abs(ten["all"]["median"] - ((1.005 ** 12 - 1) * 100)) < 0.5


def test_alerts_detect_state_change_and_curve_inversion():
    from kondratiev import alerts
    prev = {"indices": {"usa": {"minsky": {"state": "Fragilidade média", "value": 50}}}, "indicators": [{"id": "fred_t10y2y", "value": 0.2}]}
    new = {"indices": {"usa": {"minsky": {"state": "Fragilidade alta", "value": 70}}}, "indicators": [{"id": "fred_t10y2y", "value": -0.1}], "runs": []}
    items = alerts.compare(prev, new)
    assert len(items) == 2 and "Fragilidade alta" in items[0] and "inverteu" in items[1]
    assert alerts.compare(new, new) == []


def test_alerts_do_not_flag_state_changes_caused_by_a_methodology_change():
    from kondratiev import alerts
    prev = {"methodology_version": "0.3", "indices": {"usa": {"minsky": {"state": "Fragilidade média", "value": 50}}}, "indicators": []}
    new = {"methodology_version": "0.4", "indices": {"usa": {"minsky": {"state": "Fragilidade alta", "value": 70}}}, "indicators": [], "runs": []}
    assert alerts.compare(prev, new) == []                       # no issue just because the rules changed
    new["runs"] = [{"source": "fred", "status": "failed"}]
    items = alerts.compare(prev, new)
    assert "Metodologia atualizada" in items[0] and "fred" in items[1] and len(items) == 2


def test_composite_balances_groups():
    hist_hi = monthly([100 + i for i in range(120)])          # rising level -> high percentile
    hist_lo = monthly([100 - i for i in range(120)])          # falling level -> low percentile
    s_hi = A.member_scores("ust_10y", hist_hi, "monthly")     # polarity +1, level
    s_lo = A.member_scores("ust_10y", hist_lo, "monthly")
    members = {"r1": s_hi, "r2": s_hi, "r3": s_hi, "p1": s_lo}
    freqs = {k: "monthly" for k in members}
    groups = {"r1": "juros", "r2": "juros", "r3": "juros", "p1": "preços"}
    series, _ = A.composite(members, freqs, A.month_key(date(2009, 12, 1)), groups)
    plain, _ = A.composite(members, freqs, A.month_key(date(2009, 12, 1)), {})
    # three correlated rate series no longer outvote the single price series
    assert abs(series[-1][1] - 50) < abs(plain[-1][1] - 50)
    assert abs(series[-1][1] - (s_hi[-1][1] + s_lo[-1][1]) / 2) < 1e-9


def test_index_summary_rounding_dedup_and_staleness():
    from kondratiev import export
    series = [(A.month_key(date(2025, m, 1)), 70.46, 3) for m in range(1, 13)]
    drivers = [("a", 90.0, date(2025, 1, 1)), ("b", 50.0, date(2025, 1, 1)), ("c", 10.0, date(2025, 1, 1))]
    rows = [{"id": k, "name": k.upper()} for k in "abc"]
    out = export._index_summary("minsky", rows, drivers, series, A.month_key(date(2026, 10, 1)), 3)
    assert out["value"] == 70.5 and "índice 71/100" in out["summary"]            # same integer as the site shows
    assert "Mais baixas: C (10)." in out["summary"] and out["summary"].count("B (50)") == 1  # no name in both lists
    assert out["stale"] and out["as_of"] == "2025-12" and "2025-12" in out["summary"]
    assert out["change_12m"] is None                                                 # no point exactly 12 months earlier


def test_derive_extends_cape_and_crosses_sources():
    from kondratiev import export
    obs = {
        "shiller_cape": [(date(2024, 8, 1), 34.0), (date(2024, 9, 1), 35.0)],
        "fred_sp500": [(date(2024, 9, 2), 5000.0), (date(2024, 9, 30), 5000.0), (date(2024, 10, 15), 5500.0)],
        "fred_cpiaucsl": [(date(2023, m, 1), 300.0) for m in range(1, 13)] + [(date(2024, m, 1), 309.0) for m in range(1, 10)] + [(date(2024, 10, 1), 309.0)],
        "fred_fedfunds": [(date(2024, 9, 1), 5.0)],
        "fred_dfii10": [(date(2024, 9, 3), 2.0), (date(2024, 9, 20), 2.0), (date(2024, 10, 3), 2.2)],
    }
    out, notes = export.derive(obs)
    cape = out["shiller_cape"]
    assert cape[-1][0] == date(2024, 10, 1) and abs(cape[-1][1] - 35.0 * 1.1) < 1e-9     # price +10%, CPI flat
    assert "estimado" in notes["shiller_cape"]
    assert abs(out["x_real_fedfunds"][0][1] - (5.0 - 3.0)) < 1e-9                          # 5% minus 3% inflation
    erp = dict(out["x_erp"])
    assert abs(erp[date(2024, 9, 1)] - (100 / 35.0 - 2.0)) < 1e-9
    assert abs(erp[date(2024, 10, 1)] - (100 / 38.5 - 2.2)) < 1e-9
    obs["shiller_real_tr"] = [(date(2024, 9, 1), 1000.0)]
    tr = export.derive(obs)[0]["shiller_real_tr"]
    assert tr[-1] == (date(2024, 10, 1), 1100.0)                                           # extended with price and CPI


def test_derive_skips_missing_inputs():
    from kondratiev import export
    out, notes = export.derive({"shiller_cape": [(date(2024, 9, 1), 35.0)]})
    assert out == {} and notes == {}


def test_sahm_rule_and_curve_probability():
    flat = monthly([4.0] * 20)
    assert all(abs(v) < 1e-9 for _, v in A.sahm_rule(flat))
    rising = monthly([4.0] * 15 + [4.3, 4.6, 4.9, 5.2])
    assert A.sahm_rule(rising)[-1][1] >= 0.5
    p = dict(A.curve_probability(monthly([2.0, 0.0, -1.0])))
    assert p[date(2000, 1, 1)] < p[date(2000, 2, 1)] < p[date(2000, 3, 1)]
    assert abs(p[date(2000, 2, 1)] - 29.7) < 0.5          # Φ(-0.5333) ≈ 29.7%


def test_score_change_uses_usable_month_keys():
    sc = [(100, 40.0, None), (101, 50.0, None), (103, 70.0, None)]
    assert A.score_change(sc, 3) == 30.0
    assert A.score_change(sc[:1], 3) is None


def test_analogs_pick_nearest_spaced_months_and_report_outcomes():
    keys = list(range(24000, 24000 + 240))
    hist = {p: [(k, 50.0 + (10 if (k - 24000) % 60 < 6 else 0)) for k in keys] for p in ("a", "b")}
    hist["a"][-1] = (keys[-1], 60.0)
    hist["b"][-1] = (keys[-1], 60.0)
    rec = [["2002-06-01", "2002-12-01"]]
    price = [(date(2000 + i // 12, i % 12 + 1, 1), 100 * 1.01 ** i) for i in range(240)]
    out = A.analogs(hist, rec, price, n=3)
    ms = out["matches"]
    assert len(ms) == 3 and all(m["distance"] == 0 for m in ms)
    ks = sorted(int(m["month"][:4]) * 12 + int(m["month"][5:7]) - 1 for m in ms)
    assert all(b - a >= 24 for a, b in zip(ks, ks[1:]))
    assert ms[0]["return_12m"] is not None


def test_export_full_catalog_synthetic(tmp_path):
    """Synthetic data for every catalog series, test-only: exercises watch, analogs and movers."""
    import json
    from datetime import datetime
    from kondratiev import db, export
    from kondratiev.catalog import CATALOG
    engine = db.get_engine(f"sqlite:///{tmp_path/'y.db'}")
    rng = np.random.default_rng(2)
    keep = [c for c in CATALOG if c["source"] != "derivado"]
    db.upsert(engine, db.series_catalog, CATALOG, ["id"])
    rows = []
    for c in keep:
        annual = c["frequency"] == "annual"
        for i in range(60 if annual else 600):
            d = date(1966 + i, 12, 31) if annual else date(1976 + i // 12, i % 12 + 1, 1)
            v = float(i % 97 in range(80, 88)) if c["id"] == "fred_usrec" else float(abs(rng.normal(5, 1)) + 1)
            rows.append(dict(series_id=c["id"], ref_date=d, vintage="latest", value=v, as_of=datetime(2026, 1, 1), is_provisional=False))
    db.upsert(engine, db.observations, rows, ["series_id", "ref_date", "vintage"])
    data = export.build(engine)
    json.dumps(data)
    assert list(data["indices"]) == ["usa"]
    assert data["recession_watch"]["total"] >= 5
    assert data["analogs"] and data["analogs"]["matches"]
    assert data["movers"] and all("change" in m for m in data["movers"])
    assert any(i["id"] == "x_sahm" and i["value"] is not None for i in data["indicators"])


def test_alerts_sahm_rule_crossing():
    from kondratiev import alerts
    mk = lambda v: {"methodology_version": "x", "indicators": [{"id": "x_sahm", "value": v}]}
    assert any("Sahm" in a for a in alerts.compare(mk(0.3), mk(0.55)))
    assert not alerts.compare(mk(0.3), mk(0.4))
