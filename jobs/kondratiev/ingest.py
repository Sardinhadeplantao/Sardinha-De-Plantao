"""Ingestion runner. Idempotent (upsert) and audited in `runs`. One source failing never stops the others."""
import sys
from datetime import datetime, timezone
from kondratiev import db
from kondratiev.catalog import CATALOG
import os
from kondratiev.sources import fred, treasury, worldbank

SOURCES = {"fred": fred, "treasury": treasury, "worldbank": worldbank}


def run(engine, catalog=CATALOG, sources=SOURCES, session=None):
    if not os.environ.get("FRED_API_KEY"):  # FRED is optional: without a key its series are simply not tracked
        catalog = [s for s in catalog if s["source"] != "fred"]
    db.upsert(engine, db.series_catalog, catalog, ["id"])
    failures = 0
    for name in sorted({s["source"] for s in catalog}):
        started = datetime.now(timezone.utc).replace(tzinfo=None)
        total, errors = 0, []
        for s in (x for x in catalog if x["source"] == name):
            try:
                rows = sources[name].fetch(s, session=session)
                as_of = datetime.now(timezone.utc).replace(tzinfo=None)
                total += db.upsert(engine, db.observations,
                                   [dict(series_id=s["id"], ref_date=d, vintage="latest", value=v, as_of=as_of,
                                         is_provisional=p) for d, v, p in rows],
                                   ["series_id", "ref_date", "vintage"])
            except Exception as exc:  # keep going: last stored data stays, flagged by freshness
                errors.append(f"{s['id']}: {exc}")
                if len(errors) >= 2 and total == 0:  # source looks unreachable: stop instead of waiting on every series
                    errors.append("fonte abortada após falhas consecutivas")
                    break
        status = "ok" if not errors else ("failed" if total == 0 else "partial")
        failures += bool(errors)
        _log(engine, name, started, status, total, errors)
    return failures


def _log(engine, name, started, status, total, errors):
    with engine.begin() as c:
        c.execute(db.runs.insert().values(source=name, started_at=started,
                                          finished_at=datetime.now(timezone.utc).replace(tzinfo=None),
                                          status=status, rows=total, error="; ".join(errors) or None))


if __name__ == "__main__":
    sys.exit(1 if run(db.get_engine()) else 0)  # non-zero exit makes the cron job fail and notify
