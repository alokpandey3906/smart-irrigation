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

## 7. Deploying on Replit
The repository includes a `.replit` run command and a `Procfile` for production hosting.
Import the GitHub repository into Replit, then use **Deploy** to publish it. The deployment
needs to install `requirements.txt` and run `gunicorn --bind 0.0.0.0:3000 run:app`.
SQLite history is stored in the app's `instance/` folder; use a persistent Replit deployment
or an external database if saved history must survive redeployments.

## 8. Deploying on Vercel
The repository includes `pyproject.toml` with the Flask application entry point for Vercel.
Import the GitHub repository into Vercel and deploy with the default settings.
Vercel's function filesystem is temporary, so SQLite history is not durable across
function instances or deployments. Configure `DATABASE` to use a persistent database
before relying on saved history in production.
