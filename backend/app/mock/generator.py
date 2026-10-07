"""Pure, deterministic signal model. Same inputs -> same output, so tests and demos are reproducible."""
import math
import random
from datetime import datetime

from app.historian.base import Quality
from app.mock.scenarios import TagSpec


def _noise(tag: str, t: datetime, std: float) -> float:
    minute = int(t.timestamp() // 60)
    return random.Random(f"{tag}:{minute}").gauss(0.0, std)


def value(spec: TagSpec, tag: str, t: datetime, now: datetime) -> tuple[float | None, Quality]:
    hours_ago = (now - t).total_seconds() / 3600

    # injected data faults that replace the reading entirely
    for f in spec.faults:
        active = f.start_hours_ago - f.duration_hours <= hours_ago <= f.start_hours_ago
        if active and f.kind == "dropout":
            return None, Quality.BAD
        if active and f.kind == "flatline":
            return spec.baseline, Quality.GOOD  # stuck at a constant, but looks fine to the system

    # asset tripped: failure -> repair window
    fl = spec.failure
    if fl and fl.hours_ago - fl.repair_hours <= hours_ago <= fl.hours_ago:
        return spec.trip_value, Quality.GOOD

    hour_of_day = (t.hour + t.minute / 60) / 24
    v = spec.baseline + spec.daily_amp * math.sin(2 * math.pi * hour_of_day)
    v += _noise(tag, t, spec.noise)

    d = spec.degradation
    wearing = d is not None and (fl is None or hours_ago > fl.hours_ago)  # wear resets after repair
    if wearing:
        p = d.progress(d.start_hours_ago - hours_ago)
        v += spec.sensitivity * p * (spec.alarm_limit - spec.baseline)

    for f in spec.faults:
        if f.kind == "spike" and f.start_hours_ago - f.duration_hours <= hours_ago <= f.start_hours_ago:
            v += f.magnitude
    return v, Quality.GOOD
