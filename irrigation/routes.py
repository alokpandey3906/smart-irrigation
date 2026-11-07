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
