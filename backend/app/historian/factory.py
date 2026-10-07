import os
from functools import lru_cache

from app.historian.base import HistorianClient


@lru_cache
def get_historian() -> HistorianClient:
    kind = os.environ.get("HISTORIAN", "mock")
    if kind == "mock":
        from app.historian.mock import MockHistorian
        return MockHistorian()
    if kind == "pi":
        from app.historian.pi_web_api import PIWebApiHistorian
        return PIWebApiHistorian()
    raise ValueError(f"Unknown HISTORIAN={kind!r} (expected 'mock' or 'pi')")
