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
