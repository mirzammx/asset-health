"""Building blocks for simulated storylines. All times are relative to "now" so the demo is always current."""
import math
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Degradation:
    """Asset-level wear. progress() is 0 at start and 1 when the most sensitive sensor hits its alarm limit."""
    start_hours_ago: float
    hours_to_limit: float  # hours from start until progress == 1
    k: float  # growth rate; small k ~ linear, larger k ~ accelerating

    def progress(self, hours_since_start: float) -> float:
        if hours_since_start <= 0:
            return 0.0
        p = (math.exp(self.k * hours_since_start) - 1) / (math.exp(self.k * self.hours_to_limit) - 1)
        return min(p, 1.2)


@dataclass(frozen=True)
class Failure:
    """The asset trips at hours_ago, stays down for repair_hours, then returns to healthy."""
    hours_ago: float
    repair_hours: float


@dataclass(frozen=True)
class Fault:
    """An injected data problem on one sensor: spike | flatline | dropout."""
    kind: str
    start_hours_ago: float
    duration_hours: float
    magnitude: float = 0.0  # spikes only


@dataclass(frozen=True)
class TagSpec:
    description: str
    kind: str
    unit: str
    baseline: float
    alarm_limit: float
    daily_amp: float
    noise: float
    sensitivity: float  # share of the asset's degradation that shows up on this sensor
    trip_value: float  # reading while the asset is tripped
    degradation: Degradation | None = None
    failure: Failure | None = None
    faults: tuple[Fault, ...] = field(default_factory=tuple)
