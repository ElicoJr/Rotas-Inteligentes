# backend/app/ors_client.py
import requests
from .config import ORS_URL

def build_matrix(locations, metrics=["duration","distance"], timeout=120):
    """
    locations: list of [lon, lat] pairs
    returns durations (seconds) and distances (meters) (as returned)
    """
    url = ORS_URL.rstrip('/') + "/matrix/driving-car"
    body = {
        "locations": locations,
        "metrics": metrics,
        "units": "km"
    }
    resp = requests.post(url, json=body, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    return data.get("durations"), data.get("distances")
