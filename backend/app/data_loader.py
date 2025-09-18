# backend/app/data_loader.py
import pandas as pd
from .config import PATH_SERVICOS_PARQUET, PATH_ESCALAS_PARQUET, PATH_GARAGENS_XLSX, PATH_EUSD_PARQUET

def load_services(path=None):
    path = path or PATH_SERVICOS_PARQUET
    df = pd.read_parquet(path)
    # Expect columns: tipo, request_time, due_time, exec_time, alloc_time, check_time, end_time, lat, lon, ext_id, duration_min, monetary_value, ...
    # normalize column names if needed
    df['request_time'] = pd.to_datetime(df['request_time'])
    df['due_time'] = pd.to_datetime(df['due_time'])
    # ensure numeric duration
    if 'duration_min' in df.columns:
        df['duration_min'] = df['duration_min'].fillna(30).astype(int)
    else:
        df['duration_min'] = 30
    return df

def load_shifts(path=None):
    path = path or PATH_ESCALAS_PARQUET
    df = pd.read_parquet(path)
    # Expect columns: crew, start, end, garage (id or name)
    df['start'] = pd.to_datetime(df['start'])
    df['end'] = pd.to_datetime(df['end'])
    # compute available minutes
    df['shift_minutes'] = (df['end'] - df['start']).dt.total_seconds() / 60.0
    return df

def load_garages(path=None):
    path = path or PATH_GARAGENS_XLSX
    # supports xlsx or csv
    if path.lower().endswith('.xlsx') or path.lower().endswith('.xls'):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path)
    # expect columns: garage_id/name, lat, lon
    return df

def load_eusd(path=None):
    path = path or PATH_EUSD_PARQUET
    df = pd.read_parquet(path)
    # expect: chave_unidade, ano, mes, eusd_value
    return df
