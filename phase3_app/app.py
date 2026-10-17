"""Four-page Streamlit app with a real bidirectional Python data connection."""
from phase2_adapter import load_predictions
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
from data_service import read_dataset,read_predictions,preview_records,read_senior_posts
from build_preview import ROOT,build_payload,write_preview
from phase1_adapter import guess_kind,read_artifact,load_local,validate_collection,build_phase1
st.set_page_config(page_title='NEORORA · Cognitive Compass',page_icon='🧭',layout='wide',initial_sidebar_state='collapsed')
st.markdown('''<style>
header[data-testid="stHeader"]{display:none}
.block-container{padding:0!important;max-width:100%!important}
.stApp{background:#e6f1f8} iframe{border:0;display:block}
[data-testid="stElementContainer"]{margin:0}
[data-testid="stVerticalBlock"]{gap:0}
</style>''',unsafe_allow_html=True)
if not (ROOT/'component/index.html').exists():write_preview()
ui=components.declare_component('neorora_interface',path=str(ROOT/'component'))
s=st.session_state
if 'phase1_frames' not in s:
    s.phase1_frames,local_notes=load_local()
    if local_notes:s.notice='Some patient records could not be loaded.'
s.setdefault('active_page','senior');s.setdefault('selected_id',None);s.setdefault('notice','')
results,prediction_error=load_predictions()
if prediction_error:st.error('The saved assessment file could not be read. Ask the project team to check predictions.csv.')
summary=None
if 'dataset' in s:
    df=s['dataset'];summary={'name':s.get('dataset_name','CSV'),'rows':len(df),'columns':list(df.columns),'preview':preview_records(df),'location':'Python / Streamlit session'}
payload=build_payload(results,summary,s.active_page,s.selected_id,s.notice,connected=True)
payload['phase1']=build_phase1(s.phase1_frames)
payload['upload_summary']=s.get('upload_summary')
payload['senior_result']=s.get('senior_result')
if s.get('submitted_prediction'):
    payload['results']=[*payload['results'],s.submitted_prediction]
if s.get('submitted_patient'):
    payload['phase1']['patients']=[*payload['phase1']['patients'],s.submitted_patient]
    payload['phase1']['patient_ids']=[*payload['phase1']['patient_ids'],s.submitted_patient['patient']]
    payload['selectedId']=s.selected_id or s.submitted_patient['patient']
if payload['phase1']['patient_ids']:
    payload['selectedId']=s.selected_id if s.selected_id in payload['phase1']['patient_ids'] else (results[0]['patient_id'] if results else payload['phase1']['patient_ids'][0])
event=ui(payload=payload,key='neorora_interface',default=None)
if isinstance(event,dict) and event.get('event_id')!=s.get('last_event'):
    s.last_event=event.get('event_id')
    page=event.get('page','senior');s.active_page=page if page in ['senior','clinician','researcher','about'] else 'senior'
    s.selected_id=event.get('selected_id',s.selected_id)
    try:
        action=event.get('action')
        if action=='upload_phase1':
            kind=event.get('artifact_kind','auto')
            if kind=='auto':kind=guess_kind(event.get('csv',''),event.get('filename',''))
            frame=read_artifact(event.get('csv',''),kind)
            candidate={**s.phase1_frames,kind:frame};validate_collection(candidate)
            s.phase1_frames=candidate
            s.notice='Your file has been received. Patient records have been updated.'
        elif action=='upload_dataset':
            if s.active_page=='senior' and event.get('consent') is not True:raise ValueError('Agreement is required before uploading from the Senior page.')
            kind=guess_kind(event.get('csv',''),event.get('filename','')) if s.active_page!='senior' else None
            if s.active_page=='senior':
                for key in ['upload_summary','senior_result','submitted_prediction','submitted_patient']:s.pop(key,None)
                posts,receipt=read_senior_posts(event.get('csv',''))
                # Clear the previous assessment before handling a replacement submission.
                for key in ['senior_result','submitted_prediction','submitted_patient']:s.pop(key,None)
                s.senior_posts=posts
                s.upload_summary={**receipt,'name':str(event.get('filename','Posts CSV'))[:150]}
                s.notice='Your posts have been received.'
                if not posts.date.str.contains(r'[ T]\d{2}:\d{2}',regex=True).all():
                    s.upload_summary['status']='Please include each post’s original time as well as its date so we can assess posting patterns.'
                else:
                    from uuid import uuid4
                    from post_processing import prepare_posts,extract_features
                    from predictor import predict
                    from phase2_adapter import read_saved_predictions
                    anonymous='SUB-'+uuid4().hex[:8].upper()
                    posts=posts.rename(columns={'patient_id':'patient'});posts['patient']=anonymous
                    clean=prepare_posts(posts)
                    feature_frame=extract_features(clean)
                    result=read_saved_predictions(predict(feature_frame).to_csv(index=False))[0]
                    s.submitted_prediction=result;s.senior_result=result
                    # Only aggregate measurements go to the interface; raw text stays server-side.
                    frames={'features_test':feature_frame,'clean_posts':clean}
                    s.submitted_patient=build_phase1(frames)['patients'][0]
                    s.submitted_patient['metadata']['label']=None
                    s.selected_id=anonymous
                    s.upload_summary['status']='Your screening summary is ready.'
                    s.notice='Your screening summary is ready.'
            elif kind:
                frame=read_artifact(event.get('csv',''),kind)
                candidate={**s.phase1_frames,kind:frame};validate_collection(candidate)
                s.phase1_frames=candidate
                s.notice='Your file has been received. Patient records have been updated.'
            else:
                s.dataset=read_dataset(event.get('csv',''));s.dataset_name=str(event.get('filename','Dataset CSV'))[:150]
                s.notice='Your posts have been received. An assessment is not available yet.'
        elif action=='upload_predictions':
            s.predictions=read_predictions(event.get('csv',''));s.selected_id=s.predictions.iloc[0]['patient_id']
            s.notice=f'Imported {len(s.predictions)} prediction rows. Clinician values now use this file.'
        elif action=='clear_data':
            for key in ['dataset','dataset_name','predictions','senior_posts','upload_summary','senior_result','submitted_prediction','submitted_patient']:s.pop(key,None)
            s.phase1_frames={}
            s.selected_id=None;s.notice='Session uploads cleared. Showing placeholder values.'
    except ValueError as exc:s.notice='Upload error: '+str(exc)
    except Exception:
        import logging
        logging.exception('Screening submission could not be processed')
        s.notice='Upload error: We could not complete the screening. Please try again or contact the project team.'
    st.rerun()
