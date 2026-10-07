from datetime import datetime, timedelta, timezone
from typing import Callable

from app.historian.base import Sample, TagInfo
from app.mock import generator
from app.mock.fleet import TAGS

_MINUTE = timedelta(minutes=1)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(second=0, microsecond=0)


class MockHistorian:
    """Implements HistorianClient on top of the simulated signal model."""

    def __init__(self, clock: Callable[[], datetime] = _utc_now):
        self._clock = clock

    def _spec(self, tag: str):
        try:
            return TAGS[tag]
        except KeyError:
            raise KeyError(f"Unknown tag: {tag}") from None

    def _sample(self, tag: str, t: datetime) -> Sample:
        v, q = generator.value(self._spec(tag), tag, t, self._clock())
        return Sample(tag, t, v, q)

    def list_tags(self, prefix: str | None = None) -> list[TagInfo]:
        return [
            TagInfo(tag, s.description, s.unit)
            for tag, s in TAGS.items()
            if prefix is None or tag.startswith(prefix)
        ]

    def get_current(self, tags: list[str]) -> dict[str, Sample]:
        now = self._clock()
        return {tag: self._sample(tag, now) for tag in tags}

    def get_recorded(self, tag, start, end, max_count=10_000):
        self._spec(tag)
        # raw samples are stored on the minute grid
        t = start.replace(second=0, microsecond=0)
        if t < start:
            t += _MINUTE
        out: list[Sample] = []
        while t <= end and len(out) < max_count:
            out.append(self._sample(tag, t))
            t += _MINUTE
        return out

    def get_interpolated(self, tag, start, end, interval):
        self._spec(tag)
        out: list[Sample] = []
        t = start
        while t <= end:
            out.append(self._sample(tag, t))
            t += interval
        return out
