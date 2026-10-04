import os
from datetime import date
import pytest
from sqlalchemy import select, func
from kondratiev import db, ingest, freshness
from kondratiev.sources import fred, worldbank

CAT = [
    dict(id="f1", perspective="kondratiev", layer="timing", source="fred", code="DGS10", name="x", country="USA",
         unit="%", frequency="daily", stale_after_days=7),
    dict(id="w1", perspective="kondratiev", layer="structure", source="worldbank", code="FP.CPI.TOTL.ZG", name="y",
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


def test_failed_source_is_isolated_and_logged(engine, monkeypatch):
    monkeypatch.delenv("FRED_API_KEY")
    failures = ingest.run(engine, CAT, session=FakeSession())
    assert failures == 1
    assert db.latest_ref_date(engine, "w1") is not None  # World Bank still ingested
    with engine.connect() as c:
        row = c.execute(select(db.runs).where(db.runs.c.source == "fred")).one()
    assert row.status == "failed" and "FRED_API_KEY" in row.error


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
