"""Read the team's notebook exports without executing or changing its notebooks."""
from pathlib import Path
from io import StringIO
import math
import numpy as np
import pandas as pd

APP=Path(__file__).resolve().parent
REPO=APP.parent
FEATURES=['own_posts','avg_words_per_post','avg_word_length','avg_sentence_length','mattr','hapax_ratio','pronoun_ratio','filler_ratio','repetition_rate','n_posts','night_post_ratio','emoji_per_post','elongation_per_post','english_share','copied_share','active_months','posts_per_month','mattr_change','avg_words_per_post_change','avg_sentence_length_change','pronoun_ratio_change','filler_ratio_change','repetition_rate_change']
PATHS={'features_train':'data/processed/features_train.csv','features_test':'data/processed/features_test.csv','patient_info':'data/processed/patient_info.csv','clean_posts':'data/interim/clean_posts.csv','cleaning_funnel':'phase1_data/cleaning_funnel.csv','nlp_funnel':'phase1_data/nlp_funnel.csv'}
LABEL_NOTE='Notebook target: 0 = Normal; 1 = MCI or Dementia. This is not dementia-only classification.'

def guess_kind(text,filename=''):
    head=set(pd.read_csv(StringIO(text),nrows=0).columns)
    if {'patient','mattr','avg_words_per_post'}.issubset(head):return 'features_test' if 'test' in filename.lower() else 'features_train'
    if {'patient','group','moca','split'}.issubset(head):return 'patient_info'
    if {'patient','date','text'}.issubset(head):return 'clean_posts'
    if {'step','rows','patients'}.issubset(head):return 'nlp_funnel' if 'nlp' in filename.lower() else 'cleaning_funnel'
    return None

def read_artifact(text,kind):
    if kind not in PATHS:raise ValueError('Choose a recognised Phase 1 artifact type.')
    if len(text.encode('utf-8'))>50*1024*1024:raise ValueError('Phase 1 CSV limit is 50 MB.')
    df=pd.read_csv(StringIO(text),dtype={'patient':str},encoding='utf-8-sig')
    if df.empty:raise ValueError('The artifact is empty.')
    if len(df)>250000:raise ValueError('Maximum 250,000 rows per Phase 1 artifact.')
    required={'patient'}
    if kind.startswith('features'):required|={'mattr','avg_words_per_post','avg_sentence_length','repetition_rate'}
    elif kind=='patient_info':required|={'group','moca','split','label'}
    elif kind=='clean_posts':required|={'date','text'}
    else:required={'step','rows','patients'}
    if not required.issubset(df.columns):raise ValueError('Missing columns: '+', '.join(sorted(required-set(df.columns))))
    if 'patient' in required:
        if df.patient.isna().any() or df.patient.str.strip().eq('').any():raise ValueError('Every row needs a patient ID.')
        df.patient=df.patient.str.strip()
        if kind!='clean_posts' and df.patient.duplicated().any():raise ValueError('Feature/metadata exports need one row per patient.')
    for col in [c for c in FEATURES if c in df]+(['label'] if 'label' in df else []):
        source=df[col];num=pd.to_numeric(source,errors='coerce')
        if (source.notna()&num.isna()).any() or np.isinf(num.dropna()).any():raise ValueError(f'{col} contains invalid numeric values.')
        df[col]=num
    if 'label' in df and not df.label.dropna().isin([0,1]).all():raise ValueError('The notebook label must be 0 or 1.')
    if kind=='clean_posts':
        df['date']=pd.to_datetime(df.date,errors='coerce')
        if df.date.isna().any():raise ValueError('Clean-post export contains invalid dates; correct the upstream export.')
    if kind.endswith('funnel'):
        for c in ['rows','patients']:
            df[c]=pd.to_numeric(df[c],errors='raise')
            if df[c].isna().any() or (df[c]<0).any():raise ValueError('Funnel counts must be non-negative numbers.')
    return df

def validate_collection(frames):
    if 'features_train' in frames and 'features_test' in frames:
        overlap=set(frames['features_train'].patient)&set(frames['features_test'].patient)
        if overlap:raise ValueError('Train/test IDs overlap. Keep the notebook patient-level split intact.')

def load_local():
    frames={};notes=[]
    for kind,relative in PATHS.items():
        path=REPO/relative
        if not path.is_file():path=APP/'data/phase1'/Path(relative).name
        if path.is_file():
            try:frames[kind]=read_artifact(path.read_text(encoding='utf-8-sig'),kind)
            except Exception as exc:notes.append(f'{path.name}: {exc}')
    try:validate_collection(frames)
    except ValueError as exc:
        notes.append(str(exc));frames.pop('features_test',None)
    return frames,notes

def scalar(value):
    if pd.isna(value):return None
    if isinstance(value,(int,float,np.number)):
        return float(value) if math.isfinite(float(value)) else None
    return str(value)

def build_phase1(frames):
    validate_collection(frames)
    parts=[]
    for split in ['train','test']:
        key='features_'+split
        if key in frames:
            d=frames[key].copy();d['split']=split;parts.append(d)
    features=pd.concat(parts,ignore_index=True) if parts else pd.DataFrame()
    info=frames.get('patient_info',pd.DataFrame());posts=frames.get('clean_posts',pd.DataFrame())
    ids=set()
    for df in [features,info,posts]:
        if 'patient' in df:ids.update(df.patient.tolist())
    # Keep all post text server-side. Browser payload contains aggregate features only.
    info_by=info.set_index('patient').to_dict('index') if len(info) else {}
    feature_by=features.set_index('patient').to_dict('index') if len(features) else {}
    monthly={};post_counts={}
    if len(posts):
        work=posts.assign(month=posts.date.dt.strftime('%Y-%m'))
        post_counts=work.groupby('patient').size().to_dict()
        monthly={pid:[{'month':str(m),'posts':int(n)} for m,n in g.groupby('month').size().items()] for pid,g in work.groupby('patient')}
    patients=[]
    for pid in sorted(ids):
        feat=feature_by.get(pid,{});meta=info_by.get(pid,{})
        meta={k:meta.get(k,feat.get(k)) for k in ['group','moca','split','label']}
        own=feat.get('own_posts')
        enough=None if own is None or pd.isna(own) else bool(float(own)>=10)
        patients.append({'patient':pid,'features':{c:scalar(feat[c]) for c in FEATURES if c in feat},'metadata':{k:scalar(v) for k,v in meta.items()},'monthly':monthly.get(pid,[]),'post_count':int(post_counts[pid]) if pid in post_counts else None,'change_supported':enough})
    train=features[features.split=='train'] if len(features) else pd.DataFrame()
    cohort_means={c:scalar(pd.to_numeric(train[c],errors='coerce').mean()) for c in FEATURES if c in train} if len(train) else {}
    funnels={kind:[{k:scalar(v) for k,v in row.items()} for row in df.to_dict('records')] for kind,df in frames.items() if kind.endswith('funnel')}
    return {'patient_ids':sorted(ids),'patients':patients,'loaded':list(frames),'target_note':LABEL_NOTE,'feature_columns':FEATURES,'train_count':int(len(train)),'test_count':int(len(features)-len(train)),'post_count':int(len(posts)) if len(posts) else None,'train_means':cohort_means,'funnels':funnels,'metadata_excluded':['patient','group','moca','split','label'],'missing':[relative for kind,relative in PATHS.items() if kind not in frames]}
