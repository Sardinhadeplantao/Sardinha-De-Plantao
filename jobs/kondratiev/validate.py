"""Check every catalog series ID against its source API. Usage: python -m kondratiev.validate"""
import sys
from kondratiev.catalog import CATALOG
from kondratiev.ingest import SOURCES

bad = 0
for s in (x for x in CATALOG if x["source"] != "derivado"):
    try:
        print("OK  ", s["id"], "->", SOURCES[s["source"]].validate(s))
    except Exception as exc:
        bad += 1
        print("FAIL", s["id"], exc)
sys.exit(1 if bad else 0)
