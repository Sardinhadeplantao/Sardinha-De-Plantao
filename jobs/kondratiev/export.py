"""Export the database to web/data/data.json (what the static site reads). Real data only."""
import json
import sys
from datetime import datetime, timezone
from sqlalchemy import select
from kondratiev import db

SPARK_POINTS = 60


def sample(values, n=SPARK_POINTS):
    if len(values) <= n:
        return values
    step = (len(values) - 1) / (n - 1)
    return [values[round(i * step)] for i in range(n)]


def build(engine):
    with engine.connect() as c:
        cat = c.execute(select(db.series_catalog).order_by(db.series_catalog.c.perspective, db.series_catalog.c.id)).mappings().all()
        indicators = []
        for s in cat:
            obs = c.execute(select(db.observations).where(db.observations.c.series_id == s["id"])
                            .order_by(db.observations.c.ref_date)).mappings().all()
            last, prev = (obs[-1] if obs else None), (obs[-2] if len(obs) > 1 else None)
            indicators.append({**{k: s[k] for k in s.keys()},
                "value": last["value"] if last else None, "previous": prev["value"] if prev else None,
                "ref_date": last["ref_date"].isoformat() if last else None,
                "as_of": last["as_of"].isoformat() if last else None,
                "history": [[o["ref_date"].isoformat(), o["value"]] for o in sample(obs)]})
        runs = [{**r, "started_at": r["started_at"].isoformat(), "finished_at": r["finished_at"].isoformat() if r["finished_at"] else None}
                for r in c.execute(select(db.runs).order_by(db.runs.c.id.desc()).limit(20)).mappings().all()]
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "indicators": indicators, "runs": runs}


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "../web/data/data.json"
    data = build(db.get_engine())
    with open(out, "w") as f:
        json.dump(data, f, ensure_ascii=False)
    print(f"exported {len(data['indicators'])} indicators")
