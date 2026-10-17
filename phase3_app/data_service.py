"""CSV boundaries for the actual Streamlit/Python connection; no model inference."""
from io import StringIO
import re
import numpy as np
import pandas as pd

MAX_BYTES=5*1024*1024

def read_dataset(text):
    if len(text.encode('utf-8'))>MAX_BYTES:raise ValueError('Use a CSV smaller than 5 MB.')
    df=pd.read_csv(StringIO(text),dtype=str,keep_default_na=False)
    if df.empty:raise ValueError('The CSV must contain at least one data row.')
    if len(df)>5000:raise ValueError('Use no more than 5,000 rows for this interface.')
    if len(df.columns)>100:raise ValueError('Use no more than 100 columns.')
    if any(not str(c).strip() for c in df.columns):raise ValueError('Every column needs a name.')
    return df

def read_predictions(text):
    df=read_dataset(text)
    required=['patient_id','date','risk_score','risk_level']
    if not set(required).issubset(df.columns):raise ValueError('Predictions need patient_id, date, risk_score, risk_level.')
    if df[required].apply(lambda s:s.str.strip().eq('')).any().any():raise ValueError('Required prediction fields cannot be empty.')
    if not df['date'].str.fullmatch(r'\d{4}-\d{2}-\d{2}').all():raise ValueError('Prediction dates must use YYYY-MM-DD.')
    dates=pd.to_datetime(df['date'],errors='coerce')
    if dates.isna().any():raise ValueError('A prediction date is invalid.')
    scores=pd.to_numeric(df.risk_score,errors='coerce')
    if not np.isfinite(scores).all() or not scores.between(0,100).all():raise ValueError('risk_score must be a finite number from 0 to 100; do not supply 0-1 fractions as percentages.')
    df['patient_id']=df['patient_id'].str.strip()
    if (df.patient_id.str.len()>100).any():raise ValueError('Person IDs must be 100 characters or shorter.')
    if df.duplicated(['patient_id','date']).any():raise ValueError('Use one prediction per person per date.')
    df['risk_score']=scores
    df['risk_level']=df['risk_level'].str.strip().str.title()
    if not df.risk_level.isin(['Low','Moderate','High']).all():raise ValueError('risk_level must be Low, Moderate or High, supplied by your model team.')
    for col in ['reason_1','reason_2','reason_3']:
        if col not in df:df[col]='Not supplied by the model.'
        df[col]=df[col].replace('', 'Not supplied by the model.')
    return df[['patient_id','date','risk_score','risk_level','reason_1','reason_2','reason_3']].sort_values(['patient_id','date']).reset_index(drop=True)

def placeholder_results():
    # Isolated UI placeholder series, with no profile or posts.
    return [{'patient_id':'PLACEHOLDER','date':f'2026-{i:02d}-28','risk_score':s,'risk_level':'High' if i==6 else 'Moderate','reason_1':'Placeholder reason 1','reason_2':'Placeholder reason 2','reason_3':'Placeholder reason 3'} for i,s in enumerate([22,35,44,58,69,78],1)]

def preview_records(df):
    return df.head(8).fillna('').astype(str).to_dict('records')


def read_senior_posts(text):
    """Validate an unprocessed submission; do not treat it as notebook output."""
    df=read_dataset(text)
    id_col='patient_id' if 'patient_id' in df else 'patient'
    required={id_col,'date','text'}
    if not required.issubset(df.columns):
        raise ValueError('Use patient_id, date and text columns.')
    ids=df[id_col].str.strip()
    if ids.eq('').any() or ids.nunique()!=1:
        raise ValueError('Please upload posts for one person only.')
    if df.text.str.strip().eq('').any():
        raise ValueError('Each post needs text.')
    if not df.date.str.fullmatch(r'\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?').all():
        raise ValueError('Use YYYY-MM-DD or YYYY-MM-DD HH:MM dates.')
    dates=pd.to_datetime(df.date,format='mixed',errors='coerce')
    if dates.isna().any():raise ValueError('A post date is invalid.')
    return df,{'posts':len(df),'start':str(dates.min().date()),'end':str(dates.max().date())}
