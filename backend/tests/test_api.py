from fastapi.testclient import TestClient

from app.main import app

TAG = "PDO.F1.COMP-02.VIB_DE"


def test_fleet_endpoints():
    with TestClient(app) as c:  # runs startup: seed + backfill + first run
        assets = c.get("/assets").json()
        assert len(assets) == 5
        by_id = {a["id"]: a for a in assets}
        assert by_id["comp-02"]["status"] == "degrading" and len(by_id["comp-02"]["trend"]) > 10
        assert by_id["pump-01"]["status"] == "normal"
        s = c.get("/summary").json()
        assert s["asset_count"] == 5 and sum(s["status_counts"].values()) == 5

        d = c.get("/assets/comp-02").json()
        assert len(d["sensors"]) == 4 and all(x["score"] is not None for x in d["sensors"])
        assert len(c.get("/assets/comp-02/health/history").json()) > 10

        ts = c.get("/assets/comp-02/timeseries", params={"tag": TAG}).json()
        assert len(ts) > 400 and ts[-1]["value"] > ts[0]["value"]


def test_404s():
    with TestClient(app) as c:
        assert c.get("/assets/nope").status_code == 404
        assert c.get("/assets/comp-02/timeseries", params={"tag": "X"}).status_code == 404
