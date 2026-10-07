from datetime import datetime, timedelta, timezone

from app.historian.base import Quality, Sample
from app.historian.mock import MockHistorian
from app.processing.health import compute_health

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
H = MockHistorian(clock=lambda: NOW)
COMP, PUMP = "PDO.F1.COMP-02.VIB_DE", "PDO.F1.PUMP-01.VIB_DE"


def health(tag, base, end):
    return compute_health(H.get_recorded(tag, end - timedelta(hours=1), end), base, 7.1)


def test_healthy_asset_scores_high():
    assert health(PUMP, 2.0, NOW).health_index >= 90


def test_compressor_early_vs_now():
    early = health(COMP, 2.0, NOW - timedelta(hours=240))  # before drift began
    now = health(COMP, 2.0, NOW)
    assert early.health_index >= 90
    assert now.health_index < 70
    assert now.status in ("degrading", "attention")


def test_bad_quality_ignored_and_empty_is_unknown():
    bad = [Sample("t", NOW, None, Quality.BAD)]
    assert compute_health(bad, 2.0, 7.1).status == "unknown"
    spike = [Sample("t", NOW, 2.0, Quality.GOOD)] * 20 + [Sample("t", NOW, 50.0, Quality.GOOD)]
    assert compute_health(spike, 2.0, 7.1).health_index == 100
