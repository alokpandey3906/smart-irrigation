# Smart Irrigation Advisor: all source files

Create each file below at the path shown (make the folders first), paste the code, save. Then follow `README.md` section 2.

Folders to create: `irrigation/templates`, `irrigation/static/css`, `irrigation/static/js`, `tests`, `docs`.

`tests/__init__.py` is an empty file. `docs/REPORT_GUIDE.md` is included separately in the zip.

## Files

1. `README.md`
2. `requirements.txt`
3. `config.py`
4. `run.py`
5. `irrigation/__init__.py`
6. `irrigation/data.py`
7. `irrigation/engine.py`
8. `irrigation/validators.py`
9. `irrigation/models.py`
10. `irrigation/routes.py`
11. `irrigation/templates/base.html`
12. `irrigation/templates/index.html`
13. `irrigation/templates/history.html`
14. `irrigation/static/css/style.css`
15. `irrigation/static/js/app.js`
16. `tests/__init__.py`
17. `tests/test_engine.py`
18. `tests/test_validators.py`
19. `tests/test_routes.py`


---

## `README.md`

```markdown
# Smart Irrigation Advisor

A Flask web app that recommends when to irrigate, how much water to apply and how long to run the pump.
It uses a simplified FAO-56 water balance, validates every input, and saves each recommendation to SQLite.

## 1. Requirements
- Python 3.9 or newer (check with `python --version`)
- A terminal (Command Prompt, PowerShell, Terminal)
- Internet access once, to install Flask

## 2. Set up (do these in order)
1. Open a terminal in this folder (the one containing `run.py`).
2. Create a virtual environment:
   - Windows: `python -m venv venv`
   - macOS/Linux: `python3 -m venv venv`
3. Activate it:
   - Windows (PowerShell): `venv\Scripts\Activate.ps1`
   - Windows (cmd): `venv\Scripts\activate.bat`
   - macOS/Linux: `source venv/bin/activate`
   You should see `(venv)` at the start of the prompt.
4. Install dependencies: `pip install -r requirements.txt`
5. Run the tests: `python -m unittest discover -v`
   Expect `Ran 25 tests ... OK`. Fix anything that fails before continuing.
6. Start the app: `python run.py`
7. Open http://127.0.0.1:5000 in your browser.

## 3. Using it
1. On **Advisor**, enter crop, stage, soil, soil moisture, weather and system details.
2. Select **Get recommendation**. The verdict, litres, pump hours and soil gauge appear.
3. Open **History** to see saved results, download a CSV, or clear the list.

## 4. Folder map
| Path | Purpose |
|---|---|
| `run.py` | Starts the server |
| `config.py` | Settings (database path, secret key) |
| `irrigation/__init__.py` | App factory |
| `irrigation/data.py` | Crop, soil and method tables |
| `irrigation/engine.py` | All calculations |
| `irrigation/validators.py` | Input checks |
| `irrigation/models.py` | SQLite history |
| `irrigation/routes.py` | Pages and JSON API |
| `irrigation/templates/` | HTML pages |
| `irrigation/static/` | CSS and JavaScript |
| `tests/` | Unit and route tests |
| `docs/REPORT_GUIDE.md` | Chapter-by-chapter guide for the project report |

## 5. API
`POST /api/recommend` with JSON: `crop, stage, soil, method, moisture, tmax, tmin, humidity, rain, lat, area, flow`.
Returns the recommendation (200) or `{"errors": [...]}` (400).
Other routes: `GET /history`, `GET /history.csv`, `POST /history/clear`, `GET /health`.

## 6. Troubleshooting
| Problem | Fix |
|---|---|
| `python` not found | Install Python from python.org and tick "Add to PATH" |
| `No module named flask` | Activate the venv, then run `pip install -r requirements.txt` |
| Port 5000 already in use | Edit `run.py`: `app.run(debug=True, port=5001)` |
| PowerShell blocks activation | Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, or use cmd |
| Page has no styling | Hard refresh with Ctrl+F5 |
```


---

## `requirements.txt`

```text
Flask>=3.0
```


---

## `config.py`

```python
"""Application configuration."""
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-change-me")
    # SQLite file that stores recommendation history.
    DATABASE = os.environ.get("DATABASE", os.path.join(BASE_DIR, "instance", "irrigation.db"))
```


---

## `run.py`

```python
"""Entry point:  python run.py"""
from irrigation import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
```


---

## `irrigation/__init__.py`

```python
"""Smart Irrigation Advisor - Flask application factory."""
import os
from flask import Flask


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object("config.Config")
    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(app.config["DATABASE"]), exist_ok=True)

    from . import models, routes
    models.init_app(app)
    app.register_blueprint(routes.bp)
    return app
```


---

## `irrigation/data.py`

```python
"""Reference tables used by the engine.

Values are simplified from FAO Irrigation and Drainage Paper No. 56
(Allen et al., 1998). Replace them with local agronomy data for real use.

kc      : crop coefficient for each growth stage
root_m  : effective root depth in metres
p       : fraction of total available water that may be used before stress
"""

STAGES = ("initial", "development", "mid", "late")

CROPS = {
    "Wheat":     {"kc": {"initial": 0.40, "development": 0.80, "mid": 1.15, "late": 0.40}, "root_m": 1.0, "p": 0.55},
    "Rice":      {"kc": {"initial": 1.05, "development": 1.10, "mid": 1.20, "late": 0.90}, "root_m": 0.5, "p": 0.20},
    "Maize":     {"kc": {"initial": 0.40, "development": 0.80, "mid": 1.20, "late": 0.60}, "root_m": 1.0, "p": 0.55},
    "Tomato":    {"kc": {"initial": 0.60, "development": 0.90, "mid": 1.15, "late": 0.80}, "root_m": 0.7, "p": 0.40},
    "Potato":    {"kc": {"initial": 0.50, "development": 0.80, "mid": 1.15, "late": 0.75}, "root_m": 0.5, "p": 0.35},
    "Sugarcane": {"kc": {"initial": 0.40, "development": 0.85, "mid": 1.25, "late": 0.75}, "root_m": 1.2, "p": 0.65},
}

# awc: available water capacity (mm of water per metre of soil)
# fc / wp: field capacity / wilting point (% by volume)
SOILS = {
    "Sandy": {"awc": 80,  "fc": 15, "wp": 7},
    "Loam":  {"awc": 150, "fc": 28, "wp": 13},
    "Clay":  {"awc": 180, "fc": 38, "wp": 20},
}

# Application efficiency of each irrigation method.
METHODS = {"Drip": 0.90, "Sprinkler": 0.75, "Flood": 0.55}
```


---

## `irrigation/engine.py`

```python
"""Irrigation recommendation engine (simplified FAO-56 water balance).

Pipeline
  1. ET0  - reference evapotranspiration (Hargreaves)
  2. ETc  - crop water use = Kc x ET0
  3. TAW  - total available water in the root zone
  4. Dr   - current root-zone depletion from measured soil moisture
  5. RAW  - readily available water = p x TAW (stress threshold)
  6. Decide, then convert the needed depth to litres and pump hours.
"""
import math
from datetime import date

from .data import CROPS, METHODS, SOILS


def extraterrestrial_radiation(lat_deg, doy):
    """Ra in mm/day (FAO-56 eq. 21, converted with 0.408)."""
    phi = math.radians(lat_deg)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    delta = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    x = max(-1.0, min(1.0, -math.tan(phi) * math.tan(delta)))
    ws = math.acos(x)
    ra_mj = (24 * 60 / math.pi) * 0.0820 * dr * (
        ws * math.sin(phi) * math.sin(delta)
        + math.cos(phi) * math.cos(delta) * math.sin(ws)
    )
    return ra_mj * 0.408


def hargreaves_et0(tmax, tmin, lat_deg, doy):
    """ET0 (mm/day) = 0.0023 (Tmean + 17.8) sqrt(Tmax - Tmin) Ra."""
    tmean = (tmax + tmin) / 2
    ra = extraterrestrial_radiation(lat_deg, doy)
    return max(0.0, 0.0023 * (tmean + 17.8) * math.sqrt(max(tmax - tmin, 0.0)) * ra)


def humidity_adjustment(humidity):
    """Hargreaves ignores humidity, so trim demand slightly above 60% RH."""
    return 1 - max(0.0, humidity - 60) / 200


def effective_rain(forecast_mm):
    """Ignore showers under 5 mm; count 80% of larger events."""
    return 0.8 * forecast_mm if forecast_mm >= 5 else 0.0


def recommend(d, doy=None):
    """Return a recommendation dict from validated inputs `d`."""
    crop, soil, eff = CROPS[d["crop"]], SOILS[d["soil"]], METHODS[d["method"]]
    doy = doy or date.today().timetuple().tm_yday

    et0 = hargreaves_et0(d["tmax"], d["tmin"], d["lat"], doy) * humidity_adjustment(d["humidity"])
    kc = crop["kc"][d["stage"]]
    etc = et0 * kc
    rain_eff = effective_rain(d["rain"])

    taw = soil["awc"] * crop["root_m"]
    raw = crop["p"] * taw
    remaining = (d["moisture"] - soil["wp"]) / (soil["fc"] - soil["wp"])
    remaining = max(0.0, min(1.0, remaining))
    depletion = (1 - remaining) * taw

    projected = max(0.0, depletion + etc - rain_eff)     # depletion after today and rain
    irrigate = projected >= raw
    rain_saves_trip = (not irrigate) and (depletion + etc >= raw)
    days_left = max(0.0, (raw - depletion) / etc) if etc > 0 else 99.0

    net = min(projected, taw) if irrigate else 0.0
    gross = net / eff
    litres = gross * d["area"]                            # 1 mm over 1 m2 = 1 L
    hours = litres / d["flow"]

    if irrigate and remaining < 0.25:
        level, message = "urgent", "Soil is dry. Irrigate today."
    elif irrigate:
        level, message = "irrigate", "Irrigate within the next day."
    elif rain_saves_trip:
        level, message = "skip", "Forecast rain covers crop needs. Skip irrigation."
    else:
        level, message = "ok", f"Soil moisture is fine. Check again in {max(1, int(days_left))} day(s)."

    return {
        "level": level, "message": message,
        "et0": round(et0, 2), "kc": kc, "etc": round(etc, 2),
        "rain_effective": round(rain_eff, 1),
        "taw": round(taw, 1), "raw": round(raw, 1), "depletion": round(depletion, 1),
        "moisture_pct": round(remaining * 100), "trigger_pct": round((1 - crop["p"]) * 100),
        "net_mm": round(net, 1), "gross_mm": round(gross, 1),
        "litres": round(litres), "hours": round(hours, 1),
        "days_left": round(days_left, 1), "efficiency": round(eff * 100),
    }
```


---

## `irrigation/validators.py`

```python
"""Input validation. Returns clean values or a list of readable errors."""
from .data import CROPS, METHODS, SOILS, STAGES

# field: (label, minimum, maximum)
NUMERIC_RULES = {
    "moisture": ("Soil moisture (%)", 0, 60),
    "tmax": ("Max temperature (°C)", -10, 55),
    "tmin": ("Min temperature (°C)", -20, 45),
    "humidity": ("Humidity (%)", 0, 100),
    "rain": ("Rain forecast (mm)", 0, 500),
    "lat": ("Latitude (°N)", -60, 60),
    "area": ("Field area (m²)", 1, 10_000_000),
    "flow": ("Pump flow (L/h)", 1, 1_000_000),
}

CHOICES = {
    "crop": ("Crop", CROPS),
    "stage": ("Growth stage", STAGES),
    "soil": ("Soil type", SOILS),
    "method": ("Method", METHODS),
}


def validate(form):
    """Return (clean_dict, errors). clean_dict is empty when errors exist."""
    clean, errors = {}, []

    for key, (label, options) in CHOICES.items():
        value = form.get(key)
        if value not in options:
            errors.append(f"{label}: choose one of the listed options.")
        else:
            clean[key] = value

    for key, (label, low, high) in NUMERIC_RULES.items():
        raw = form.get(key)
        try:
            number = float(raw)
        except (TypeError, ValueError):
            errors.append(f"{label}: enter a number.")
            continue
        if number != number or number in (float("inf"), float("-inf")):
            errors.append(f"{label}: enter a finite number.")
        elif not low <= number <= high:
            errors.append(f"{label}: must be between {low} and {high}.")
        else:
            clean[key] = number

    if "tmax" in clean and "tmin" in clean and clean["tmax"] < clean["tmin"]:
        errors.append("Max temperature must not be lower than min temperature.")

    return ({} if errors else clean), errors
```


---

## `irrigation/models.py`

```python
"""SQLite storage for recommendation history (standard library only)."""
import json
import sqlite3
from datetime import datetime, timezone

from flask import current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT    NOT NULL,
    crop       TEXT    NOT NULL,
    stage      TEXT    NOT NULL,
    soil       TEXT    NOT NULL,
    method     TEXT    NOT NULL,
    inputs     TEXT    NOT NULL,
    level      TEXT    NOT NULL,
    message    TEXT    NOT NULL,
    litres     INTEGER NOT NULL,
    hours      REAL    NOT NULL
);
"""


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
    with app.app_context():
        get_db().executescript(SCHEMA)


def save_record(inputs, result):
    db = get_db()
    db.execute(
        "INSERT INTO records (created_at, crop, stage, soil, method, inputs, level, message, litres, hours)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
         inputs["crop"], inputs["stage"], inputs["soil"], inputs["method"],
         json.dumps(inputs), result["level"], result["message"], result["litres"], result["hours"]),
    )
    db.commit()


def list_records(limit=100):
    rows = get_db().execute("SELECT * FROM records ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    return [dict(r) for r in rows]


def clear_records():
    db = get_db()
    db.execute("DELETE FROM records")
    db.commit()
```


---

## `irrigation/routes.py`

```python
"""HTTP routes: pages and JSON API."""
import csv
import io

from flask import Blueprint, Response, jsonify, redirect, render_template, request, url_for

from . import models
from .data import CROPS, METHODS, SOILS, STAGES
from .engine import recommend
from .validators import validate

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return render_template("index.html", crops=CROPS, soils=SOILS, methods=METHODS, stages=STAGES)


@bp.post("/api/recommend")
def api_recommend():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify(errors=["Send the form values as a JSON object."]), 400
    clean, errors = validate(payload)
    if errors:
        return jsonify(errors=errors), 400
    result = recommend(clean)
    models.save_record(clean, result)
    return jsonify(result)


@bp.get("/history")
def history():
    return render_template("history.html", records=models.list_records())


@bp.get("/history.csv")
def history_csv():
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["id", "created_at_utc", "crop", "stage", "soil", "method", "decision", "litres", "pump_hours"])
    for r in models.list_records(limit=10_000):
        writer.writerow([r["id"], r["created_at"], r["crop"], r["stage"], r["soil"], r["method"],
                         r["level"], r["litres"], r["hours"]])
    return Response(out.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=irrigation_history.csv"})


@bp.post("/history/clear")
def history_clear():
    models.clear_records()
    return redirect(url_for("main.history"))


@bp.get("/health")
def health():
    return jsonify(status="ok")
```


---

## `irrigation/templates/base.html`

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{% block title %}Smart Irrigation Advisor{% endblock %}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Bitter:wght@600;700&family=Instrument+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
<nav class="nav">
  <a class="brand" href="{{ url_for('main.index') }}">Smart Irrigation Advisor</a>
  <div>
    <a href="{{ url_for('main.index') }}">Advisor</a>
    <a href="{{ url_for('main.history') }}">History</a>
  </div>
</nav>
{% block content %}{% endblock %}
<footer class="foot">Advice is based on a simplified FAO-56 model. Check it against local conditions before relying on it.</footer>
</body>
</html>
```


---

## `irrigation/templates/index.html`

```html
{% extends "base.html" %}
{% block content %}
<header class="top">
  <h1>Today’s irrigation advice</h1>
  <p>Enter field conditions. Get how much water to apply, and for how long.</p>
</header>
<main class="layout">
  <form id="form" class="panel" novalidate>
    <fieldset>
      <legend>Crop and soil</legend>
      <label>Crop
        <select name="crop">{% for c in crops %}<option>{{ c }}</option>{% endfor %}</select></label>
      <label>Growth stage
        <select name="stage">{% for s in stages %}<option value="{{ s }}" {{ 'selected' if s == 'mid' }}>{{ s|capitalize }}</option>{% endfor %}</select></label>
      <label>Soil type
        <select name="soil">{% for s in soils %}<option {{ 'selected' if s == 'Loam' }}>{{ s }}</option>{% endfor %}</select></label>
      <label>Soil moisture (% by volume)
        <input type="number" name="moisture" value="20" min="0" max="60" step="0.1" required></label>
    </fieldset>
    <fieldset>
      <legend>Weather</legend>
      <label>Max temp (°C)<input type="number" name="tmax" value="32" step="0.1" required></label>
      <label>Min temp (°C)<input type="number" name="tmin" value="18" step="0.1" required></label>
      <label>Humidity (%)<input type="number" name="humidity" value="45" min="0" max="100" required></label>
      <label>Rain forecast, next 48 h (mm)<input type="number" name="rain" value="0" min="0" step="0.1" required></label>
      <label>Latitude (°N)<input type="number" name="lat" value="25.4" step="0.1" min="-60" max="60" required></label>
    </fieldset>
    <fieldset>
      <legend>Your system</legend>
      <label>Field area (m²)<input type="number" name="area" value="1000" min="1" required></label>
      <label>Method
        <select name="method">{% for m in methods %}<option>{{ m }}</option>{% endfor %}</select></label>
      <label>Pump flow (litres/hour)<input type="number" name="flow" value="2000" min="1" required></label>
    </fieldset>
    <button type="submit">Get recommendation</button>
    <ul id="errors" class="error" role="alert"></ul>
  </form>

  <section class="panel" aria-live="polite">
    <div class="empty" id="empty">
      <h2>No recommendation yet</h2>
      <p>Fill in the form and select <b>Get recommendation</b>.</p>
    </div>
    <div id="output" hidden>
      <div class="verdict" id="verdict"><h2 id="msg"></h2></div>
      <div class="body">
        <div class="gauge" aria-label="Root-zone water level">
          <div class="tube">
            <div class="fill" id="fill"></div>
            <div class="trigger" id="trigger"><span>Irrigate below here</span></div>
          </div>
          <div class="g-labels"><span>Field capacity</span><span id="gpct"></span><span>Wilting point</span></div>
        </div>
        <dl class="facts">
          <div class="big"><dt>Apply</dt><dd><span id="litres"></span> L</dd></div>
          <div><dt>Run pump for</dt><dd><span id="hours"></span> h</dd></div>
          <div><dt>Water depth</dt><dd><span id="gross"></span> mm</dd></div>
          <div><dt>Crop water use today</dt><dd><span id="etc"></span> mm/day</dd></div>
          <div><dt>Reference ET₀</dt><dd><span id="et0"></span> mm/day</dd></div>
          <div><dt>Crop coefficient Kc</dt><dd><span id="kc"></span></dd></div>
          <div><dt>Soil deficit</dt><dd><span id="depl"></span> mm</dd></div>
          <div><dt>Stress threshold (RAW)</dt><dd><span id="raw"></span> mm</dd></div>
          <div><dt>Effective rain</dt><dd><span id="rain"></span> mm</dd></div>
          <div><dt>Days until trigger</dt><dd><span id="days"></span></dd></div>
        </dl>
      </div>
    </div>
  </section>
</main>
<script src="{{ url_for('static', filename='js/app.js') }}"></script>
{% endblock %}
```


---

## `irrigation/templates/history.html`

```html
{% extends "base.html" %}
{% block title %}History · Smart Irrigation Advisor{% endblock %}
{% block content %}
<header class="top">
  <h1>Recommendation history</h1>
  <p>Every recommendation is saved so you can review past decisions.</p>
</header>
<main class="wrap">
  <section class="panel">
    {% if records %}
    <div class="actions">
      <a class="btn" href="{{ url_for('main.history_csv') }}">Download CSV</a>
      <form method="post" action="{{ url_for('main.history_clear') }}"
            onsubmit="return confirm('Delete all saved recommendations?')">
        <button class="danger" type="submit">Clear history</button>
      </form>
    </div>
    <div class="scroll">
      <table>
        <thead><tr><th>Time (UTC)</th><th>Crop</th><th>Stage</th><th>Soil</th><th>Method</th><th>Decision</th><th>Litres</th><th>Pump hours</th></tr></thead>
        <tbody>
        {% for r in records %}
          <tr><td>{{ r.created_at }}</td><td>{{ r.crop }}</td><td>{{ r.stage|capitalize }}</td><td>{{ r.soil }}</td><td>{{ r.method }}</td>
              <td><span class="tag {{ r.level }}">{{ r.level }}</span></td><td>{{ '{:,}'.format(r.litres) }}</td><td>{{ r.hours }}</td></tr>
        {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div class="empty"><h2>No history yet</h2><p>Get a recommendation on the <a href="{{ url_for('main.index') }}">Advisor</a> page and it will appear here.</p></div>
    {% endif %}
  </section>
</main>
{% endblock %}
```


---

## `irrigation/static/css/style.css`

```css
:root {
  --paper:#eef2ec; --card:#fbfcfa; --ink:#1b2a22; --muted:#5b6b61; --line:#cfd8cf;
  --leaf:#2e7a4c; --water:#1d6fa5; --amber:#b9801f; --alert:#b4402f; --soil:#5a4632;
}
@media (prefers-color-scheme: dark) {
  :root { --paper:#121a15; --card:#1a251e; --ink:#e6eee8; --muted:#9bb0a3; --line:#2c3b32;
          --leaf:#5fb27f; --water:#5aa9dd; --amber:#e0a94a; --alert:#e07767; --soil:#8a6e50; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--paper); color:var(--ink); font:16px/1.5 "Instrument Sans", system-ui, sans-serif; }
a { color:var(--water); }
h1, h2 { font-family:"Bitter", Georgia, serif; margin:0; }
.nav { display:flex; justify-content:space-between; align-items:center; gap:1rem; flex-wrap:wrap;
  padding:.8rem 1.25rem; background:var(--card); border-bottom:1px solid var(--line); }
.nav a { text-decoration:none; color:var(--ink); margin-left:1rem; }
.nav .brand { font:700 1.1rem "Bitter", serif; margin:0; color:var(--leaf); }
.top, .layout, .wrap { max-width:1100px; margin:0 auto; padding-left:1.25rem; padding-right:1.25rem; }
.top { padding-top:2rem; padding-bottom:.5rem; }
.top h1 { font-size:clamp(1.7rem,4vw,2.4rem); }
.top p { color:var(--muted); margin:.4rem 0 0; }
.layout { display:grid; grid-template-columns:340px 1fr; gap:1.25rem; align-items:start; padding-top:1rem; padding-bottom:3rem; }
.wrap { padding-top:1rem; padding-bottom:3rem; }
.panel { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:1.25rem; }
fieldset { border:0; padding:0; margin:0 0 1.25rem; display:grid; gap:.75rem; min-width:0; }
legend { font:600 1.05rem "Bitter", serif; padding:0 0 .5rem; border-bottom:2px solid var(--leaf); width:100%; margin-bottom:.25rem; }
label { display:grid; gap:.25rem; font-size:.9rem; color:var(--muted); }
input, select { font:inherit; color:var(--ink); background:var(--paper); border:1px solid var(--line); border-radius:6px; padding:.5rem .6rem; width:100%; }
input:focus-visible, select:focus-visible, button:focus-visible, a:focus-visible { outline:3px solid var(--water); outline-offset:1px; }
button, .btn { font:600 1rem "Instrument Sans", sans-serif; color:#fff; background:var(--leaf); border:0; border-radius:6px;
  padding:.7rem 1rem; cursor:pointer; text-decoration:none; display:inline-block; }
form button[type=submit] { width:100%; }
button.danger { background:var(--alert); }
.error { color:var(--alert); margin:.6rem 0 0; padding-left:1.1rem; font-size:.9rem; }
.error:empty { display:none; }
.empty { padding:3rem 1rem; text-align:center; color:var(--muted); }
.empty h2 { color:var(--ink); font-size:1.3rem; margin-bottom:.4rem; }
.verdict { border-left:8px solid var(--leaf); background:color-mix(in srgb, var(--leaf) 12%, transparent); padding:1rem 1.25rem; border-radius:6px; margin-bottom:1.5rem; }
.verdict h2 { font-size:1.4rem; }
.verdict.irrigate { border-color:var(--amber); background:color-mix(in srgb, var(--amber) 15%, transparent); }
.verdict.urgent { border-color:var(--alert); background:color-mix(in srgb, var(--alert) 15%, transparent); }
.verdict.skip { border-color:var(--water); background:color-mix(in srgb, var(--water) 14%, transparent); }
.body { display:grid; grid-template-columns:170px 1fr; gap:2rem; }
.gauge { display:grid; gap:.5rem; justify-items:center; }
.tube { position:relative; width:64px; height:260px; border:2px solid var(--soil); border-radius:6px; background:color-mix(in srgb, var(--soil) 18%, var(--card)); }
.fill { position:absolute; bottom:0; left:0; right:0; height:0; background:var(--water); border-radius:0 0 3px 3px; transition:height .6s ease; }
.trigger { position:absolute; left:-10px; right:-10px; bottom:50%; border-top:2px dashed var(--alert); }
.trigger span { position:absolute; left:100%; margin-left:.6rem; top:-.7rem; white-space:nowrap; font-size:.75rem; color:var(--alert); }
.g-labels { display:grid; gap:.15rem; text-align:center; font-size:.75rem; color:var(--muted); }
.g-labels #gpct { color:var(--ink); font-weight:600; }
.facts { margin:0; display:grid; grid-template-columns:1fr 1fr; gap:1rem 1.5rem; align-content:start; }
.facts div { border-top:1px solid var(--line); padding-top:.5rem; }
.facts dt { font-size:.85rem; color:var(--muted); }
.facts dd { margin:0; font-size:1.2rem; font-weight:600; }
.facts .big { grid-column:1 / -1; border-top:0; padding:0; }
.facts .big dd { font:700 clamp(2.2rem,6vw,3.2rem)/1.1 "Bitter", serif; color:var(--water); }
.actions { display:flex; gap:.75rem; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; }
.scroll { overflow-x:auto; }
table { width:100%; border-collapse:collapse; font-size:.92rem; }
th, td { text-align:left; padding:.55rem .7rem; border-bottom:1px solid var(--line); white-space:nowrap; }
th { color:var(--muted); font-weight:600; }
.tag { padding:.15rem .6rem; border-radius:99px; font-size:.8rem; font-weight:600; background:color-mix(in srgb, var(--leaf) 18%, transparent); }
.tag.irrigate { background:color-mix(in srgb, var(--amber) 22%, transparent); }
.tag.urgent { background:color-mix(in srgb, var(--alert) 22%, transparent); }
.tag.skip { background:color-mix(in srgb, var(--water) 20%, transparent); }
.foot { text-align:center; color:var(--muted); font-size:.85rem; padding:1.5rem 1.25rem 2.5rem; }
@media (max-width:820px) {
  .layout, .body { grid-template-columns:1fr; }
  .gauge { justify-items:start; }
  .trigger span { display:none; }
}
@media (prefers-reduced-motion:reduce) { .fill { transition:none; } }
```


---

## `irrigation/static/js/app.js`

```javascript
"use strict";
const $ = id => document.getElementById(id);

$("form").addEventListener("submit", async event => {
  event.preventDefault();
  $("errors").innerHTML = "";
  const body = Object.fromEntries(new FormData(event.target));
  try {
    const res = await fetch("/api/recommend", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (!res.ok) { showErrors(data.errors || ["Something went wrong."]); return; }
    show(data);
  } catch {
    showErrors(["Could not reach the server. Check that run.py is running."]);
  }
});

function showErrors(list) {
  $("errors").innerHTML = list.map(e => `<li>${e.replace(/[<>&]/g, "")}</li>`).join("");
}

function show(r) {
  $("empty").hidden = true;
  $("output").hidden = false;
  $("verdict").className = "verdict " + r.level;
  $("msg").textContent = r.message;
  $("fill").style.height = r.moisture_pct + "%";
  $("trigger").style.bottom = r.trigger_pct + "%";
  $("gpct").textContent = r.moisture_pct + "% of usable water left";
  $("litres").textContent = r.litres.toLocaleString();
  $("hours").textContent = r.hours;
  $("gross").textContent = r.gross_mm;
  $("etc").textContent = r.etc;
  $("et0").textContent = r.et0;
  $("kc").textContent = r.kc;
  $("depl").textContent = r.depletion;
  $("raw").textContent = r.raw;
  $("rain").textContent = r.rain_effective;
  $("days").textContent = r.days_left >= 30 ? "30+" : r.days_left;
}
```


---

## `tests/__init__.py`

(empty file)


---

## `tests/test_engine.py`

```python
import unittest

from irrigation.engine import (effective_rain, extraterrestrial_radiation,
                               hargreaves_et0, humidity_adjustment, recommend)

BASE = dict(crop="Wheat", stage="mid", soil="Loam", method="Drip", moisture=20.0,
            tmax=32.0, tmin=18.0, humidity=45.0, rain=0.0, lat=25.4, area=1000.0, flow=2000.0)
DOY = 60  # 1 March


class EngineMath(unittest.TestCase):
    def test_ra_in_expected_range(self):
        self.assertTrue(11 < extraterrestrial_radiation(25.4, DOY) < 15)

    def test_et0_zero_when_no_temperature_range(self):
        self.assertEqual(hargreaves_et0(25, 25, 25.4, DOY), 0.0)

    def test_et0_rises_with_temperature_range(self):
        self.assertGreater(hargreaves_et0(35, 15, 25.4, DOY), hargreaves_et0(30, 20, 25.4, DOY))

    def test_humidity_adjustment(self):
        self.assertEqual(humidity_adjustment(50), 1.0)
        self.assertAlmostEqual(humidity_adjustment(100), 0.8)

    def test_effective_rain(self):
        self.assertEqual(effective_rain(4.9), 0.0)
        self.assertAlmostEqual(effective_rain(10), 8.0)


class Decisions(unittest.TestCase):
    def rec(self, **over):
        return recommend({**BASE, **over}, doy=DOY)

    def test_wet_soil_needs_nothing(self):
        r = self.rec(moisture=28)
        self.assertEqual(r["level"], "ok")
        self.assertEqual(r["litres"], 0)

    def test_dry_soil_is_urgent(self):
        r = self.rec(moisture=14)
        self.assertEqual(r["level"], "urgent")
        self.assertGreater(r["litres"], 0)

    def test_moderately_dry_soil_irrigates(self):
        self.assertEqual(self.rec(moisture=19)["level"], "irrigate")

    def test_rain_skips_irrigation(self):
        dry = self.rec(moisture=20)
        self.assertEqual(dry["level"], "irrigate")
        wet = self.rec(moisture=20, rain=40)
        self.assertEqual(wet["level"], "skip")
        self.assertEqual(wet["litres"], 0)

    def test_litres_equal_depth_times_area(self):
        r = self.rec(moisture=15)
        self.assertAlmostEqual(r["litres"], r["gross_mm"] * 1000, delta=60)

    def test_less_efficient_method_uses_more_water(self):
        drip = self.rec(moisture=15, method="Drip")["litres"]
        flood = self.rec(moisture=15, method="Flood")["litres"]
        self.assertGreater(flood, drip)

    def test_pump_hours_scale_with_flow(self):
        slow = self.rec(moisture=15, flow=1000)["hours"]
        fast = self.rec(moisture=15, flow=4000)["hours"]
        self.assertGreater(slow, fast)

    def test_moisture_clamped_between_wilting_and_field_capacity(self):
        self.assertEqual(self.rec(moisture=0)["moisture_pct"], 0)
        self.assertEqual(self.rec(moisture=60)["moisture_pct"], 100)


if __name__ == "__main__":
    unittest.main()
```


---

## `tests/test_validators.py`

```python
import unittest

from irrigation.validators import validate

GOOD = dict(crop="Wheat", stage="mid", soil="Loam", method="Drip", moisture="20", tmax="32",
            tmin="18", humidity="45", rain="0", lat="25.4", area="1000", flow="2000")


class Validation(unittest.TestCase):
    def test_valid_input_passes_and_is_converted(self):
        clean, errors = validate(GOOD)
        self.assertEqual(errors, [])
        self.assertEqual(clean["moisture"], 20.0)

    def test_missing_field(self):
        bad = {k: v for k, v in GOOD.items() if k != "area"}
        self.assertTrue(validate(bad)[1])

    def test_text_instead_of_number(self):
        self.assertTrue(validate({**GOOD, "tmax": "hot"})[1])

    def test_out_of_range(self):
        self.assertTrue(validate({**GOOD, "humidity": "150"})[1])

    def test_unknown_crop(self):
        self.assertTrue(validate({**GOOD, "crop": "Banana"})[1])

    def test_tmax_below_tmin(self):
        self.assertTrue(validate({**GOOD, "tmax": "10", "tmin": "20"})[1])

    def test_nan_and_infinity_rejected(self):
        self.assertTrue(validate({**GOOD, "rain": "nan"})[1])
        self.assertTrue(validate({**GOOD, "rain": "inf"})[1])


if __name__ == "__main__":
    unittest.main()
```


---

## `tests/test_routes.py`

```python
import os
import tempfile
import unittest

from irrigation import create_app

GOOD = dict(crop="Wheat", stage="mid", soil="Loam", method="Drip", moisture=20, tmax=32,
            tmin=18, humidity=45, rain=0, lat=25.4, area=1000, flow=2000)


class Routes(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.client = create_app({"DATABASE": self.path, "TESTING": True}).test_client()

    def tearDown(self):
        os.remove(self.path)

    def test_pages_load(self):
        for url in ("/", "/history", "/health"):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_recommend_returns_result_and_is_saved(self):
        r = self.client.post("/api/recommend", json=GOOD)
        self.assertEqual(r.status_code, 200)
        self.assertIn("litres", r.get_json())
        self.assertIn(b"Wheat", self.client.get("/history").data)

    def test_bad_input_returns_errors(self):
        r = self.client.post("/api/recommend", json={**GOOD, "humidity": 500})
        self.assertEqual(r.status_code, 400)
        self.assertTrue(r.get_json()["errors"])

    def test_non_json_body_rejected(self):
        self.assertEqual(self.client.post("/api/recommend", data="x").status_code, 400)

    def test_csv_export_and_clear(self):
        self.client.post("/api/recommend", json=GOOD)
        csv_text = self.client.get("/history.csv").data.decode()
        self.assertIn("crop", csv_text.splitlines()[0])
        self.assertEqual(len(csv_text.strip().splitlines()), 2)
        self.client.post("/history/clear")
        self.assertEqual(len(self.client.get("/history.csv").data.decode().strip().splitlines()), 1)


if __name__ == "__main__":
    unittest.main()
```
