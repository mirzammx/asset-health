# Asset Health & Predictive Maintenance — Architecture (Step 1 analysis)

Status: **DRAFT, awaiting approval.** No application code exists yet.
Source of requirements: the Rug-Rel infographic (`docs/requirements.md` is empty).

---

## 1. Current project structure

```
asset-health/
├── .git/            (initialised, no commits, no remote)
└── docs/
    └── requirements.md   (EMPTY, 0 bytes)
```

## 2. Tech stack, dependencies, entry points

None. No `package.json`, `pyproject.toml`, lockfile, or source files.

## 3. Database and UI/component system

None.

## 4. Usable / missing

Repo is empty. Only the git init and the `docs/` folder are usable. Everything else is missing.

## 5. Ambiguities → questions, with my default assumption

| # | Question | Assumption I'll make |
|---|----------|----------------------|
| 1 | `requirements.md` is empty. Is the infographic the full spec? | Yes. Requirements derived from it (below). Please paste anything extra into the file. |
| 2 | Which assets? | 5 assets: Pump-01, Compressor-02, Gearbox-03 (named in the infographic), plus Motor-04 and Wellhead-05. |
| 3 | Which sensors per asset? | 4–5 each, from the infographic: vibration, temperature, pressure, current/power, runtime/cycles. Not every asset has every type. |
| 4 | Sample rate / history | 1 sample/min, 14 days of history, ~600k points total. |
| 5 | Target | Local demo (backend + frontend on one laptop). Rug-Rel edge computer is out of scope. |
| 6 | Health index meaning | 0–100 score. Status bands: ≥75 Normal, 50–75 Degrading, <50 Attention (matches 82/61/38 in the infographic). |
| 7 | RUL units / confidence | Hours, shown with a simple uncertainty range; shown as ">N hrs" when far out. |
| 8 | "Fault classification" | Rule-based labels (e.g. "bearing wear", "overheating") from which sensors drifted. No trained classifier. |
| 9 | "Action" column (maintenance planning, early warning) | MVP = alerts + a "recommended action" text per fault. No work orders or scheduling. |
| 10 | Users / auth | Single user, no login. |
| 11 | Live vs historical | Dashboard polls the API every few seconds. Mock "now" = real clock. No WebSockets. |
| 12 | Is the Python/React split OK for you? | Yes (see stack decision). |

## 6. Recommended architecture

### Decisions (2 options each, my pick marked ★)

| Decision | Option A | Option B | Pick |
|----------|----------|----------|------|
| **Stack** | ★ Python **FastAPI** backend + **React (Vite) + Recharts** frontend | Streamlit, all Python, single app | **A**. Python is the natural home for signal/health/RUL code and for a future PI connector. FastAPI gives auto-generated API docs at `/docs`, so you can test without a UI. The separate API layer matches your pipeline (Application API → Dashboard). B is faster for chart #1 but blurs layers and looks less like a product. |
| **Database** | ★ **SQLite** (via SQLAlchemy) | PostgreSQL / TimescaleDB | **A**. Zero setup, a single file, plenty for ~600k points. SQLAlchemy means switching to Postgres later is a config change. B is overkill for 2 days. |
| **Where raw data lives** | ★ Only in the **historian** (mock). The app DB stores assets, computed health, alerts. | Copy all raw samples into the app DB | **A**. This mirrors reality: PI owns raw data, and you never duplicate it. It's also why the historian interface matters. |
| **RUL method** | see §11 | | Trend extrapolation |

### Pipeline

```
 [Mock generator]  ← replaceable →  [PI Web API connector]   (both implement HistorianClient)
        │                                    │
        └────────────────┬───────────────────┘
                         ▼
              Data Retrieval Layer   (historian/  — the ONLY code that knows about PI vs mock)
                         ▼
        Health / RUL Processing      (processing/  — features → health → RUL → faults → alerts)
                         ▼
                 App DB (SQLite)     (assets, health_snapshots, alerts)
                         ▼
                 Application API     (FastAPI, reads DB, serves JSON)
                         ▼
                 Dashboard           (React)
```

**Key architectural decision (plain terms):** processing is a *separate step* from the API. A job reads the historian, computes health/RUL, and writes results to the DB. The API only reads the DB. This keeps the dashboard fast, and lets you test health logic without a web server. For the demo the job runs on startup and on a timer (every 30–60 s).

**Swap rule:** code above `historian/` imports only the `HistorianClient` protocol and gets an instance from `historian/factory.py`, chosen by one env var `HISTORIAN=mock|pi`.

## 7. Recommended folder structure

```
asset-health/
├── docs/                      requirements.md, architecture.md
├── backend/
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py            FastAPI app, startup, scheduler
│   │   ├── config.py          env settings (HISTORIAN=mock|pi, thresholds)
│   │   ├── api/               routes: assets, health, timeseries, alerts
│   │   ├── historian/         ★ the boundary
│   │   │   ├── base.py          Sample, Quality, HistorianClient (Protocol)
│   │   │   ├── mock.py          MockHistorian (uses mock/)
│   │   │   ├── pi_web_api.py    stub only (raises NotImplementedError) in MVP
│   │   │   └── factory.py
│   │   ├── mock/              scenarios.py (per-asset storyline), generator.py (pure functions)
│   │   ├── processing/        features.py, health.py, rul.py, faults.py, runner.py
│   │   └── db/                models.py, session.py, seed.py
│   └── tests/                 test_historian_contract.py, test_health.py, test_rul.py
└── frontend/
    ├── package.json
    └── src/
        ├── api/               typed fetch client
        ├── components/        HealthGauge, AssetCard, TrendChart, AlertList
        └── pages/             FleetOverview, AssetDetail
```

## 8. Database entities

| Entity | Key fields | Relationships |
|--------|-----------|---------------|
| `assets` | id, name, type (pump/compressor/gearbox/motor/wellhead), site, area | has many `sensors`, `health_snapshots`, `alerts`, `failure_events` |
| `sensors` | id, asset_id, tag (historian tag), kind (vibration/temp/pressure/current/runtime), unit, baseline_mean, baseline_std, alarm_limit, weight | belongs to `assets` |
| `health_snapshots` | id, asset_id, ts, health_index (0–100), status, rul_hours, rul_low, rul_high, fault_label, details_json (per-sensor contribution) | belongs to `assets` |
| `alerts` | id, asset_id, ts, severity, fault_label, message, recommended_action, acknowledged | belongs to `assets` |
| `failure_events` | id, asset_id, ts, description | belongs to `assets`. **Ground truth** (from the mock scenario / maintenance history), used to validate RUL |

Not stored: raw samples (historian owns them).

## 9. Historian interface

Python, in `historian/base.py`. Modelled on PI Web API so the future connector is a thin adapter (the PI connector would resolve tag → WebId internally, and map `Quality` from PI's `Good`/`Questionable`/`Substituted` flags).

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol

class Quality(str, Enum):
    GOOD = "good"
    UNCERTAIN = "uncertain"   # questionable / substituted
    BAD = "bad"               # comm loss, sensor fault; value may be None

@dataclass(frozen=True)
class Sample:
    tag: str                  # e.g. "PDO.F1.PUMP-01.VIB_DE"
    timestamp: datetime       # timezone-aware, UTC
    value: float | None       # None allowed when quality == BAD
    quality: Quality

@dataclass(frozen=True)
class TagInfo:
    tag: str
    description: str
    unit: str

class HistorianClient(Protocol):
    def list_tags(self, prefix: str | None = None) -> list[TagInfo]: ...

    def get_current(self, tags: list[str]) -> dict[str, Sample]: ...

    def get_recorded(self, tag: str, start: datetime, end: datetime,
                     max_count: int = 10_000) -> list[Sample]: ...
        # raw stored samples, ascending by timestamp, [start, end]

    def get_interpolated(self, tag: str, start: datetime, end: datetime,
                         interval: timedelta) -> list[Sample]: ...
        # evenly spaced samples; use for charts and fixed-window features
```

Contract rules (enforced by one shared test, `test_historian_contract.py`, run against every implementation):
1. Timestamps are tz-aware UTC and ascending.
2. Unknown tag → `KeyError`.
3. BAD samples are returned, not dropped. Processing decides what to do with them.
4. `get_recorded` never returns more than `max_count`.

Tag naming: `SITE.AREA.ASSET.SENSOR`, e.g. `PDO.F1.COMP-02.TEMP_DE`.

## 10. Mock data design

The generator is a **pure, deterministic function** `value(tag, t)` (seeded per tag). No storage needed, and results are reproducible for tests. `MockHistorian` just samples it on a 1-min grid.

Signal model per sensor: `baseline + daily load cycle + slow noise + white noise`, then layer **scenario effects**:

| Layer | How it's simulated | What it tests |
|-------|-------------------|---------------|
| Normal operation | Stable mean with diurnal load variation (vibration/current rise with load) | No false alarms; health stays ~80–100 |
| Gradual degradation | From `t_start`, drift grows exponentially: `x += a·(e^{k(t−t_start)} − 1)` on affected sensors (vibration first, temperature lagging) | Health decline and RUL slope |
| Injected faults | Short spikes, step change, flatline (stuck sensor), dropout windows with `quality=BAD` | Robustness: spikes shouldn't tank health; bad data is ignored |
| Failure event | At `t_fail` the signal hits alarm limit, then trip: current/runtime → 0, then back to baseline after a "repair" gap. A `failure_events` row is recorded. | RUL accuracy: predicted vs actual time-to-failure |

Asset storylines (so the demo has contrast, mirroring the infographic):

| Asset | Storyline | Expected demo state |
|-------|-----------|---------------------|
| Pump-01 | Healthy | 82%+ Normal, RUL ">1000 hrs" |
| Compressor-02 | Degradation started ~10 days ago | ~61% Degrading, RUL ~300 hrs |
| Gearbox-03 | Late-stage degradation | ~38% Attention, RUL ~150 hrs, active alert |
| Motor-04 | Ran to failure 5 days ago, repaired | Chart shows full degrade → fail → recover cycle; RUL backtest |
| Wellhead-05 | Healthy but with stuck-sensor and dropouts | Data-quality handling; no false alert |

Degradation timelines are anchored relative to "now". Stretch (cut by default): a replay-speed multiplier so degradation visibly advances during a live demo.

## 11. Health and RUL method

| | Option A: Baseline-deviation index + trend extrapolation | Option B: ML (Isolation Forest/autoencoder for health; regression/LSTM for RUL) |
|---|---|---|
| How | Per sensor: rolling mean over a window vs healthy baseline → z-score → 0–100 sub-score. Weighted combine → health index. RUL: fit linear (or exponential) trend to recent health/feature values, extrapolate to the failure threshold; range from fit residuals. | Train on simulated or public run-to-failure data (e.g. NASA C-MAPSS), predict health/RUL. |
| Pros | Explainable (you can say *which sensor* is driving the score), no training data needed, a few dozen lines, testable | "Impressive", learns multivariate patterns |
| Cons | Hand-tuned weights/thresholds; trend fit is crude and noisy early in degradation | Needs training data. Simulated data teaches the model only the simulator's own rules. Slow to debug. Hard to explain. |
| 2-day fit | ✅ | ❌ |

**Pick: A.** It's also honest, since the infographic says "actual models, thresholds and data sources will depend on equipment and available data." Put health and RUL behind small functions (`compute_health(features) -> HealthResult`, `estimate_rul(history) -> RulResult`) so a model can replace them later.
Fault labels: a small rule table (e.g. vibration↑ + temp↑ → "bearing wear"; temp↑ only → "cooling/overheating"; current↑ → "overload").

## 12. Implementation phases (2 days)

| Phase | When | Scope | Demoable outcome | Acceptance criteria |
|-------|------|-------|------------------|---------------------|
| **1. Thin slice** | Day 1 AM | 1 asset (Compressor-02), 1 sensor (vibration). `HistorianClient` + `MockHistorian` with degradation. Health score from the one sensor. API: `GET /assets/{id}/health`, `GET /assets/{id}/timeseries?tag=`. React page with a single line chart + health number. | Open the page, see vibration drifting up and health dropping. | (a) Contract test passes for `MockHistorian`. (b) Health ≥90 on healthy window, <70 on degraded window (unit test). (c) `/docs` shows both endpoints returning data. (d) Chart renders from the API, not hard-coded data. |
| **2. Widen** | Day 1 PM | 5 assets × all sensors. SQLite + seed. Processing runner writes `health_snapshots`. Fleet overview (cards with health %, status colour) and asset detail (multi-sensor charts). | Fleet page like the infographic's "Health Intelligence" panel. | (a) 5 cards with expected statuses (Normal/Degrading/Attention). (b) Clicking a card shows its sensors. (c) Wellhead-05 dropouts don't change its health by >5 pts. (d) Re-running the runner is idempotent. |
| **3. Intelligence** | Day 2 AM | RUL estimate with range, rule-based fault labels, alerts with recommended action, health trend sparkline. | Cards show RUL; alerts list for degrading assets. | (a) Backtest on Motor-04: RUL predicted 48 h before failure is within ±40% of actual. (b) Gearbox-03 raises an alert; Pump-01 raises none. (c) RUL shows ">1000 hrs" for healthy assets, not a nonsense number. |
| **4. Polish + proof** | Day 2 PM | Auto-refresh, loading/error states, `HISTORIAN` env switch + PI stub, README with run steps, 3-minute demo script, update this doc. | End-to-end demo script runs cleanly from a fresh clone. | (a) Fresh clone → documented commands → working app. (b) Swapping to `HISTORIAN=pi` fails with a clear "not implemented" error and nothing above `historian/` changes. |

**Cut from MVP:** real PI/SCADA connection (stub only), ML models, auth/users, work-order/maintenance scheduling, multi-site, WebSockets, deployment/Docker, edge computer (out of scope), replay-speed clock (stretch), mobile layout, alert notifications (email/SMS).

---

## 13. UI design direction (added after Phase 1)

Reference: AdminCN / shadcn-style dark dashboard (screenshots supplied by user).

| Aspect | Direction |
|--------|-----------|
| Theme | Dark by default (near-black page, slightly lighter rounded cards, thin subtle borders); light-mode toggle is a stretch |
| Layout | Collapsible left sidebar (logo, section labels, icon + text nav, active item highlighted), top bar (sidebar toggle, search, alerts bell with red dot, theme toggle) |
| Cards | Rounded, title + muted subtitle, big bold KPI number, small coloured delta/badge, tiny chart inside |
| Colour | Green = normal, amber = degrading, red/pink = attention, blue as neutral accent. Muted dark-green bars with one highlighted bar |
| Charts | Minimal: no heavy grid, thin lines, dotted vertical guides, rounded bars, donut/ring gauge with centre number (used for health %) |
| Tables | Row per asset with status pill, avatar/icon cell, search box, page-size select, pagination |

Mapping to this app:
- Fleet overview: KPI cards (assets monitored, active alerts, avg health, lowest RUL), per-asset cards with ring gauge + RUL + sparkline.
- Asset detail: trend chart with alarm line, per-sensor mini cards, alert list.
- Assets table: status pill, health %, RUL, fault label, search and pagination.
- Sidebar items: Overview, Assets, Alerts (only these; the rest of the template's nav is out of scope).

**Stack change this implies (deviation from the approved plan, pending approval):** add **Tailwind CSS + shadcn/ui** (Radix primitives, copy-in components such as Card, Badge, Table, Sidebar) and keep Recharts for charts (shadcn's chart components wrap Recharts). The backend and API are unaffected.

---

## 14. Changes made during Phase 2 (design deltas)

| Area | What changed vs the plan above |
|------|-------------------------------|
| Mock model | Degradation is **asset-level**: `progress` goes 0→1 (1 = most sensitive sensor hits its alarm limit). Each sensor shows `sensitivity × progress × (alarm − baseline)`, so vibration moves first, temperature lags, pressure may not move. Defined in `mock/scenarios.py`, storylines in `mock/fleet.py` (also used to seed the DB). |
| Health | Per sensor: median of last 1 h (GOOD samples only) → 0–100. Asset: **70 % worst sensor + 30 % weighted average**, so one failing signal dominates but others still count. |
| Processing | `processing/runner.py`: `run_once(at)` upserts one snapshot per asset (unique `asset_id, ts`); `backfill()` fills 14 days at 3 h steps on first start. Background job re-runs every 60 s (`REFRESH_SECONDS`, 0 disables). |
| DB | Only `assets`, `sensors`, `health_snapshots` exist so far. `alerts` and `failure_events` are added in Phase 3 when they are used. `baseline_std` dropped (unused). |
| API | `GET /assets`, `/summary`, `/assets/{id}`, `/assets/{id}/health/history`, `/assets/{id}/timeseries` (live from historian). |
| UI | Tailwind v4 + shadcn/ui (Base UI style), dark theme, hash routing (no router library). Sidebar has Overview and Assets; Alerts arrives in Phase 3. |
