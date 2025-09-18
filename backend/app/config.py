# backend/app/config.py
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# ORS
ORS_URL = os.getenv("ORS_URL", "http://localhost:8080/ors/v2")
# DB (reuse sua configuração; exemplo sqlite local)
DATABASE_URI = os.getenv("DATABASE_URI", f"sqlite:///{os.path.join(BASE_DIR,'../database/rotas.db')}")

# Local paths expected (ajuste conforme sua organização)
PATH_SERVICOS_PARQUET = os.getenv("PATH_SERVICOS_PARQUET", os.path.join(BASE_DIR,"../data/raw/services.parquet"))
PATH_ESCALAS_PARQUET  = os.getenv("PATH_ESCALAS_PARQUET",  os.path.join(BASE_DIR,"../data/raw/shifts.parquet"))
PATH_GARAGENS_XLSX    = os.getenv("PATH_GARAGENS_XLSX",  os.path.join(BASE_DIR,"../data/raw/garages.xlsx"))
PATH_EUSD_PARQUET     = os.getenv("PATH_EUSD_PARQUET",   os.path.join(BASE_DIR,"../data/raw/eusd.parquet"))

# Prioritization weights (initial guess, tune later)
WEIGHT_URGENCY = 0.35
WEIGHT_PENALTY = 0.35
WEIGHT_RECOV = 0.20
WEIGHT_DISTANCE = 0.10

# effective recovery for tipo 3
EFFECTIVITY_3 = 0.57
