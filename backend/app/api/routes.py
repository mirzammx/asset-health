from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset, HealthSnapshot
from app.db.session import get_session
from app.historian.base import HistorianClient
from app.historian.factory import get_historian

router = APIRouter()

MAX_TREND_POINTS = 60


def _iso(dt: datetime) -> str:
    return dt.replace(tzinfo=timezone.utc).isoformat()  # DB stores naive UTC


def _latest(session: Session, asset_id: str) -> HealthSnapshot | None:
    return session.scalar(
        select(HealthSnapshot).where(HealthSnapshot.asset_id == asset_id).order_by(HealthSnapshot.ts.desc()).limit(1)
    )


def _history(session: Session, asset_id: str, days: int) -> list[HealthSnapshot]:
    since = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=days)
    return list(session.scalars(
        select(HealthSnapshot).where(HealthSnapshot.asset_id == asset_id, HealthSnapshot.ts >= since)
        .order_by(HealthSnapshot.ts)
    ))


def _downsample(rows: list, limit: int) -> list:
    if len(rows) <= limit:
        return rows
    stride = len(rows) / limit
    picked = [rows[int(i * stride)] for i in range(limit)]
    picked[-1] = rows[-1]  # always keep the newest point
    return picked


def _asset_or_404(session: Session, asset_id: str) -> Asset:
    asset = session.get(Asset, asset_id)
    if asset is None:
        raise HTTPException(404, f"Unknown asset {asset_id}")
    return asset


def _health_view(snap: HealthSnapshot | None) -> dict:
    if snap is None:
        return {"health_index": None, "status": "unknown", "as_of": None}
    return {"health_index": snap.health_index, "status": snap.status, "as_of": _iso(snap.ts)}


@router.get("/assets")
def list_assets(session: Session = Depends(get_session)):
    out = []
    for a in session.scalars(select(Asset).order_by(Asset.id)):
        trend = [r.health_index for r in _downsample(_history(session, a.id, 14), MAX_TREND_POINTS)]
        out.append({"id": a.id, "name": a.name, "type": a.type, "area": a.area,
                    **_health_view(_latest(session, a.id)), "trend": trend})
    return out


@router.get("/summary")
def summary(session: Session = Depends(get_session)):
    assets = list_assets(session)
    scored = [a["health_index"] for a in assets if a["health_index"] is not None]
    counts = {"normal": 0, "degrading": 0, "attention": 0, "unknown": 0}
    for a in assets:
        counts[a["status"]] += 1
    return {"asset_count": len(assets), "avg_health": round(sum(scored) / len(scored), 1) if scored else None,
            "status_counts": counts}


@router.get("/assets/{asset_id}")
def asset_detail(asset_id: str, session: Session = Depends(get_session)):
    asset = _asset_or_404(session, asset_id)
    snap = _latest(session, asset_id)
    by_tag = {d["tag"]: d for d in (snap.details if snap else [])}
    sensors = []
    for s in asset.sensors:
        d = by_tag.get(s.tag, {})
        sensors.append({"tag": s.tag, "kind": s.kind, "unit": s.unit, "baseline": s.baseline_mean,
                        "alarm_limit": s.alarm_limit, "level": d.get("level"),
                        "score": d.get("score"), "status": d.get("status", "unknown")})
    return {"id": asset.id, "name": asset.name, "type": asset.type, "site": asset.site, "area": asset.area,
            **_health_view(snap), "sensors": sensors}


@router.get("/assets/{asset_id}/health/history")
def health_history(asset_id: str, days: int = 14, session: Session = Depends(get_session)):
    _asset_or_404(session, asset_id)
    rows = _downsample(_history(session, asset_id, days), 300)
    return [{"t": _iso(r.ts), "health_index": r.health_index} for r in rows]


@router.get("/assets/{asset_id}/timeseries")
def timeseries(asset_id: str, tag: str, hours: int = 240, interval_minutes: int = 30,
               session: Session = Depends(get_session), h: HistorianClient = Depends(get_historian)):
    asset = _asset_or_404(session, asset_id)
    if tag not in [s.tag for s in asset.sensors]:
        raise HTTPException(404, f"Tag {tag} not on asset {asset_id}")
    end = datetime.now(timezone.utc)
    samples = h.get_interpolated(tag, end - timedelta(hours=hours), end, timedelta(minutes=interval_minutes))
    return [{"t": s.timestamp.isoformat(), "value": s.value, "quality": s.quality} for s in samples]
