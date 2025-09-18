# backend/app/prioritizer.py
import numpy as np
import pandas as pd
from datetime import datetime
from .config import WEIGHT_URGENCY, WEIGHT_PENALTY, WEIGHT_RECOV, WEIGHT_DISTANCE, EFFECTIVITY_3

def compute_penalty(row):
    """
    Row must have tipo and gammas and end_time (if available) or estimate lateness.
    We'll estimate penalty per minute by gamma fields; user must calibrate gamma1/gamma2.
    """
    tipo = int(row['tipo'])
    # assume gamma1, gamma2, gamma3 columns exist; fallback to defaults
    if tipo == 1:
        gamma = float(row.get('gamma1', 0.0))
    elif tipo == 2:
        gamma = float(row.get('gamma2', 0.0))
    else:
        gamma = float(row.get('gamma3', 0.0))
    # compute minutes until due from now (if sim time provided elsewhere); here use request_time->due_time gap as urgency
    return gamma

def normalize_series(s):
    s = np.array(s, dtype=float)
    mn, mx = s.min(), s.max()
    if mx - mn < 1e-9:
        return np.zeros_like(s)
    return (s - mn) / (mx - mn)

def prioritize(df_services, time_matrix_from_garages=None, now=None):
    """
    df_services: pandas DataFrame with required fields:
      - tipo (1,2,3)
      - request_time (datetime)
      - due_time (datetime)
      - duration_min
      - monetary_value (for tipo 3)
      - lat, lon
      - gamma1, gamma2, gamma3 (optional)
    time_matrix_from_garages: optional list/array of travel times from each garage to each service (in minutes)
      shape: (G, N)
    Returns df with columns: score, urgency_norm, penalty_norm, recov_norm, dist_norm
    """
    now = now or pd.Timestamp.utcnow()
    df = df_services.copy()
    # urgency: reciprocal of minutes until due (soonest => highest)
    df['mins_to_due'] = (df['due_time'] - now).dt.total_seconds() / 60.0
    # negative mins_to_due => already late; treat as 0
    df['mins_to_due_clip'] = df['mins_to_due'].clip(upper=1e9)
    # transform: larger => more urgent -> use 1/(1+mins)
    df['urgency'] = 1.0 / (1.0 + np.maximum(df['mins_to_due_clip'], 0.0))
    # penalty factor: gamma * expected lateness (we don't have planned end, so use gamma alone as proxy)
    df['penalty_proxy'] = df.apply(compute_penalty, axis=1)
    # benefit (tipo 3)
    df['recov'] = df.apply(lambda r: r['monetary_value'] * EFFECTIVITY_3 if int(r['tipo'])==3 else 0.0, axis=1)
    # distance proxy: if matrix provided, use min across garages; else compute Haversine or zero
    if time_matrix_from_garages is not None:
        # time_matrix_from_garages: G x N (minutes)
        mins = np.min(time_matrix_from_garages, axis=0)
        df['dist_proxy'] = mins
    else:
        df['dist_proxy'] = 0.0

    # normalize components
    df['urg_norm'] = normalize_series(df['urgency'].values)
    df['pen_norm'] = normalize_series(df['penalty_proxy'].values)
    df['rec_norm'] = normalize_series(df['recov'].values)
    df['dist_norm'] = normalize_series(df['dist_proxy'].values)

    # final score (higher => more priority)
    df['score'] = (WEIGHT_URGENCY * df['urg_norm']
                   + WEIGHT_PENALTY * df['pen_norm']
                   + WEIGHT_RECOV * df['rec_norm']
                   - WEIGHT_DISTANCE * df['dist_norm'])
    # sort descending by score
    df = df.sort_values('score', ascending=False).reset_index(drop=True)
    return df
