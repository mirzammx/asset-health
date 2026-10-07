"""The simulated plant: 5 assets, their sensors and storylines.

Also used to seed the app DB. In a real deployment the asset register would come from
the customer's system; only the mock historian would be replaced.
"""
from dataclasses import dataclass

from app.mock.scenarios import Degradation, Failure, Fault, TagSpec

SITE, AREA = "PDO", "F1"


@dataclass(frozen=True)
class SensorDef:
    key: str  # tag suffix, e.g. VIB_DE
    kind: str
    unit: str
    baseline: float
    alarm_limit: float
    weight: float
    sensitivity: float
    daily_amp: float
    noise: float
    description: str
    trip_value: float = 0.0


@dataclass(frozen=True)
class AssetDef:
    id: str
    name: str
    type: str
    sensors: tuple[SensorDef, ...]
    degradation: Degradation | None = None
    failure: Failure | None = None
    faults: dict[str, tuple[Fault, ...]] | None = None  # sensor key -> faults

    def tag(self, key: str) -> str:
        return f"{SITE}.{AREA}.{self.id.upper()}.{key}"


def vib(baseline=2.0, key="VIB_DE", desc="Drive-end vibration", sens=1.0) -> SensorDef:
    return SensorDef(key, "vibration", "mm/s", baseline, 7.1, 0.40, sens, 0.12, 0.07, desc)


def temp(baseline=65.0, alarm=100.0, key="TEMP_DE", desc="Drive-end temperature", sens=0.6) -> SensorDef:
    return SensorDef(key, "temperature", "°C", baseline, alarm, 0.25, sens, 1.5, 0.6, desc, trip_value=25.0)


def curr(baseline=45.0, alarm=65.0, desc="Motor current", sens=0.25) -> SensorDef:
    return SensorDef("CURR", "current", "A", baseline, alarm, 0.15, sens, 2.0, 0.5, desc)


def press(baseline=12.0, alarm=16.0, key="PRESS_DIS", desc="Discharge pressure", sens=0.0) -> SensorDef:
    return SensorDef(key, "pressure", "bar", baseline, alarm, 0.20, sens, 0.3, 0.08, desc)


ASSETS: tuple[AssetDef, ...] = (
    AssetDef("pump-01", "Pump-01", "pump",
             (vib(1.8), temp(55, 95), curr(), press()),
             faults={  # one-off spikes: health must NOT react to these
                 "TEMP_DE": (Fault("spike", 30, 0.03, 40), Fault("spike", 100, 0.03, 40)),
                 "VIB_DE": (Fault("spike", 12, 0.02, 6),),
             }),
    AssetDef("comp-02", "Compressor-02", "compressor",
             (vib(2.0), temp(68, 105), curr(52, 75), press(14, 19)),
             degradation=Degradation(start_hours_ago=240, hours_to_limit=560, k=0.0008)),
    AssetDef("gear-03", "Gearbox-03", "gearbox",
             (vib(2.0), temp(60, 95), curr(38, 55)),
             degradation=Degradation(start_hours_ago=288, hours_to_limit=438, k=0.0006)),
    AssetDef("motor-04", "Motor-04", "motor",
             (vib(1.5), temp(60, 110), curr(80, 110)),
             degradation=Degradation(start_hours_ago=264, hours_to_limit=144, k=0.015),
             failure=Failure(hours_ago=120, repair_hours=12)),
    AssetDef("well-05", "Wellhead-05", "wellhead",
             (press(150, 210, "PRESS_WH", "Wellhead pressure"),
              temp(48, 85, "TEMP_WH", "Wellhead temperature", 0.0),
              vib(1.2, "VIB_CHOKE", "Choke vibration", 0.0)),
             faults={
                 "PRESS_WH": (Fault("flatline", 6, 6),),  # stuck sensor, quality still GOOD
                 "VIB_CHOKE": (Fault("dropout", 3, 2.5), Fault("dropout", 50, 5)),  # comm loss -> BAD
             }),
)

ASSETS_BY_ID = {a.id: a for a in ASSETS}


def _build_tags() -> dict[str, TagSpec]:
    tags: dict[str, TagSpec] = {}
    for a in ASSETS:
        for s in a.sensors:
            tags[a.tag(s.key)] = TagSpec(
                f"{a.name} {s.description.lower()}", s.kind, s.unit, s.baseline, s.alarm_limit,
                s.daily_amp, s.noise, s.sensitivity, s.trip_value,
                a.degradation, a.failure, (a.faults or {}).get(s.key, ()),
            )
    return tags


TAGS: dict[str, TagSpec] = _build_tags()
