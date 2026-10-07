from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from app.db.models import Base, HealthSnapshot
from app.db.seed import seed_assets
from app.historian.mock import MockHistorian
from app.processing.runner import backfill, run_once

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
H = MockHistorian(clock=lambda: NOW)


def make_session():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    s = sessionmaker(engine)()
    seed_assets(s)
    return s


def health_of(session, asset_id, at):
    run_once(session, H, at)
    ts = at.replace(tzinfo=None)
    return session.scalar(select(HealthSnapshot).where(HealthSnapshot.asset_id == asset_id, HealthSnapshot.ts == ts))


def test_expected_statuses_now():
    s = make_session()
    run_once(s, H, NOW)
    got = {r.asset_id: (r.status, r.health_index) for r in s.scalars(select(HealthSnapshot))}
    assert got["pump-01"][0] == "normal" and got["pump-01"][1] >= 90
    assert got["comp-02"][0] == "degrading"
    assert got["gear-03"][0] == "attention"
    assert got["motor-04"][1] >= 90  # repaired, healthy again
    assert got["well-05"][0] == "normal"


def test_motor_degrades_then_recovers():
    s = make_session()
    before_failure = health_of(s, "motor-04", NOW - timedelta(hours=122)).health_index
    healthy_early = health_of(s, "motor-04", NOW - timedelta(hours=270)).health_index
    after_repair = health_of(s, "motor-04", NOW - timedelta(hours=60)).health_index
    assert healthy_early >= 90 and before_failure < 20 and after_repair >= 90


def test_pump_spikes_do_not_move_health():
    s = make_session()
    baseline = health_of(s, "pump-01", NOW - timedelta(hours=14)).health_index
    after_spike = health_of(s, "pump-01", NOW - timedelta(hours=12) + timedelta(minutes=5)).health_index
    assert abs(baseline - after_spike) <= 5


def test_wellhead_dropouts_do_not_move_health():
    s = make_session()
    normal = health_of(s, "well-05", NOW - timedelta(hours=5)).health_index
    in_dropout = health_of(s, "well-05", NOW - timedelta(hours=1)).health_index
    assert in_dropout is not None and abs(normal - in_dropout) <= 5


def test_run_once_is_idempotent_and_backfill_fills():
    s = make_session()
    run_once(s, H, NOW)
    n = s.scalar(select(func.count()).select_from(HealthSnapshot))
    run_once(s, H, NOW)
    assert s.scalar(select(func.count()).select_from(HealthSnapshot)) == n == 5
    backfill(s, H, days=1, step_hours=6, end=NOW)
    assert s.scalar(select(func.count()).select_from(HealthSnapshot)) > n
