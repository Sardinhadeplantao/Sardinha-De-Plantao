import os
from datetime import date
import pytest
from sqlalchemy import select, func
from kondratiev import db, ingest, freshness
from kondratiev.sources import fred, worldbank

CAT = [
    dict(id="f1", scope="usa", perspective="kondratiev", layer="timing", source="fred", code="DGS10", name="x", country="USA",
         unit="%", frequency="daily", stale_after_days=7),
    dict(id="w1", scope="global", perspective="kondratiev", layer="structure", source="worldbank", code="FP.CPI.TOTL.ZG", name="y",
         country="WLD", unit="%", frequency="annual", stale_after_days=730),
]


class Resp:
    def __init__(self, data, status=200): self.data, self.status_code = data, status
    def json(self): return self.data
    def raise_for_status(self): pass


class FakeSession:
    def __init__(self): self.calls = []
    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, params))
        if "stlouisfed" in url:
            return Resp({"observations": [{"date": "2026-09-30", "value": "4.1"}, {"date": "2026-10-01", "value": "."}]})
        return Resp([{"page": 1}, [{"date": "2023", "value": 5.9}, {"date": "2024", "value": None}]])


@pytest.fixture
def engine(tmp_path, monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "secret-key")
    return db.get_engine(f"sqlite:///{tmp_path/'t.db'}")


def count(engine, table):
    with engine.connect() as c:
        return c.execute(select(func.count()).select_from(table)).scalar()


def test_ingest_end_to_end_and_idempotent(engine):
    s = FakeSession()
    assert ingest.run(engine, CAT, session=s) == 0
    assert ingest.run(engine, CAT, session=s) == 0
    assert count(engine, db.observations) == 2          # '.' and null skipped; rerun does not duplicate
    assert count(engine, db.runs) == 4                  # one audit row per source per run
    assert db.latest_ref_date(engine, "f1") == date(2026, 9, 30)
    assert db.latest_ref_date(engine, "w1") == date(2023, 12, 31)


def test_failed_source_is_isolated_and_logged(engine):
    class Broken:
        @staticmethod
        def fetch(series, session=None): raise RuntimeError("source down")
    cat = [dict(CAT[0], source="broken"), CAT[1]]
    failures = ingest.run(engine, cat, sources={"broken": Broken, "worldbank": worldbank}, session=FakeSession())
    assert failures == 1
    assert db.latest_ref_date(engine, "w1") is not None  # the other source still ingested
    with engine.connect() as c:
        row = c.execute(select(db.runs).where(db.runs.c.source == "broken")).one()
    assert row.status == "failed" and "source down" in row.error


def test_fred_skipped_without_key(engine, monkeypatch):
    monkeypatch.delenv("FRED_API_KEY")
    assert ingest.run(engine, CAT, session=FakeSession()) == 0
    assert db.latest_ref_date(engine, "f1") is None and db.latest_ref_date(engine, "w1") is not None


def test_treasury_parses_csv_and_skips_blank():
    from kondratiev.sources import treasury
    treasury._cache.clear()
    class S:
        def get(self, *a, **k):
            return type("R", (), {"status_code": 200, "text": "Date,2 Yr,10 Yr\n10/01/2026,3.9,4.1\n09/30/2026,N/A,\n",
                                  "raise_for_status": lambda s: None})()
    rows = treasury.fetch({"code": "10 Yr"}, session=S(), first_year=2026)
    assert rows == [(date(2026, 10, 1), 4.1, False)]


def test_api_key_never_appears_in_error(monkeypatch):
    import requests
    from kondratiev import http
    class Boom:
        def get(self, *a, **k): raise requests.ConnectionError("down")
    monkeypatch.setattr(http.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError) as e:
        http.get_json("https://api.stlouisfed.org/x", {"api_key": "secret-key"}, session=Boom(), retries=1)
    assert "secret-key" not in str(e.value)


def test_worldbank_contract_rejects_invalid_indicator():
    class S:
        def get(self, *a, **k): return Resp([{"message": [{"id": "120"}]}])
    with pytest.raises(RuntimeError):
        worldbank.fetch(CAT[1], session=S())


def test_freshness():
    t = date(2026, 10, 4)
    assert freshness.status(date(2026, 10, 1), 7, t) == "ok"
    assert freshness.status(date(2026, 9, 20), 7, t) == "atrasado"
    assert freshness.status(date(2026, 8, 1), 7, t) == "obsoleto"


def test_fred_key_whitespace_is_ignored(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "  secret-key\n")
    s = FakeSession()
    fred.fetch(CAT[0], session=s)
    assert s.calls[0][1]["api_key"] == "secret-key"


def test_bis_parses_sdmx_csv_quarters():
    from kondratiev.sources import bis
    csv_text = "KEY,FREQ,TIME_PERIOD,OBS_VALUE\nX,Q,2025-Q4,4.5\nX,Q,2026-Q1,\nX,Q,2026-Q2,-1.2\n"
    class S:
        def get(self, *a, **k):
            return type("R", (), {"status_code": 200, "text": csv_text, "raise_for_status": lambda s: None})()
    rows = bis.fetch({"code": "WS_CREDIT_GAP/Q.US.P.A.C"}, session=S())
    assert rows == [(date(2025, 12, 31), 4.5, False), (date(2026, 6, 30), -1.2, False)]


def test_shiller_fails_loudly_when_layout_changes():
    from kondratiev.sources import shiller
    import xlrd
    class Sheet:
        ncols, nrows = 3, 5
        def cell_value(self, r, c): return "x"
    class WB:
        def sheet_by_name(self, n): return Sheet()
    shiller._cache["wb"] = WB()
    try:
        with pytest.raises(RuntimeError, match="layout changed"):
            shiller.fetch({"code": "CAPE"})
    finally:
        shiller._cache.clear()


def _facts(capex_by_year, ocf_by_year, fy_start_month=1):
    """Synthetic SEC companyfacts in the real structure: cash-flow items arrive year-to-date (3, 6, 9, 12 months)."""
    from datetime import date as D
    def entries(per_year):
        out = []
        for year, q in per_year.items():
            start = D(year, fy_start_month, 1)
            ends = [D(year, fy_start_month + 2, 28), D(year, fy_start_month + 5, 30), D(year, fy_start_month + 8, 30), D(year + 1, 1, 1)]
            ends = [e if e.year == year else D(year, 12, 31) for e in ends]
            ends[-1] = D(year, 12, 31)
            ends[0] = D(year, 3, 31)
            cum = 0
            for e, v in zip(ends, q):
                cum += v
                out.append({"start": start.isoformat(), "end": e.isoformat(), "val": cum, "form": "10-K" if e.month == 12 else "10-Q",
                            "filed": (e.replace(year=e.year + (1 if e.month == 12 else 0), month=1 if e.month == 12 else e.month)).isoformat()})
        return out
    return {"facts": {"us-gaap": {
        "PaymentsToAcquirePropertyPlantAndEquipment": {"units": {"USD": entries(capex_by_year)}},
        "NetCashProvidedByUsedInOperatingActivities": {"units": {"USD": entries(ocf_by_year)}}}}}


def test_edgar_rebuilds_quarters_from_ytd_and_aggregates(monkeypatch):
    from kondratiev.sources import edgar
    capex = {2023: [10, 10, 10, 10], 2024: [20, 20, 20, 20]}
    ocf = {2023: [40, 40, 40, 40], 2024: [40, 40, 40, 40]}
    monkeypatch.setattr(edgar, "_facts", lambda cik, session=None: _facts(capex, ocf))
    rows = edgar.fetch({"code": "capex_ocf"})
    # five identical companies: ratio equals one company's TTM capex / TTM OCF
    last = rows[-1]
    assert last[0] == date(2024, 12, 31) and abs(last[1] - 50.0) < 1e-6        # 80 / 160
    first_full = [r for r in rows if r[0] == date(2023, 12, 31)][0]
    assert abs(first_full[1] - 25.0) < 1e-6                                     # 40 / 160
    usd = edgar.fetch({"code": "capex"})
    assert abs(usd[-1][1] - 5 * 80 / 1e9) < 1e-12


def test_edgar_ignores_standalone_quarter_facts(monkeypatch):
    from kondratiev.sources import edgar
    capex = {2023: [10, 10, 10, 10], 2024: [20, 20, 20, 20]}
    ocf = {2023: [40, 40, 40, 40], 2024: [40, 40, 40, 40]}
    facts = _facts(capex, ocf)
    # extra 3-month stand-alone fact for Q2 2024 with a misleading value (10-Q income-style context)
    facts["facts"]["us-gaap"]["PaymentsToAcquirePropertyPlantAndEquipment"]["units"]["USD"].append(
        {"start": "2024-04-01", "end": "2024-06-30", "val": 999, "form": "10-Q", "filed": "2024-08-01"})
    monkeypatch.setattr(edgar, "_facts", lambda cik, session=None: facts)
    assert abs(edgar.fetch({"code": "capex_ocf"})[-1][1] - 50.0) < 1e-6


def test_edgar_uses_year_in_progress(monkeypatch):
    from kondratiev.sources import edgar
    facts = _facts({2023: [10, 10, 10, 10], 2024: [20, 20, 20, 20]}, {2023: [40, 40, 40, 40], 2024: [40, 40, 40, 40]})
    for tag in facts["facts"]["us-gaap"].values():  # drop the 2024 annual filing: only Q1-Q3 2024 are known
        tag["units"]["USD"] = [e for e in tag["units"]["USD"] if not (e["start"] == "2024-01-01" and e["end"] == "2024-12-31")]
    monkeypatch.setattr(edgar, "_facts", lambda cik, session=None: facts)
    last = edgar.fetch({"code": "capex_ocf"})[-1]
    assert last[0] == date(2024, 9, 30) and abs(last[1] - (10 + 20 * 3) / 160 * 100) < 1e-6 * 100


def test_edgar_merges_capex_tags_across_a_tag_change(monkeypatch):
    from kondratiev.sources import edgar
    facts = _facts({2023: [10, 10, 10, 10], 2024: [20, 20, 20, 20]}, {2023: [40, 40, 40, 40], 2024: [40, 40, 40, 40]})
    gaap = facts["facts"]["us-gaap"]
    entries = gaap.pop("PaymentsToAcquirePropertyPlantAndEquipment")["units"]["USD"]
    # the company used the old tag for 2023 and the new tag from 2024 on
    gaap["PaymentsToAcquirePropertyPlantAndEquipment"] = {"units": {"USD": [e for e in entries if e["start"].startswith("2023")]}}
    gaap["PaymentsToAcquireProductiveAssets"] = {"units": {"USD": [e for e in entries if e["start"].startswith("2024")]}}
    monkeypatch.setattr(edgar, "_facts", lambda cik, session=None: facts)
    assert abs(edgar.fetch({"code": "capex_ocf"})[-1][1] - 50.0) < 1e-6


def test_fred_ratio_series(monkeypatch):
    monkeypatch.setenv("FRED_API_KEY", "k")
    class S:
        def get(self, url, params=None, **k):
            vals = {"NUM": [("2026-01-01", "2000"), ("2026-04-01", "3000")], "DEN": [("2026-01-01", "10"), ("2026-04-01", ".")]}
            obs = [{"date": d, "value": v} for d, v in vals[params["series_id"]]]
            return Resp({"observations": obs})
    rows = fred.fetch({"code": "NUM/DEN*0.1"}, session=S())
    assert rows == [(date(2026, 1, 1), 20.0, False)]   # (2000/10)*0.1; the quarter with a missing denominator is skipped
