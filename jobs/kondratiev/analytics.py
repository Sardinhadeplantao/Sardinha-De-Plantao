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

METHODOLOGY_VERSION = "0.2"

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
    "wb_wld_fp_cpi_totl_zg": (1, "level", "diff"), "wb_wld_ny_gdp_defl_kd_zg": (1, "level", "diff"),
    "wb_wld_ny_gdp_mktp_kd_zg": (1, "level", "diff"),
    # Schumpeter: innovation inputs growing over five years
    **{f"wb_{c}_{k}": (1, "chg60", "pct") for c in ("usa", "wld")
       for k in ("gb_xpd_rsdv_gd_zs", "ip_pat_resd", "sp_pop_scie_rd_p6", "tx_val_tech_mf_zs")},
    # Perez: financial capital heat (valuation levels) and spread of the information paradigm
    **{f"wb_{c}_{k}": (1, "level", "diff") for c in ("usa", "wld") for k in ("cm_mkt_lcap_gd_zs", "cm_mkt_trad_gd_zs")},
    **{f"wb_{c}_tx_val_ictg_zs_un": (1, "chg60", "pct") for c in ("usa", "wld")},
    "wb_usa_cm_mkt_indx_zg": (1, "level", "diff"),
    # Freeman: diffusion of the new energy paradigm (renewables up, carbon and energy intensity down)
    **{f"wb_{c}_eg_fec_rnew_zs": (1, "chg60", "pct") for c in ("usa", "wld")},
    **{f"wb_{c}_{k}": (-1, "chg60", "pct") for c in ("usa", "wld") for k in ("en_ghg_co2_pc_ce_ar5", "eg_egy_prim_pp_kd")},
    # Minsky: financial fragility (100 = most fragile)
    **{f"wb_{c}_fs_ast_prvt_gd_zs": (1, "level", "diff") for c in ("usa", "wld")},
    "wb_usa_fs_ast_doms_gd_zs": (1, "level", "diff"), "wb_usa_fb_bnk_capa_zs": (-1, "level", "diff"),
    "fred_t10y2y": (-1, "level", "diff"), "fred_t10y3m": (-1, "level", "diff"), "fred_baa10y": (1, "level", "diff"),
    "fred_hy": (1, "level", "diff"), "fred_nfci": (1, "level", "diff"), "fred_tdsp": (1, "level", "diff"),
    "fred_m2sl": (1, "chg12", "pct"), "fred_mortgage30us": (1, "level", "diff"),
    "ust_3m": (1, "level", "diff"), "ust_2y": (1, "level", "diff"),
    "bis_us_credit_gap": (1, "level", "diff"), "bis_us_dsr": (1, "level", "diff"),
    # Perez: long-run equity valuation
    "shiller_cape": (1, "level", "diff"),
}

# publication lag (months) before a reading can be used, and max age (months) before it is considered stale
LAG = {"annual": 12, "quarterly": 3, "monthly": 1, "weekly": 0, "daily": 0}
MAX_AGE = {"annual": 36, "quarterly": 9, "monthly": 3, "weekly": 3, "daily": 3}
MIN_OBS = {"annual": 15, "quarterly": 40, "monthly": 60, "weekly": 60, "daily": 60}
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


def state_with_history(index, values):
    """State from the latest index value; Perez also flags an inflection (a drop of 10+ points from a recent frenzy)."""
    now = values[-1]
    if index == "perez" and len(values) > 1:
        peak = max(values[-24:])
        if peak >= 75 and now < 75 and peak - now >= 10:
            return "Inflexão (pós-euforia)"
    return state_for(index, now)


def member_scores(series_id, hist, frequency):
    """Monthly-usable scores (0-100) for one series: [(usable_from_monthkey, score, ref_date)]."""
    polarity, how, kind = SCORING[series_id]
    pct = expanding_percentile(transform(hist, how, kind), MIN_OBS[frequency])
    return [(month_key(d) + LAG[frequency], p if polarity > 0 else 100 - p, d) for d, p in pct]


def composite(members, frequencies, last_month):
    """members: {series_id: [(usable_key, score, ref_date)]}. Returns monthly [(key, mean_score, n)] and latest drivers."""
    if not members:
        return [], []
    start = min(s[0][0] for s in members.values() if s)
    out, drivers = [], []
    pointers = {k: 0 for k in members}
    for key in range(start, last_month + 1):
        vals, latest = [], []
        for sid, scores in members.items():
            i = pointers[sid]
            while i + 1 < len(scores) and scores[i + 1][0] <= key:
                i += 1
            pointers[sid] = i
            if scores and scores[i][0] <= key and key - scores[i][0] <= MAX_AGE[frequencies[sid]]:
                vals.append(scores[i][1])
                latest.append((sid, scores[i][1], scores[i][2]))
        if len(vals) >= MIN_MEMBERS:
            out.append((key, sum(vals) / len(vals), len(vals)))
            drivers = latest
    return out, drivers


def key_to_label(key):
    y, m = divmod(key, 12)
    return f"{y}-{m + 1:02d}"
