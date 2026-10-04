"""Export the database plus analytics to web/data/data.json (what the static site reads). Real data only."""
import json
import sys
from datetime import date, datetime, timezone
from sqlalchemy import select
from kondratiev import analytics as A
from kondratiev import db

PERSPECTIVES = ["kondratiev", "schumpeter", "perez", "freeman", "minsky"]


def _round(v):
    return round(v, 4) if isinstance(v, float) else v


def _recessions(hist):
    out, start, prev = [], None, None
    for d, v in hist:
        if v >= 1 and start is None:
            start = d
        if v < 1 and start is not None:
            out.append([start.isoformat(), prev.isoformat()])
            start = None
        prev = d
    if start is not None:
        out.append([start.isoformat(), prev.isoformat()])
    return out


def _index_summary(index, rows, drivers_raw, series, last_month, total):
    if not series:
        return {"label": A.INDEX_LABELS[index], "state": None, "value": None, "n": 0, "total": total, "history": [],
                "drivers": [], "summary": f"Dados insuficientes: menos de {A.MIN_MEMBERS} indicadores com histórico utilizável."}
    values = [v for _, v, _ in series]
    state = A.state_with_history(index, values)
    names = {r["id"]: r["name"] for r in rows}
    drivers = sorted(({"id": sid, "name": names[sid], "score": round(sc, 1), "ref_date": rd.isoformat()}
                      for sid, sc, rd in drivers_raw), key=lambda x: -x["score"])
    top = ", ".join(f"{d['name']} ({d['score']:.0f})" for d in drivers[:2])
    bottom = ", ".join(f"{d['name']} ({d['score']:.0f})" for d in drivers[-2:][::-1])
    change = values[-1] - values[-13] if len(values) > 12 else None
    return {
        "label": A.INDEX_LABELS[index], "state": state, "value": round(values[-1], 1), "n": series[-1][2], "total": total,
        "change_12m": round(change, 1) if change is not None else None,
        "history": [[A.key_to_label(k), round(v, 1), n] for k, v, n in series], "drivers": drivers,
        "summary": f"{state}: índice {values[-1]:.0f}/100, com {series[-1][2]} de {total} indicadores. "
                   f"Pontuações mais altas: {top}. Mais baixas: {bottom}.",
    }


def build(engine):
    with engine.connect() as c:
        cat = c.execute(select(db.series_catalog).order_by(db.series_catalog.c.perspective, db.series_catalog.c.id)).mappings().all()
        indicators, members, freqs, recessions, latest_key, context = [], {}, {}, [], 0, {}
        for s in cat:
            obs = [(o["ref_date"], o["value"]) for o in c.execute(
                select(db.observations).where(db.observations.c.series_id == s["id"]).order_by(db.observations.c.ref_date)).mappings()]
            as_of = c.execute(select(db.observations.c.as_of).where(db.observations.c.series_id == s["id"])
                              .order_by(db.observations.c.ref_date.desc()).limit(1)).scalar()
            if s["scope"] == "context":
                if s["id"] == "fred_usrec":
                    recessions = _recessions(obs)
                else:
                    context[s["id"]] = obs
                continue
            row = {k: s[k] for k in s.keys()}
            row.update(value=None, previous=None, ref_date=None, as_of=None, history=[], trend=[], stats=None, score=None,
                       polarity=A.SCORING[s["id"]][0] if s["id"] in A.SCORING else 0,
                       transform=A.SCORING[s["id"]][1] if s["id"] in A.SCORING else None)
            if obs:
                hist = A.to_monthly(obs, s["frequency"])
                st = A.describe(hist, s["frequency"])
                trend = st.pop("trend")
                row.update(value=obs[-1][1], previous=obs[-2][1] if len(obs) > 1 else None, ref_date=obs[-1][0].isoformat(),
                           as_of=as_of.isoformat() if as_of else None, stats={k: _round(v) for k, v in st.items()},
                           history=[[d.isoformat(), _round(v)] for d, v in hist], trend=[_round(t) for t in trend])
                latest_key = max(latest_key, A.month_key(obs[-1][0]))
                if s["id"] in A.SCORING:
                    scores = A.member_scores(s["id"], hist, s["frequency"])
                    if scores:
                        members.setdefault((s["scope"], s["perspective"]), {})[s["id"]] = scores
                        row["score"] = round(scores[-1][1], 1)
                    freqs[s["id"]] = s["frequency"]
            indicators.append(row)
    last_month = A.month_key(date.today())
    indices = {"usa": {}, "global": {}}
    for scope in indices:
        for persp in PERSPECTIVES:
            rows = [r for r in indicators if r["scope"] == scope and r["perspective"] == persp and r["id"] in A.SCORING]
            series, drivers = A.composite(members.get((scope, persp), {}), freqs, last_month)
            indices[scope][persp] = _index_summary(persp, rows, drivers, series, last_month, len(rows))
    thresholds = {"minsky": 60, "perez": 70}
    backtest = {p: A.backtest([(h[0], h[1]) for h in indices["usa"][p]["history"]], recessions, thresholds.get(p))
                for p in PERSPECTIVES if indices["usa"][p]["history"]}
    cape = next((i for i in indicators if i["id"] == "shiller_cape" and i["history"]), None)
    valuation = None
    if cape and context.get("shiller_real_tr"):
        valuation = A.forward_returns(A.to_monthly([(date.fromisoformat(d), v) for d, v in cape["history"]], "monthly"),
                                      A.to_monthly(context["shiller_real_tr"], "monthly"))
    return {"generated_at": datetime.now(timezone.utc).isoformat(), "methodology_version": A.METHODOLOGY_VERSION,
            "indicators": indicators, "indices": indices, "recessions": recessions,
            "backtest": {k: v for k, v in backtest.items() if v}, "valuation": valuation,
            "runs": [{**r, "started_at": r["started_at"].isoformat(),
                      "finished_at": r["finished_at"].isoformat() if r["finished_at"] else None}
                     for r in _runs(engine)]}


def _runs(engine):
    with engine.connect() as c:
        return c.execute(select(db.runs).order_by(db.runs.c.id.desc()).limit(20)).mappings().all()


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "../web/data/data.json"
    data = build(db.get_engine())
    with open(out, "w") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    for scope, idx in data["indices"].items():
        for p, v in idx.items():
            print(f"{scope:6} {p:11} {v['state']}  value={v['value']}  n={v['n']}/{v['total']}")
    for i in data["indicators"]:
        print(f"{i['id']:32} {len(i['history']):4} pts  latest={i['ref_date']}  value={i['value']}  score={i['score']}")
    for r in data["runs"][:8]:
        print(f"run {r['source']}: {r['status']} rows={r['rows']} {(r['error'] or '')[:1500]}")
    print("backtest:", json.dumps(data["backtest"], ensure_ascii=False))
    print("valuation:", json.dumps(data["valuation"], ensure_ascii=False))
    print(f"exported {len(data['indicators'])} indicators, {len(data['recessions'])} recessions")
