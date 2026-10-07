from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Asset, Sensor
from app.mock.fleet import ASSETS, AREA, SITE


def seed_assets(session: Session) -> None:
    """Insert the demo plant if the assets table is empty."""
    if session.scalar(select(Asset.id).limit(1)):
        return
    for a in ASSETS:
        asset = Asset(id=a.id, name=a.name, type=a.type, site=SITE, area=AREA)
        asset.sensors = [
            Sensor(tag=a.tag(s.key), kind=s.kind, unit=s.unit, baseline_mean=s.baseline,
                   alarm_limit=s.alarm_limit, weight=s.weight)
            for s in a.sensors
        ]
        session.add(asset)
    session.commit()
