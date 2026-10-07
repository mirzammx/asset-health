"""The historian boundary. Everything above this package depends only on these types."""
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol


class Quality(str, Enum):
    GOOD = "good"
    UNCERTAIN = "uncertain"  # questionable / substituted
    BAD = "bad"  # comm loss or sensor fault; value may be None


@dataclass(frozen=True)
class Sample:
    tag: str  # e.g. "PDO.F1.COMP-02.VIB_DE"
    timestamp: datetime  # timezone-aware, UTC
    value: float | None  # None allowed when quality == BAD
    quality: Quality


@dataclass(frozen=True)
class TagInfo:
    tag: str
    description: str
    unit: str


class HistorianClient(Protocol):
    def list_tags(self, prefix: str | None = None) -> list[TagInfo]: ...

    def get_current(self, tags: list[str]) -> dict[str, Sample]: ...

    def get_recorded(
        self, tag: str, start: datetime, end: datetime, max_count: int = 10_000
    ) -> list[Sample]:
        """Raw stored samples in [start, end], ascending, at most max_count."""
        ...

    def get_interpolated(
        self, tag: str, start: datetime, end: datetime, interval: timedelta
    ) -> list[Sample]:
        """Evenly spaced samples from start to end (inclusive)."""
        ...
