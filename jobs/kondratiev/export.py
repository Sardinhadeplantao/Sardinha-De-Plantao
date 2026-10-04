"""Export the database plus analytics to web/data/data.json (what the static site reads). Real data only."""
import json
import math
import sys
from datetime import date, datetime, timezone
from sqlalchemy import select
from kondratiev import analytics as A
from kondratiev import db
from kondratiev.freshness import status as freshness_status

PERSPECTIVES = ["kondratiev", "schumpeter", "perez", "freeman", "minsky"]


def _round(v):
    return round(v, 4) if isinstance(v, float) else v


def _int(v):
    """Round half up, the same way the site does (Math.round), so text and numbers never disagree."""
    return int(math.floor(v + 0.5))


VIEW_LABELS = {"chg12": "Variação em 12 meses", "chg60": "Variação em 5 anos"}


def _view(row, hist):
    """For series read through a change (prices, indices, counts), describe the change, not the ever-rising level."""
    if row["id"] not in A.SCORING:
        return None
    _, how, kind = A.SCORING[row["id"]]
    if how == "level":
        return None
    th = A.transform(hist, how, kind)
    if len(th) < 3:
        return None
    st = A.describe(th, row["frequency"])
    trend = st.pop("trend")
    return {"label": VIEW_LABELS[how], "unit": "%" if kind == "pct" else row["unit"], "value": _round(th[-1][1]),
            "ref_date": th[-1][0].isoformat(), "stats": {k: _round(v) for k, v in st.items()},
            "history": [[d.isoformat(), _round(v)] for d, v in th], "trend": [_round(t) for t in trend]}


def _monthly_mean(obs):
    """Daily or weekly observations -> one (first-of-month date, mean) per month."""
    acc = {}
    for d, v in obs:
        acc.setdefault(date(d.year, d.month, 1), []).append(v)
    return [(k, sum(v) / len(v)) for k, v in sorted(acc.items())]


def derive(obs):
    """Cross-source series computed from official data. Returns ({id: observations}, {id: note}).
    - shiller_cape is extended past the last published month: CAPE x (S&P 500 change) x (CPI change)⁻¹, keeping
      Shiller's 10-year real earnings of the last published month (they move slowly).
    - x_real_fedfunds = FEDFUNDS - CPI 12-month inflation.
    - x_erp = 100 / CAPE - 10-year TIPS real yield (monthly averages)."""
    out, notes = {}, {}
    cape, spx, cpi = obs.get("shiller_cape") or [], obs.get("fred_sp500") or [], obs.get("fred_cpiaucsl") or []
    if cape and spx and cpi:
        sp_m = dict(_monthly_mean(spx))
        cpi_h = [(d, v) for d, v in cpi]
        anchor_d, anchor_v = cape[-1]
        anchor_d = date(anchor_d.year, anchor_d.month, 1)
        sp0, cpi0 = sp_m.get(anchor_d), A.value_at_or_before(cpi_h, anchor_d)
        if sp0 and cpi0:
            ext = [(d, anchor_v * (v / sp0) * (cpi0 / A.value_at_or_before(cpi_h, d))) for d, v in sorted(sp_m.items())
                   if d > anchor_d and A.value_at_or_before(cpi_h, d)]
            if ext:
                out["shiller_cape"] = list(cape) + ext
                notes["shiller_cape"] = (f"Publicado por Shiller até {anchor_d.isoformat()[:7]}; de {ext[0][0].isoformat()[:7]} em diante, "
                                         "estimado com o S&P 500 e o CPI do FRED (lucros de 10 anos mantidos).")
    fed, cpi_m = obs.get("fred_fedfunds") or [], A.to_monthly(cpi, "monthly")
    if fed and cpi_m:
        infl = {date(d.year, d.month, 1): v for d, v in A.transform(cpi_m, "chg12", "pct")}
        out["x_real_fedfunds"] = [(date(d.year, d.month, 1), v - infl[date(d.year, d.month, 1)]) for d, v in fed
                                  if date(d.year, d.month, 1) in infl]
        notes["x_real_fedfunds"] = "Calculado: FEDFUNDS menos a inflação do CPI em 12 meses, mês a mês."
    cape_all, tips = out.get("shiller_cape") or cape, obs.get("fred_dfii10") or []
    if cape_all and tips:
        tips_m = dict(_monthly_mean(tips))
        out["x_erp"] = [(date(d.year, d.month, 1), 100 / v - tips_m[date(d.year, d.month, 1)]) for d, v in cape_all
                        if v > 0 and date(d.year, d.month, 1) in tips_m]
        notes["x_erp"] = "Calculado: rendimento de lucros do CAPE (100/CAPE) menos o juro real dos TIPS de 10 anos (média do mês)."
    return {k: v for k, v in out.items() if v}, notes


def _extremes(indicators, scope, limit=8):
    """Fresh indicators at the edges of their own history (percentile >= 95 or <= 5), most extreme first."""
    out = []
    for r in indicators:
        if r["scope"] != scope or not r["stats"] or freshness_status(date.fromisoformat(r["ref_date"]), r["stale_after_days"]) == "obsoleto":
            continue
        basis = r["view"] or r
        p = basis["stats"]["percentile"]
        if p >= 95 or p <= 5:
            out.append({"id": r["id"], "name": r["name"], "percentile": p, "basis": basis.get("label", "nível"),
                        "direction": "máxima" if p >= 95 else "mínima"})
    return sorted(out, key=lambda x: -abs(x["percentile"] - 50))[:limit]


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
                "drivers": [], "as_of": None, "stale": False,
                "summary": f"Dados insuficientes: menos de {A.MIN_MEMBERS} indicadores com histórico utilizável."}
    values, keys = [v for _, v, _ in series], [k for k, _, _ in series]
    value = round(values[-1], 1)
    state = A.state_with_history(index, values, keys)
    names = {r["id"]: r["name"] for r in rows}
    drivers = sorted(({"id": sid, "name": names[sid], "score": round(sc, 1), "ref_date": rd.isoformat(),
                       "group": A.GROUPS.get(sid, index)} for sid, sc, rd in drivers_raw), key=lambda x: -x["score"])
    top = drivers[:2]
    bottom = [d for d in reversed(drivers) if d not in top][:2]
    fmt = lambda ds: ", ".join(f"{d['name']} ({_int(d['score'])})" for d in ds)
    past = A.value_months_ago(series, 12)
    stale = keys[-1] < last_month - A.STALE_INDEX_MONTHS
    as_of = A.key_to_label(keys[-1])
    summary = f"{state}: índice {_int(value)}/100, com {series[-1][2]} de {total} indicadores. Pontuações mais altas: {fmt(top)}."
    if bottom:
        summary += f" Mais baixas: {fmt(bottom)}."
    if stale:
        summary += f" Atenção: último mês com dados suficientes foi {as_of}."
    return {
        "label": A.INDEX_LABELS[index], "state": state, "value": value, "n": series[-1][2], "total": total,
        "change_12m": round(value - past, 1) if past is not None else None, "as_of": as_of, "stale": stale,
        "history": [[A.key_to_label(k), round(v, 1), n] for k, v, n in series], "drivers": drivers, "summary": summary,
    }


def build(engine):
    with engine.connect() as c:
        cat = c.execute(select(db.series_catalog).order_by(db.series_catalog.c.perspective, db.series_catalog.c.id)).mappings().all()
        obs_by_id, as_of_by_id = {}, {}
        for s in cat:
            obs_by_id[s["id"]] = [(o["ref_date"], o["value"]) for o in c.execute(
                select(db.observations).where(db.observations.c.series_id == s["id"]).order_by(db.observations.c.ref_date)).mappings()]
            as_of_by_id[s["id"]] = c.execute(select(db.observations.c.as_of).where(db.observations.c.series_id == s["id"])
                                             .order_by(db.observations.c.ref_date.desc()).limit(1)).scalar()
    derived, notes = derive(obs_by_id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    for k, v in derived.items():
        obs_by_id[k] = v
        as_of_by_id[k] = as_of_by_id.get(k) or now
    indicators, members, freqs, recessions, latest_key, context = [], {}, {}, [], 0, {}
    for s in cat:
        obs, as_of = obs_by_id[s["id"]], as_of_by_id[s["id"]]
        if s["scope"] == "context":
            if s["id"] == "fred_usrec":
                recessions = _recessions(obs)
            else:
                context[s["id"]] = obs
            continue
        row = {k: s[k] for k in s.keys()}
        row.update(value=None, previous=None, ref_date=None, as_of=None, history=[], trend=[], stats=None, score=None, view=None,
                   note=notes.get(s["id"]),
                   polarity=A.SCORING[s["id"]][0] if s["id"] in A.SCORING else 0,
                   transform=A.SCORING[s["id"]][1] if s["id"] in A.SCORING else None)
        if obs:
            hist = A.to_monthly(obs, s["frequency"])
            st = A.describe(hist, s["frequency"])
            trend = st.pop("trend")
            row.update(value=obs[-1][1], previous=obs[-2][1] if len(obs) > 1 else None, ref_date=obs[-1][0].isoformat(),
                       as_of=as_of.isoformat() if as_of else None, stats={k: _round(v) for k, v in st.items()},
                       history=[[d.isoformat(), _round(v)] for d, v in hist], trend=[_round(t) for t in trend],
                       view=_view(row, hist))
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
            "extremes": {scope: _extremes(indicators, scope) for scope in ("usa", "global")},
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
            print(f"{scope:6} {p:11} {v['state']}  value={v['value']}  n={v['n']}/{v['total']}  as_of={v['as_of']}  stale={v['stale']}")
    print("extremes:", json.dumps(data["extremes"]["usa"], ensure_ascii=False))
    for i in data["indicators"]:
        print(f"{i['id']:32} {len(i['history']):4} pts  latest={i['ref_date']}  value={i['value']}  score={i['score']}")
    for r in data["runs"][:8]:
        print(f"run {r['source']}: {r['status']} rows={r['rows']} {(r['error'] or '')[:1500]}")
    print("backtest:", json.dumps(data["backtest"], ensure_ascii=False))
    print("valuation:", json.dumps(data["valuation"], ensure_ascii=False))
    print(f"exported {len(data['indicators'])} indicators, {len(data['recessions'])} recessions")
