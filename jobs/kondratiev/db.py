"""Schema and idempotent upserts. SQLite locally, Postgres (Supabase) in production."""
import os
from sqlalchemy import (Boolean, Column, Date, DateTime, Float, Integer, MetaData, String, Table, Text,
                        create_engine, func, select)
from sqlalchemy.dialects import postgresql, sqlite

md = MetaData()

series_catalog = Table(
    "series_catalog", md,
    Column("id", String, primary_key=True),
    Column("perspective", String, nullable=False),
    Column("layer", String, nullable=False),          # structure | regime | timing
    Column("source", String, nullable=False),
    Column("code", String, nullable=False),
    Column("name", String, nullable=False),
    Column("country", String),
    Column("unit", String),
    Column("frequency", String, nullable=False),
    Column("transform", String),
    Column("role", String),                           # procyclical | fragility | valuation_excess
    Column("rationale", Text),
    Column("source_url", String),
    Column("stale_after_days", Integer, nullable=False),
)
observations = Table(
    "observations", md,
    Column("series_id", String, primary_key=True),
    Column("ref_date", Date, primary_key=True),
    Column("vintage", String, primary_key=True, default="latest"),
    Column("value", Float, nullable=False),
    Column("as_of", DateTime, nullable=False),
    Column("is_provisional", Boolean, default=False),
)
derived = Table(
    "derived", md,
    Column("series_id", String, primary_key=True), Column("date", Date, primary_key=True),
    Column("trend", Float), Column("cycle_gap", Float), Column("percentile", Float),
    Column("zscore", Float), Column("momentum", Float), Column("acceleration", Float),
)
scores = Table(
    "scores", md,
    Column("date", Date, primary_key=True), Column("perspective", String, primary_key=True),
    Column("methodology_version", String, primary_key=True),
    Column("state", String), Column("value", Float), Column("coverage", Float), Column("uncertainty", Float),
)
runs = Table(
    "runs", md,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("source", String, nullable=False),
    Column("started_at", DateTime, nullable=False),
    Column("finished_at", DateTime),
    Column("status", String, nullable=False),         # ok | partial | failed
    Column("rows", Integer, default=0),
    Column("error", Text),
)


def get_engine(url=None):
    url = url or os.environ.get("DATABASE_URL", "sqlite:///kondratiev.db")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_engine(url)
    md.create_all(engine)
    return engine


def _insert(engine, table):
    return (postgresql if engine.dialect.name == "postgresql" else sqlite).insert(table)


def upsert(engine, table, rows, keys):
    """Insert rows; on key conflict update the other columns. Idempotent."""
    if not rows:
        return 0
    with engine.begin() as c:
        stmt = _insert(engine, table).values(rows)
        update = {k: stmt.excluded[k] for k in rows[0] if k not in keys}
        c.execute(stmt.on_conflict_do_update(index_elements=keys, set_=update))
    return len(rows)


def latest_ref_date(engine, series_id):
    with engine.connect() as c:
        return c.execute(select(func.max(observations.c.ref_date)).where(observations.c.series_id == series_id)).scalar()
