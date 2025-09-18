# backend/app/api_prior.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
from .data_loader import load_services, load_shifts, load_garages, load_eusd
from .prioritizer import prioritize
from .ors_client import build_matrix
from .assigner import greedy_assign
from .db_utils import save_run_result

app = Flask(__name__)
CORS(app)

@app.route("/api/ingest_paths", methods=["POST"])
def ingest_paths():
    """
    Optional: provide custom paths for files (JSON payload) or upload files via multipart.
    For simplicity here we accept JSON with paths; you can extend to accept multipart uploads.
    """
    payload = request.json or {}
    # not persisting paths in DB for this example
    return jsonify({"status":"ok","message":"paths received","paths":payload})

@app.route("/api/priority/run", methods=["POST"])
def run_prioritization():
    """
    Body (JSON) optional:
      { "now": "2024-03-10T09:00:00" }
    Uses configured paths by default.
    Returns prioritized DataFrame head + matrix status.
    """
    data = request.json or {}
    now_str = data.get('now')
    now = pd.to_datetime(str(now_str)) if now_str is not None else pd.Timestamp.utcnow()
    services_df = load_services()
    shifts_df = load_shifts()
    garages_df = load_garages()

    # build locations: first garages then services
    garages_loc = garages_df[['lon','lat']].values.tolist()
    services_loc = services_df[['lon','lat']].values.tolist()
    locations = garages_loc + services_loc

    # call ORS matrix (may be time-consuming)
    durations, distances = build_matrix(locations)
    # durations shape: (G+N) x (G+N) ; we need G x N (garage rows to service cols)
    G = len(garages_loc)
    N = len(services_loc)
    # extract GxN minutes matrix
    time_g2s = []
    for i in range(G):
        row = []
        for j in range(G, G+N):
            sec = durations[i][j]
            minutes = sec/60.0 if sec is not None else 1e9
            row.append(minutes)
        time_g2s.append(row)

    # compute prioritized df
    df_prior = prioritize(services_df.assign(tipo=services_df['type']), time_matrix_from_garages=time_g2s, now=now)
    # return top 100 for preview
    preview = df_prior.head(200).to_dict(orient='records')
    return jsonify({"status":"ok", "preview": preview, "n_services": len(df_prior)})

@app.route("/api/assign/run", methods=["POST"])
def run_assignment():
    """
    Run full flow: prioritize -> assign -> save result
    Accept optional JSON with 'now' and 'params' (weights).
    """
    data = request.json or {}
    now = pd.to_datetime(str(data.get('now'))) if data.get('now') else pd.Timestamp.utcnow()

    services_df = load_services()
    shifts_df = load_shifts()
    garages_df = load_garages()

    # build locations for matrix
    garages_loc = garages_df[['lon','lat']].values.tolist()
    services_loc = services_df[['lon','lat']].values.tolist()
    locations = garages_loc + services_loc

    durations, distances = build_matrix(locations)
    G = len(garages_loc)
    N = len(services_loc)
    time_g2s = []
    for i in range(G):
        row = []
        for j in range(G, G+N):
            sec = durations[i][j]
            minutes = sec/60.0 if sec is not None else 1e9
            row.append(minutes)
        time_g2s.append(row)

    # prioritize
    df_prior = prioritize(services_df.assign(tipo=services_df['type']), time_matrix_from_garages=time_g2s, now=now)

    # assign
    assignments, remaining = greedy_assign(df_prior, garages_df, shifts_df, time_g2s)
    # compute simple metrics
    metrics = {
        "n_services": len(df_prior),
        "n_assigned": sum(len(v) for v in assignments.values()),
        "remaining_minutes_per_crew": remaining
    }
    params = {"now": str(now)}
    # save run result
    run_id = save_run_result(params=params, metrics=metrics, solution=assignments)
    return jsonify({"status":"ok", "run_id": run_id, "metrics": metrics, "assignments": assignments})
