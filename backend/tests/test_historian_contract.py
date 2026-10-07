"""Run against EVERY HistorianClient implementation (add new ones to IMPLEMENTATIONS)."""
from datetime import datetime, timedelta, timezone

import pytest

from app.historian.mock import MockHistorian

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
TAG = "PDO.F1.COMP-02.VIB_DE"
IMPLEMENTATIONS = [lambda: MockHistorian(clock=lambda: NOW)]


@pytest.fixture(params=IMPLEMENTATIONS)
def hist(request):
    return request.param()


def test_recorded_ascending_utc(hist):
    s = hist.get_recorded(TAG, NOW - timedelta(hours=2), NOW)
    assert len(s) > 100
    assert all(x.timestamp.tzinfo is not None and x.timestamp.utcoffset() == timedelta(0) for x in s)
    assert [x.timestamp for x in s] == sorted(x.timestamp for x in s)


def test_unknown_tag_raises(hist):
    with pytest.raises(KeyError):
        hist.get_recorded("NOPE", NOW - timedelta(hours=1), NOW)
    with pytest.raises(KeyError):
        hist.get_interpolated("NOPE", NOW - timedelta(hours=1), NOW, timedelta(minutes=5))


def test_max_count(hist):
    assert len(hist.get_recorded(TAG, NOW - timedelta(days=1), NOW, max_count=10)) == 10


def test_interpolated_spacing(hist):
    s = hist.get_interpolated(TAG, NOW - timedelta(hours=1), NOW, timedelta(minutes=10))
    assert len(s) == 7
    assert s[1].timestamp - s[0].timestamp == timedelta(minutes=10)


def test_current_and_list(hist):
    assert hist.get_current([TAG])[TAG].tag == TAG
    assert TAG in [t.tag for t in hist.list_tags("PDO.F1.COMP")]
