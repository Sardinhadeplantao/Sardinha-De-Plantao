"""Statistical layer. Everything here is deterministic and documented in docs/methodology.md.

Conventions
- A history is a list of (date, value) sorted by date.
- Percentiles used for scoring are EXPANDING (only data up to each date), so there is no look-ahead.
- The Hodrick-Prescott trend is two-sided and therefore revised at the edge: it is shown as context only and is
  never used in scores or states.
"""
from bisect import bisect_right
from datetime import date

import numpy as np

METHODOLOGY_VERSION = "0.6"

# series id -> (polarity, transform, kind)
#   polarity +1: a high reading means more expansion / heat / fragility for its index; -1: the opposite.
#   transform: level | chg12 (12-month change) | chg60 (5-year change). kind: pct | diff (how a change is measured).
SCORING = {
    # Kondratiev: phase A (expansion of prices, rates, output) versus phase B
    "fred_cpiaucsl": (1, "chg12", "pct"), "fred_ppiaco": (1, "chg12", "pct"), "fred_indpro": (1, "chg12", "pct"),
    "fred_dcoilwtico": (1, "chg12", "pct"), "fred_fedfunds": (1, "level", "diff"), "fred_dfii10": (1, "level", "diff"),
    "fred_unrate": (-1, "level", "diff"), "ust_5y": (1, "level", "diff"), "ust_10y": (1, "level", "diff"),
    "ust_30y": (1, "level", "diff"),
    "wb_usa_fp_cpi_totl_zg": (1, "level", "diff"), "wb_usa_ny_gdp_defl_kd_zg": (1, "level", "diff"),
    "wb_usa_ny_gdp_mktp_kd_zg": (1, "level", "diff"), "wb_usa_fr_inr_rinr": (1, "level", "diff"),
    # Schumpeter: innovation inputs growing over five years
    **{f"wb_{c}_{k}": (1, "chg60", "pct") for c in ("usa",)
       for k in ("gb_xpd_rsdv_gd_zs", "ip_pat_resd", "sp_pop_scie_rd_p6")},
    **{f"wb_{c}_tx_val_tech_mf_zs": (1, "level", "diff") for c in ("usa",)},  # short series: a 5-year change leaves too few points
    # Perez: financial capital heat (valuation levels) and spread of the information paradigm
    **{f"wb_{c}_{k}": (1, "level", "diff") for c in ("usa",) for k in ("cm_mkt_lcap_gd_zs", "cm_mkt_trad_gd_zs")},
    **{f"wb_{c}_tx_val_ictg_zs_un": (1, "chg60", "pct") for c in ("usa",)},
    "fred_buffett": (1, "level", "diff"), "fred_nasdaq": (1, "chg12", "pct"), "x_erp": (-1, "level", "diff"),
    # fresher official substitutes and cross-source series (v0.5)
    "fred_gdpc1": (1, "chg12", "pct"), "fred_gdpdef": (1, "chg12", "pct"),
    "fred_bfs": (1, "chg12", "pct"), "fred_rnd": (1, "chg60", "pct"),
    "bis_us_total_credit": (1, "level", "diff"), "x_real_fedfunds": (1, "level", "diff"),
    **{f"ember_{a}_{k}": (1, "chg12", "diff") for a in ("usa",) for k in ("renew", "windsolar")},
    **{f"ember_{a}_co2int": (-1, "chg12", "pct") for a in ("usa",)},
    # Freeman: diffusion of the new energy paradigm (renewables up, carbon and energy intensity down)
    **{f"wb_{c}_eg_fec_rnew_zs": (1, "chg60", "pct") for c in ("usa",)},
    **{f"wb_{c}_{k}": (-1, "chg60", "pct") for c in ("usa",) for k in ("en_ghg_co2_pc_ce_ar5", "eg_egy_prim_pp_kd")},
    # Minsky: financial fragility (100 = most fragile)
    **{f"wb_{c}_fs_ast_prvt_gd_zs": (1, "level", "diff") for c in ("usa",)},
    "fred_t10y2y": (-1, "level", "diff"), "fred_t10y3m": (-1, "level", "diff"), "fred_baa10y": (1, "level", "diff"),
    "fred_nfci": (1, "level", "diff"), "fred_tdsp": (1, "level", "diff"),
    "fred_m2sl": (1, "chg12", "pct"), "fred_mortgage30us": (1, "level", "diff"),
    "ust_3m": (1, "level", "diff"), "ust_2y": (1, "level", "diff"),
    "bis_us_credit_gap": (1, "level", "diff"), "bis_us_dsr": (1, "level", "diff"),
    # Perez: long-run equity valuation
    "shiller_cape": (1, "level", "diff"),
    # v0.6 additions
    "fred_ophnfb": (1, "chg60", "pct"), "fred_semis": (1, "chg12", "pct"), "ember_usa_demand": (1, "chg12", "pct"),
    "fred_commod": (1, "chg12", "pct"), "fred_copper": (1, "chg12", "pct"),
    "fred_vix": (1, "level", "diff"), "fred_sloos": (1, "level", "diff"), "fred_ccdelinq": (1, "level", "diff"), "sec_ai_capex_ocf": (1, "level", "diff"), "sec_ai_capex": (1, "chg12", "pct"),
}

# Sub-groups inside each lens. The index averages members within a group, then averages the groups, so a block of
# highly correlated series (e.g. five interest rates) does not outvote the rest. Unlisted series form their own lens group.
GROUPS = {
    **{k: "preços" for k in ("fred_gdpdef", "fred_cpiaucsl", "wb_usa_fp_cpi_totl_zg", "wb_usa_ny_gdp_defl_kd_zg")},
    **{k: "commodities" for k in ("fred_ppiaco", "fred_dcoilwtico", "fred_commod", "fred_copper")},
    **{k: "juros" for k in ("fred_fedfunds", "fred_dfii10", "ust_5y", "ust_10y", "ust_30y", "wb_usa_fr_inr_rinr")},
    **{k: "atividade" for k in ("fred_gdpc1", "fred_indpro", "fred_unrate", "wb_usa_ny_gdp_mktp_kd_zg")},
    **{k: "alavancagem" for k in ("wb_usa_fs_ast_prvt_gd_zs", "bis_us_credit_gap", "bis_us_total_credit", "bis_us_dsr",
                                  "fred_tdsp", "fred_m2sl", "fred_ccdelinq")},
    **{k: "preço do risco" for k in ("fred_baa10y", "fred_nfci", "fred_mortgage30us", "fred_vix", "fred_sloos")},
    **{k: "curva e política" for k in ("fred_t10y2y", "fred_t10y3m", "ust_3m", "ust_2y", "x_real_fedfunds")},
    **{k: "valuation" for k in ("wb_usa_cm_mkt_lcap_gd_zs", "wb_usa_cm_mkt_trad_gd_zs", "shiller_cape", "fred_buffett", "fred_nasdaq", "x_erp")},
    **{k: "investimento" for k in ("sec_ai_capex_ocf", "sec_ai_capex", "wb_usa_tx_val_ictg_zs_un")},
}
STALE_INDEX_MONTHS = 3  # an index whose latest value is older than this is flagged as stale

# publication lag (months) before a reading can be used, and max age (months) before it is considered stale
LAG = {"annual": 12, "quarterly": 3, "monthly": 1, "weekly": 0, "daily": 0}
MAX_AGE = {"annual": 24, "quarterly": 9, "monthly": 3, "weekly": 3, "daily": 3}
MIN_OBS = {"annual": 15, "quarterly": 28, "monthly": 60, "weekly": 60, "daily": 60}
MIN_MEMBERS = 3

STATES = {
    "kondratiev": [(60, "Fase A (expansão)"), (40, "Transição"), (0, "Fase B (contração)")],
    "schumpeter": [(60, "Cluster de inovação em formação"), (40, "Inovação estável"), (0, "Inovação em desaceleração")],
    "perez": [(75, "Frenesi (capital financeiro em euforia)"), (40, "Fase intermediária"), (0, "Implantação (capital produtivo)")],
    "freeman": [(60, "Difusão do novo paradigma em curso"), (40, "Difusão incipiente ou mista"), (0, "Paradigma vigente consolidado")],
    "minsky": [(67, "Fragilidade alta"), (33, "Fragilidade média"), (0, "Fragilidade baixa")],
}
INDEX_LABELS = {
    "kondratiev": "Índice de fase (100 = expansão plena)", "schumpeter": "Índice de inovação (100 = aceleração forte)",
    "perez": "Índice de calor financeiro (100 = euforia)", "freeman": "Índice de difusão do paradigma (100 = difusão forte)",
    "minsky": "Índice de fragilidade (100 = fragilidade máxima)",
}


def month_key(d: date) -> int:
    return d.year * 12 + d.month - 1


def to_monthly(obs, frequency):
    """Resample to one point per month (last observation of the month). Annual series are kept as they are."""
    if frequency == "annual":
        return list(obs)
    last = {}
    for d, v in obs:
        last[month_key(d)] = (d, v)
    return [last[k] for k in sorted(last)]


def value_at_or_before(hist, target: date):
    i = bisect_right([d for d, _ in hist], target)
    return hist[i - 1][1] if i else None


def shift_months(d: date, months: int) -> date:
    k = month_key(d) + months
    y, m = divmod(k, 12)
    return date(y, m + 1, min(d.day, 28))


def transform(hist, how, kind):
    """Return the transformed history. level -> identity; chgN -> change vs N months earlier (pct or diff)."""
    if how == "level":
        return list(hist)
    months = 12 if how == "chg12" else 60
    out = []
    for d, v in hist:
        past = value_at_or_before(hist, shift_months(d, -months))
        if past is None or hist[0][0] > shift_months(d, -months):
            continue
        if kind == "pct":
            if past <= 0:
                continue
            out.append((d, (v / past - 1) * 100))
        else:
            out.append((d, v - past))
    return out


def expanding_percentile(hist, min_obs):
    """Percentile rank (0-100) of each value among values up to and including its own date. No look-ahead."""
    out, seen = [], []
    for d, v in hist:
        seen.append(v)
        if len(seen) >= min_obs:
            below = sum(1 for x in seen if x < v)
            equal = sum(1 for x in seen if x == v)
            out.append((d, (below + 0.5 * equal) / len(seen) * 100))
    return out


def percentile_of(values, v):
    below = sum(1 for x in values if x < v)
    equal = sum(1 for x in values if x == v)
    return (below + 0.5 * equal) / len(values) * 100


def hp_trend(values, lam):
    """Hodrick-Prescott trend (two-sided). Context only: it is revised at the end of the sample."""
    n = len(values)
    if n < 5:
        return list(values)
    d = np.zeros((n - 2, n))
    for i in range(n - 2):
        d[i, i:i + 3] = (1, -2, 1)
    a = np.eye(n) + lam * d.T @ d
    return np.linalg.solve(a, np.asarray(values, dtype=float)).tolist()


def zone(p):
    if p is None:
        return None
    return "muito baixo" if p < 10 else "baixo" if p < 33 else "neutro" if p < 67 else "alto" if p < 90 else "muito alto"


def describe(hist, frequency):
    """Descriptive statistics of one series against its own history (the latest value is not look-ahead)."""
    vals = [v for _, v in hist]
    d, v = hist[-1]
    hi = max(hist, key=lambda x: x[1])
    lo = min(hist, key=lambda x: x[1])
    mean, sd = float(np.mean(vals)), float(np.std(vals))
    p = percentile_of(vals, v)
    lam = 100 if frequency == "annual" else 1600 if frequency == "quarterly" else 129600
    trend = hp_trend(vals, lam)
    return {
        "percentile": round(p, 1), "zone": zone(p), "zscore": round((v - mean) / sd, 2) if sd else 0.0,
        "ath": {"date": hi[0].isoformat(), "value": hi[1]}, "atl": {"date": lo[0].isoformat(), "value": lo[1]},
        "mean": mean, "since": hist[0][0].isoformat(),
        "year_ago": value_at_or_before(hist, shift_months(d, -12)), "five_years_ago": value_at_or_before(hist, shift_months(d, -60)),
        "trend": trend, "gap": v - trend[-1],
    }


def state_for(index, value):
    for threshold, label in STATES[index]:
        if value >= threshold:
            return label
    return STATES[index][-1][1]


def state_with_history(index, values, keys=None):
    """State from the latest index value; Perez also flags an inflection (a drop of 10+ points from a frenzy within
    the last 24 months). `keys` are month keys aligned with `values` (series can have gaps)."""
    now = values[-1]
    if index == "perez" and len(values) > 1:
        keys = keys or list(range(len(values)))
        peak = max(v for k, v in zip(keys, values) if k >= keys[-1] - 23)
        if peak >= 75 and now < 75 and peak - now >= 10:
            return "Inflexão (pós-euforia)"
    return state_for(index, now)


def member_scores(series_id, hist, frequency):
    """Monthly-usable scores (0-100) for one series: [(usable_from_monthkey, score, ref_date)]."""
    polarity, how, kind = SCORING[series_id]
    pct = expanding_percentile(transform(hist, how, kind), MIN_OBS[frequency])
    return [(month_key(d) + LAG[frequency], p if polarity > 0 else 100 - p, d) for d, p in pct]


def composite(members, frequencies, last_month, groups=None):
    """members: {series_id: [(usable_key, score, ref_date)]}. Returns monthly [(key, value, n)] and the latest drivers.
    value = mean over sub-groups of the mean of their members (see GROUPS); n = members available that month."""
    groups = GROUPS if groups is None else groups
    if not members:
        return [], []
    start = min(s[0][0] for s in members.values() if s)
    out, drivers = [], []
    pointers = {k: 0 for k in members}
    for key in range(start, last_month + 1):
        latest = []
        for sid, scores in members.items():
            i = pointers[sid]
            while i + 1 < len(scores) and scores[i + 1][0] <= key:
                i += 1
            pointers[sid] = i
            if scores and scores[i][0] <= key and key - scores[i][0] <= MAX_AGE[frequencies[sid]]:
                latest.append((sid, scores[i][1], scores[i][2]))
        if len(latest) >= MIN_MEMBERS:
            by_group = {}
            for sid, sc, _ in latest:
                by_group.setdefault(groups.get(sid, "_"), []).append(sc)
            value = sum(sum(v) / len(v) for v in by_group.values()) / len(by_group)
            out.append((key, value, len(latest)))
            drivers = latest
    return out, drivers


def value_months_ago(series, months):
    """Index value `months` before the latest point of a composite series [(key, value, n)], or None."""
    if not series:
        return None
    pos = {k: v for k, v, _ in series}
    return pos.get(series[-1][0] - months)


def key_to_label(key):
    y, m = divmod(key, 12)
    return f"{y}-{m + 1:02d}"


def backtest(index_history, recessions, threshold=None, window=24):
    """How did an index behave before U.S. recessions? In-sample, on revised (not point-in-time) data.
    index_history: [(YYYY-MM, value)]; recessions: [(start_iso, end_iso)]. Returns None when there is too little overlap."""
    keys = [int(l[:4]) * 12 + int(l[5:7]) - 1 for l, _ in index_history]
    vals = [v for _, v in index_history]
    if len(keys) < 36:
        return None
    pos = dict(zip(keys, vals))
    starts = [int(a[:4]) * 12 + int(a[5:7]) - 1 for a, _ in recessions]
    starts = [s for s in starts if keys[0] + 12 <= s <= keys[-1]]
    if not starts:
        return None
    pre = [pos[k] for s in starts for k in range(s - window, s) if k in pos]
    in_rec = {k for a, b in recessions for k in range(int(a[:4]) * 12 + int(a[5:7]) - 1, int(b[:4]) * 12 + int(b[5:7]))}
    calm = [v for k, v in pos.items() if k not in in_rec]
    out = {"recessions": len(starts), "avg_before": round(sum(pre) / len(pre), 1) if pre else None,
           "avg_other": round(sum(calm) / len(calm), 1) if calm else None, "window_months": window}
    if out["avg_before"] is not None and out["avg_other"] is not None:
        out["difference"] = round(out["avg_before"] - out["avg_other"], 1)
    if threshold is not None:
        hits = sum(1 for s in starts if any(pos.get(k, -1) >= threshold for k in range(s - window, s)))
        flagged = [k for k, v in pos.items() if v >= threshold and k not in in_rec]
        false = [k for k in flagged if not any(k < s <= k + window for s in starts)]
        out.update(threshold=threshold, hits=hits, hit_rate=round(hits / len(starts) * 100),
                   false_alarm_rate=round(len(false) / len(flagged) * 100) if flagged else None, flagged_months=len(flagged))
    return out


def forward_returns(valuation, price, horizons=(12, 60, 120), neighborhood=10):
    """Historical real annualized returns after months in which `valuation` stood near its current percentile.
    valuation / price: [(date, value)] monthly. Descriptive and in-sample; windows overlap, so the effective sample is small."""
    vk = {month_key(d): v for d, v in valuation if v > 0}
    pk = {month_key(d): v for d, v in price if v > 0}
    if not vk or not pk:
        return None
    cur_key = max(vk)
    cur = vk[cur_key]
    ranked = sorted(vk.values())
    cur_pct = percentile_of(ranked, cur)
    lo, hi = max(0, cur_pct - neighborhood), min(100, cur_pct + neighborhood)
    near = {k for k, v in vk.items() if lo <= percentile_of(ranked, v) <= hi}
    out = {"current": round(cur, 1), "current_date": key_to_label(cur_key), "percentile": round(cur_pct, 1),
           "band": [round(lo), round(hi)], "since": key_to_label(min(vk)), "horizons": []}
    for h in horizons:
        def stats(keys):
            r = sorted((pk[k + h] / pk[k]) ** (12 / h) - 1 for k in keys if k in pk and k + h in pk)
            if len(r) < 12:
                return None
            q = lambda p: r[min(len(r) - 1, int(p * len(r)))]
            return {"n": len(r), "median": round(q(0.5) * 100, 1), "p10": round(q(0.1) * 100, 1), "p90": round(q(0.9) * 100, 1),
                    "negative_share": round(sum(1 for x in r if x < 0) / len(r) * 100)}
        near_stats, all_stats = stats(near), stats(vk.keys())
        if near_stats and all_stats:
            out["horizons"].append({"years": h // 12, "similar": near_stats, "all": all_stats})
    return out if out["horizons"] else None


def sahm_rule(unrate):
    """Sahm rule on monthly unemployment [(date, %)]: 3-month average minus the lowest 3-month average of the
    previous 12 months. A reading >= 0.5 has marked the start of every U.S. recession since 1970."""
    avg = [(unrate[i][0], sum(v for _, v in unrate[i - 2:i + 1]) / 3) for i in range(2, len(unrate))]
    return [(d, v - min(a for _, a in avg[i - 12:i])) for i, (d, v) in enumerate(avg) if i >= 12]


def curve_probability(spread):
    """New York Fed probit (Estrella-Mishkin): probability (%) of a recession 12 months ahead from the monthly
    10-year minus 3-month spread [(date, p.p.)]."""
    from math import erf, sqrt
    return [(d, 50 * (1 + erf((-0.5333 - 0.6330 * s) / sqrt(2)))) for d, s in spread]


def score_change(scores, months=3):
    """Change of a member score over `months` (by usable month key). scores: [(key, score, ref_date)]."""
    if not scores:
        return None
    target = scores[-1][0] - months
    past = [sc for k, sc, _ in scores if k <= target]
    return scores[-1][1] - past[-1] if past else None


def analogs(histories, recessions, price=None, n=5, gap=24, min_age=24):
    """Months whose lens vector was closest to today's. histories: {lens: [(key, value)]} using the same lenses.
    Picks the `n` nearest months (Euclidean distance), at least `gap` months apart and at least `min_age` months old,
    and reports what followed: a U.S. recession start within 24 months and the real S&P 500 total return (Shiller)
    over the next 12 and 36 months. Descriptive and in-sample."""
    lenses = list(histories)
    maps = {p: dict(h) for p, h in histories.items()}
    common = sorted(set.intersection(*(set(m) for m in maps.values()))) if maps else []
    if len(common) < 60:
        return None
    now = common[-1]
    cur = [maps[p][now] for p in lenses]
    dist = lambda k: sum((maps[p][k] - c) ** 2 for p, c in zip(lenses, cur)) ** 0.5
    starts = [int(a[:4]) * 12 + int(a[5:7]) - 1 for a, _ in recessions]
    pk = {month_key(d): v for d, v in (price or []) if v > 0}
    picked = []
    for k in sorted((k for k in common if k <= now - min_age), key=dist):
        if all(abs(k - j) >= gap for j in picked):
            picked.append(k)
        if len(picked) == n:
            break

    def ret(k, h):
        return round(((pk[k + h] / pk[k]) ** (12 / h) - 1) * 100, 1) if k in pk and k + h in pk else None

    out = []
    for k in picked:
        nxt = [s for s in starts if k < s <= k + 24]
        out.append({"month": key_to_label(k), "distance": round(dist(k), 1),
                    "values": {p: round(maps[p][k], 1) for p in lenses},
                    "recession_within_24m": bool(nxt), "recession_start": key_to_label(nxt[0]) if nxt else None,
                    "return_12m": ret(k, 12), "return_36m": ret(k, 36)})
    return {"lenses": lenses, "current": {"month": key_to_label(now), "values": {p: round(c, 1) for p, c in zip(lenses, cur)}},
            "since": key_to_label(common[0]), "matches": out}
