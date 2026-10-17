"""Editable four-page interface. Static preview contains placeholders only."""
from pathlib import Path
import base64,json
import pandas as pd
from data_service import placeholder_results
from reports import make_report
from phase1_adapter import build_phase1,REPO
ROOT=Path(__file__).resolve().parent

def data_uri(path,mime):return f'data:{mime};base64,'+base64.b64encode(path.read_bytes()).decode('ascii')

def build_payload(results=None,dataset=None,active_page='senior',selected_id=None,notice='',connected=False):
    is_placeholder=results is None
    rows=placeholder_results() if results is None else results
    ids=list(dict.fromkeys(r['patient_id'] for r in rows))
    pid=selected_id if selected_id in ids else (ids[0] if ids else None)
    report=make_report(pid,[r for r in rows if r['patient_id']==pid],is_placeholder) if pid and any(r['date'] for r in rows) else None
    precision=85/95;recall=85/100
    return {'results':rows,'isPlaceholder':is_placeholder,'activePage':active_page,'selectedId':pid,
        'dataset':dataset,'notice':notice,'connected':connected,'phase1':build_phase1({}),'phase1_figures':[],
        'metrics':{str(k).replace('AUC','ROC AUC').replace('Sensitivity (recall)','Sensitivity'):float(v) for k,v in pd.read_csv(ROOT/'data/phase2/final_test_metrics.csv',index_col=0)['value'].items()},
        'evaluationImages':{name:data_uri(ROOT/('assets/evaluation/'+name+'.png'),'image/png') for name in ['final_test','feature_importance','roc_top3']},
        'assets':{'logo':data_uri(ROOT/'assets/logo/neorora-logo.jpg','image/jpeg'),'mark':data_uri(ROOT/'assets/logo/neorora-mark.svg','image/svg+xml'),'landscape':data_uri(ROOT/'assets/landscape.svg','image/svg+xml')},
        'pdfs':{pid:'data:application/pdf;base64,'+base64.b64encode(report).decode('ascii')} if report else {}}

def build_html(payload=None):
    payload=build_payload(results=[]) if payload is None else payload
    payload=dict(payload)
    payload['phase1_figures']=[]
    text=(ROOT/'ui/index.html').read_text(encoding='utf-8')
    for key,value in {'__STYLES__':(ROOT/'ui/styles.css').read_text(encoding='utf-8'),'__SCRIPT__':(ROOT/'ui/app.js').read_text(encoding='utf-8'),'__DATA_JSON__':json.dumps(payload,ensure_ascii=True).replace('<','\\u003c')}.items():text=text.replace(key,value)
    return text

def write_preview():
    from phase2_adapter import load_predictions
    from phase1_adapter import load_local
    results,error=load_predictions()
    payload=build_payload(results=results)
    payload['phase1']=build_phase1(load_local()[0])
    html=build_html(payload) # includes the explicitly supplied de-identified assessment records
    (ROOT/'OPEN_PREVIEW.html').write_text(html,encoding='utf-8')
    (ROOT/'component').mkdir(exist_ok=True)
    (ROOT/'component/index.html').write_text(html,encoding='utf-8')

if __name__=='__main__':write_preview();print('Ready: browser preview and Streamlit interface.')
