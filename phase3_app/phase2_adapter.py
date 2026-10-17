"""Display the team's saved outputs, without training or inventing assessments."""
from pathlib import Path
from io import StringIO
import pandas as pd
import numpy as np
from phase1_adapter import APP, REPO

def read_saved_predictions(text):
    df=pd.read_csv(StringIO(text),dtype={'patient':str},keep_default_na=False)
    required={'patient','risk_percent','risk_level','reason_1','reason_2','reason_3'}
    if not required.issubset(df):raise ValueError('Prediction export is missing required columns.')
    if df.empty or df.patient.str.strip().eq('').any() or df.patient.duplicated().any():
        raise ValueError('Predictions must contain one row per patient.')
    scores=pd.to_numeric(df.risk_percent,errors='coerce')
    if not np.isfinite(scores).all() or not scores.between(0,100).all():raise ValueError('Invalid prediction scores.')
    if not df.risk_level.isin(['Low','Medium','High']).all():raise ValueError('Invalid model score band.')
    records=[]
    for (_,r),score in zip(df.iterrows(),scores):
        records.append({'patient_id':r.patient.strip(),'date':'','risk_score':float(score),
                        'risk_level':r.risk_level,'predicted_label':int(r.risk_level=='High'),
                        **{f'reason_{i}':str(r[f'reason_{i}']) for i in range(1,4)}})
    return records

def load_predictions():
    for path in [REPO/'data/processed/predictions.csv',APP/'data/phase2/predictions.csv']:
        if path.is_file():
            try:return read_saved_predictions(path.read_text(encoding='utf-8-sig')),None
            except (ValueError,TypeError) as exc:return [],str(exc)
    return [],None
