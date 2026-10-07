"""Reads the historian, computes health, writes health_snapshots. The API never calls this directly."""
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Asset, HealthSnapshot
from app.historian.base import HistorianClient
from app.processing.health import SensorHealth, combine, compute_health

WINDOW = timedelta(hours=1)


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(second=0, microsecond=0)


def process_asset(session: Session, historian: HistorianClient, asset: Asset, at: datetime) -> HealthSnapshot:
    sensor_results = []
    for s in asset.sensors:
        samples = historian.get_recorded(s.tag, at - WINDOW, at)
        sensor_results.append(SensorHealth(s.tag, s.kind, s.weight, compute_health(samples, s.baseline_mean, s.alarm_limit)))
    result = combine(sensor_results)
    return HealthSnapshot(
        asset_id=asset.id, ts=at.astimezone(timezone.utc).replace(tzinfo=None),
        health_index=result.health_index, status=result.status,
        details=[{"tag": r.tag, "kind": r.kind, "level": r.health.level,
                  "score": r.health.health_index, "status": r.health.status} for r in sensor_results],
    )


def run_once(session: Session, historian: HistorianClient, at: datetime | None = None) -> None:
    """Compute a snapshot for every asset at time `at`. Re-running for the same `at` replaces, never duplicates."""
    at = at or utc_now()
    for asset in session.scalars(select(Asset)):
        snap = process_asset(session, historian, asset, at)
        session.execute(delete(HealthSnapshot).where(HealthSnapshot.asset_id == asset.id, HealthSnapshot.ts == snap.ts))
        session.add(snap)
    session.commit()


def backfill(session: Session, historian: HistorianClient, days: int = 14, step_hours: int = 3,
             end: datetime | None = None) -> None:
    """Fill history so trend sparklines have something to show on first start."""
    end = end or utc_now()
    t = end - timedelta(days=days)
    while t < end:
        run_once(session, historian, t)
        t += timedelta(hours=step_hours)
