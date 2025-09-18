# backend/app/db_utils.py
from .models import SessionLocal, RunResult

from datetime import datetime
import json

def save_run_result(params: dict, metrics: dict, solution: dict):
    db = SessionLocal()
    rr = RunResult(created_at=datetime.utcnow(),
                   params=params,
                   metrics=metrics,
                   solution=solution)
    db.add(rr)
    db.commit()
    db.close()
    return rr.id
