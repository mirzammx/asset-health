"""Health index: how far the recent signal has moved from healthy baseline toward its alarm limit."""
from dataclasses import dataclass
from statistics import median

from app.historian.base import Quality, Sample


@dataclass(frozen=True)
class HealthResult:
    health_index: float | None  # 0-100, None if there is no usable data
    status: str  # normal | degrading | attention | unknown
    level: float | None  # the robust recent value used


@dataclass(frozen=True)
class SensorHealth:
    tag: str
    kind: str
    weight: float
    health: HealthResult


def status_for(health: float) -> str:
    if health >= 75:
        return "normal"
    if health >= 50:
        return "degrading"
    return "attention"


def compute_health(samples: list[Sample], baseline: float, alarm_limit: float) -> HealthResult:
    """One sensor. Uses the median so a single spike doesn't tank the score; ignores bad-quality samples."""
    good = [s.value for s in samples if s.quality == Quality.GOOD and s.value is not None]
    if not good:
        return HealthResult(None, "unknown", None)
    level = median(good)
    frac = (level - baseline) / (alarm_limit - baseline)
    health = round(100 * (1 - min(max(frac, 0.0), 1.0)), 1)
    return HealthResult(health, status_for(health), round(level, 3))


WORST_SENSOR_SHARE = 0.7


def combine(sensors: list[SensorHealth]) -> HealthResult:
    """Asset score = 70% worst sensor + 30% weighted average.

    The worst sensor dominates because one failing signal (e.g. vibration) means a failing asset,
    even if the rest look fine. The average term keeps several mildly drifting sensors visible.
    """
    scored = [s for s in sensors if s.health.health_index is not None]
    if not scored:
        return HealthResult(None, "unknown", None)
    worst = min(s.health.health_index for s in scored)
    total_w = sum(s.weight for s in scored)
    avg = sum(s.health.health_index * s.weight for s in scored) / total_w
    health = round(WORST_SENSOR_SHARE * worst + (1 - WORST_SENSOR_SHARE) * avg, 1)
    return HealthResult(health, status_for(health), None)
