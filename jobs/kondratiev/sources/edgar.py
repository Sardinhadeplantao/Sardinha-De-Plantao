"""SEC EDGAR XBRL company facts (official, keyless; the SEC requires a descriptive User-Agent).

Hyperscaler AI-capex proxy: trailing-four-quarter capital expenditure and operating cash flow, summed over
Microsoft, Alphabet, Amazon, Meta and Oracle. `code` is 'capex_ocf' (ratio, %) or 'capex' (US$ bn).
Cash-flow statements report year-to-date amounts, so discrete quarters are rebuilt by differencing."""
import os
from datetime import date, datetime, timedelta
import requests
from kondratiev.http import get_json

COMPANIES = {"MSFT": 789019, "GOOGL": 1652044, "AMZN": 1018724, "META": 1326801, "ORCL": 1341439}
CAPEX, OCF = "PaymentsToAcquirePropertyPlantAndEquipment", "NetCashProvidedByUsedInOperatingActivities"
# The SEC requires a descriptive User-Agent with a contact address. The default uses the repository owner's public
# GitHub no-reply address; set the SEC_USER_AGENT secret to override it with a monitored contact.
UA = (os.environ.get("SEC_USER_AGENT") or "").strip() or \
    "KondratievMonitor Sardinhadeplantao 209699569+Sardinhadeplantao@users.noreply.github.com"
_cache: dict = {}


def _facts(cik, session=None):
    if cik not in _cache:
        _cache[cik] = get_json(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json",
                               headers={"User-Agent": UA, "Accept-Encoding": "gzip, deflate"}, min_interval=0.3, session=session, error_body=True)
    return _cache[cik]


def _d(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def discrete_quarters(entries):
    """entries: facts with start/end/val/filed. Returns {quarter_end: discrete value} from year-to-date amounts."""
    best = {}
    for e in entries:
        if e.get("form") not in ("10-K", "10-Q", "10-K/A", "10-Q/A"):
            continue
        key = (e["start"], e["end"])
        if key not in best or e["filed"] > best[key]["filed"]:
            best[key] = e
    # Fiscal-year starts: the start of every annual period and the day after each annual period ends (the year in progress).
    annual = [(k, e) for k, e in best.items() if 340 <= (_d(k[1]) - _d(k[0])).days <= 400]
    starts = {k[0] for k, _ in annual} | {(_d(k[1]) + timedelta(days=1)).isoformat() for k, _ in annual}
    by_start = {}
    for (s_, en), e in best.items():
        days = (_d(en) - _d(s_)).days
        if days > 400 or s_ not in starts:  # ignore stand-alone quarter facts that do not start at a fiscal year start
            continue
        by_start.setdefault(s_, {})[en] = (days, e["val"])
    out = {}
    for s, ends in by_start.items():
        prev_val, prev_end = 0.0, None
        for en in sorted(ends):
            days, val = ends[en]
            span = (_d(en) - _d(prev_end)).days if prev_end else days
            if prev_end is None or 60 <= span <= 120:  # consecutive year-to-date points roughly one quarter apart
                out[_d(en)] = val - prev_val
                prev_val, prev_end = val, en
    return out


def ttm(quarters):
    """Trailing four discrete quarters, only when they are consecutive (about 91 days apart)."""
    ends = sorted(quarters)
    res = {}
    for i in range(3, len(ends)):
        w = ends[i - 3:i + 1]
        if all(70 <= (w[k + 1] - w[k]).days <= 110 for k in range(3)):
            res[w[-1]] = sum(quarters[x] for x in w)
    return res


def _calendar_quarter(d):
    """Map a fiscal quarter end to the nearest calendar quarter end (Aug->Sep, Nov->Dec, Feb->Mar, May->Jun)."""
    m = d.month
    m = {1: 3, 2: 3, 3: 3, 4: 6, 5: 6, 6: 6, 7: 9, 8: 9, 9: 9, 10: 12, 11: 12, 12: 12}[m]
    y = d.year + (1 if d.month == 12 and m == 3 else 0)
    return date(y, m, 30 if m in (6, 9) else 31)


def fetch(series, since=None, session=None):
    per_company, notes = {}, []
    for name, cik in COMPANIES.items():
        gaap = _facts(cik, session)["facts"]["us-gaap"]
        raw = {t: gaap.get(t, {}).get("units", {}).get("USD", []) for t in (CAPEX, OCF)}
        q = {t: discrete_quarters(v) for t, v in raw.items()}
        cap, ocf = ttm(q[CAPEX]), ttm(q[OCF])
        per_company[name] = {_calendar_quarter(d): (cap[d], ocf[d]) for d in cap if d in ocf}
        last = max(per_company[name]) if per_company[name] else None
        notes.append(f"{name}: raw capex/ocf={len(raw[CAPEX])}/{len(raw[OCF])}, quarters={len(q[CAPEX])}/{len(q[OCF])}, "
                     f"ttm={len(cap)}/{len(ocf)}, usable={len(per_company[name])}, last={last}")
    quarters = set.intersection(*(set(v) for v in per_company.values()))
    if not quarters:
        raise RuntimeError("no common quarters across the five companies | " + " | ".join(notes))
    out = []
    for q in sorted(quarters):
        capex = sum(per_company[c][q][0] for c in per_company)
        ocf = sum(per_company[c][q][1] for c in per_company)
        if series["code"] == "capex_ocf":
            out.append((q, capex / ocf * 100, False))
        else:
            out.append((q, capex / 1e9, False))
    return out


def validate(series, session=None):
    rows = fetch(series, session=session)
    return f"{series['code']}: {len(rows)} quarters, latest {rows[-1][0]} = {rows[-1][1]:.1f}"
