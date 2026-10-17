/* Interface interactions. Imported assessments are separate from writing measurements. */
'use strict';
let DATA=JSON.parse(document.getElementById('app-data').textContent);
const $=id=>document.getElementById(id);
const esc=v=>String(v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const paths={
 upload:'<path d="M7 17H5a4 4 0 0 1-1-7.87A7 7 0 0 1 17.7 7.6 4.7 4.7 0 0 1 19 17h-2"/><path d="m8 12 4-4 4 4M12 8v13"/>',
 download:'<path d="M12 3v12m-4-4 4 4 4-4M5 16v5h14v-5"/>',
 flask:'<path d="M9 3h6M10 3v6L4 19a1.3 1.3 0 0 0 1.1 2h13.8a1.3 1.3 0 0 0 1.1-2L14 9V3M8 14h8"/><path d="M9 17h.01M14 18h.01"/>',
 alert:'<path d="m12 2 11 20H1z" fill="currentColor" stroke="none"/><path d="M12 8v6m0 3v.2" stroke="white" stroke-width="2.5"/>',
 shield:'<path d="m12 2 9 4v6c0 6-9 10-9 10S3 18 3 12V6z" fill="currentColor" stroke="none"/><path d="m8 12 3 3 6-7" stroke="white" stroke-width="2.3"/>',
 people:'<circle cx="12" cy="6" r="3" fill="currentColor" stroke="none"/><circle cx="4" cy="8" r="2" fill="currentColor" stroke="none"/><circle cx="20" cy="8" r="2" fill="currentColor" stroke="none"/><path d="M6 22v-4a6 6 0 0 1 12 0v4zM1 20v-4a3 3 0 0 1 3-3M23 20v-4a3 3 0 0 0-3-3" fill="currentColor" stroke="none"/>',
 person:'<circle cx="12" cy="6" r="4" fill="currentColor" stroke="none"/><path d="M4 22v-3a8 8 0 0 1 16 0v3z" fill="currentColor" stroke="none"/>',
 document:'<path d="M5 2h10l5 5v15H5z" fill="currentColor" stroke="none"/><path d="M8 11h9M8 15h9M8 19h6M14 3v5h5" stroke="white" stroke-width="1.5"/>'};
function icon(name){return `<svg class="icon" viewBox="0 0 24 24" aria-hidden="true">${paths[name]||paths.document}</svg>`}
document.querySelectorAll('[data-icon]').forEach(el=>el.outerHTML=icon(el.dataset.icon));
$('brand-mark').src=DATA.assets.mark;$('full-logo').src=DATA.assets.logo;
document.documentElement.style.setProperty('--landscape',`url("${DATA.assets.landscape}")`);
let bridge=false,currentPage='senior',receivedBackend=false;
const pages={senior:'Senior',clinician:'Clinician',researcher:'Researcher',about:'About & Privacy'};
function post(type,extra={}){if(window.parent!==window)window.parent.postMessage({isStreamlitMessage:true,type,...extra},'*')}
function size(){if(bridge)post('streamlit:setFrameHeight',{height:Math.ceil(document.body.scrollHeight)})}
function send(action,extra={}){
 if(!bridge)return false;
 post('streamlit:setComponentValue',{value:{action,page:currentPage,selected_id:$('patient-select').value,event_id:Date.now()+'-'+Math.random(),...extra},dataType:'json'});return true;
}
function navigate(page,notify=true){
 if(!(page in pages))page='senior';currentPage=page;
 document.querySelectorAll('main>.page').forEach(el=>el.hidden=el.id!=='page-'+page);
 document.querySelectorAll('.nav-button').forEach(btn=>{const active=btn.dataset.page===page;btn.classList.toggle('active',active);if(active)btn.setAttribute('aria-current','page');else btn.removeAttribute('aria-current')});
 document.title='NEORORA · '+pages[page];try{history.replaceState(null,'','#'+page)}catch{}
 window.scrollTo(0,0);size();
}
document.querySelectorAll('.nav-button').forEach(btn=>btn.addEventListener('click',()=>navigate(btn.dataset.page)));
document.querySelector('.brand').addEventListener('click',e=>{e.preventDefault();navigate('senior')});
function downloadBlob(content,mime,name){const url=URL.createObjectURL(new Blob([content],{type:mime}));const a=document.createElement('a');a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),10000)}
function decodeURIBytes(uri){return Uint8Array.from(atob(uri.split(',')[1]),c=>c.charCodeAt(0))}
function personRows(pid){return DATA.results.filter(r=>r.patient_id===pid).sort((a,b)=>a.date.localeCompare(b.date))}
function parseCSV(text){
 text=text.replace(/^\uFEFF/,'');let rows=[],row=[],value='',quoted=false,after=false;
 function cell(){row.push(value);value='';after=false}function finish(){cell();if(row.some(v=>v.trim()!==''))rows.push(row);row=[]}
 for(let i=0;i<text.length;i++){const c=text[i];if(quoted){if(c==='"'){if(text[i+1]==='"'){value+='"';i++}else{quoted=false;after=true}}else value+=c;continue}if(c==='"'){if(value.length||after)throw Error('Unexpected quote.');quoted=true}else if(c===',')cell();else if(c==='\n'||c==='\r'){if(c==='\r'&&text[i+1]==='\n')i++;finish()}else{if(after&&!/\s/.test(c))throw Error('Unexpected text after quoted field.');if(!after)value+=c}}
 if(quoted)throw Error('A quoted field is not closed.');if(value.length||row.length||after)finish();if(rows.length<2)throw Error('The CSV needs headers and at least one data row.');const headers=rows.shift().map(s=>s.trim());if(headers.some(s=>!s)||new Set(headers).size!==headers.length)throw Error('Use unique, non-empty column names.');if(rows.length>5000||headers.length>100)throw Error('Maximum: 5,000 rows and 100 columns.');if(rows.some(r=>r.length!==headers.length))throw Error('CSV rows have different numbers of fields.');return {headers,rows:rows.map(r=>Object.fromEntries(headers.map((h,i)=>[h,r[i]])))};
}
function validatePredictions(parsed){
 const required=['patient_id','date','risk_score','risk_level'];if(required.some(k=>!parsed.headers.includes(k)))throw Error('Predictions need patient_id, date, risk_score, risk_level.');const seen=new Set();
 return parsed.rows.map(r=>{const pid=r.patient_id.trim(),date=r.date.trim(),raw=r.risk_score.trim(),score=Number(raw),level=r.risk_level.trim().toLowerCase();const d=new Date(date+'T00:00:00Z');if(!pid||pid.length>100||!raw||!Number.isFinite(score)||score<0||score>100)throw Error('Use a non-empty ID and a score from 0 to 100.');if(!/^\d{4}-\d{2}-\d{2}$/.test(date)||!Number.isFinite(d.getTime())||d.toISOString().slice(0,10)!==date)throw Error('Use valid YYYY-MM-DD dates.');if(!['low','moderate','high'].includes(level))throw Error('The model must supply Low, Moderate or High.');const key=JSON.stringify([pid,date]);if(seen.has(key))throw Error('Duplicate person/date.');seen.add(key);return {patient_id:pid,date,risk_score:score,risk_level:level[0].toUpperCase()+level.slice(1),reason_1:r.reason_1||'Not supplied by the model.',reason_2:r.reason_2||'Not supplied by the model.',reason_3:r.reason_3||'Not supplied by the model.'}});
}
async function upload(file,type,senior=false){
 if(!file)return;const feedback=$('upload-feedback');
 try{
  if(file.size>(bridge&&type==='dataset'?50:5)*1024*1024)throw Error('CSV exceeds the upload limit.');const text=await file.text();if(bridge){if(senior&&!$('consent').checked)return;send(type==='predictions'?'upload_predictions':'upload_dataset',{csv:text,filename:file.name,consent:senior?$('consent').checked:false});return;}const parsed=parseCSV(text);
  if(senior){const idKey=parsed.headers.includes('patient_id')?'patient_id':'patient';if(![idKey,'date','text'].every(k=>parsed.headers.includes(k)))throw Error('Use patient_id, date and text columns.');const ids=new Set(parsed.rows.map(r=>r[idKey].trim()));if(ids.size!==1||ids.has(''))throw Error('Please upload posts for one person only.');if(parsed.rows.some(r=>!r.text.trim()||!/^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}(?::\d{2})?)?$/.test(r.date)||!Number.isFinite(Date.parse(r.date))||new Date(r.date.length===10?r.date+'T00:00:00Z':r.date.replace(' ','T')+'Z').toISOString().slice(0,10)!==r.date.slice(0,10)))throw Error('Each post needs text and a valid date and time.');const dates=parsed.rows.map(r=>r.date).sort();DATA.upload_summary={posts:parsed.rows.length,start:dates[0],end:dates.at(-1),name:file.name};}
  if(senior&&!$('consent').checked)return;
  if(type==='predictions')validatePredictions(parsed);
  feedback.textContent=bridge?'Uploading your posts…':'Reading your file…';
  if(send(type==='predictions'?'upload_predictions':'upload_dataset',{csv:text,filename:file.name,consent:senior?$('consent').checked:false}))return;
  if(type==='dataset'){DATA.dataset={name:file.name,rows:parsed.rows.length,columns:parsed.headers,preview:parsed.rows.slice(0,8),location:'Browser preview only — run Streamlit for Python processing'};DATA.notice='Your file has been received. An assessment is not available yet.';if(senior)$('upload-feedback').textContent=DATA.notice}
  else{DATA.results=validatePredictions(parsed);DATA.isPlaceholder=false;DATA.selectedId=DATA.results[0].patient_id;DATA.pdfs={};DATA.notice='Predictions imported in the browser. Open Streamlit to generate a PDF for imported results.'}
  renderData();
 }catch(e){feedback.textContent='Upload error: '+e.message;size()}
}
$('consent').addEventListener('change',()=>{$('upload-button').disabled=!$('consent').checked;if(!$('consent').checked)$('upload-feedback').replaceChildren()});
$('upload-button').addEventListener('click',()=>{if($('consent').checked)$('posts-file').click()});
$('posts-file').addEventListener('change',e=>upload(e.target.files[0],'dataset',true));
function trendSVG(rows){
 const w=640,h=270,x0=46,y0=20,pw=575,ph=211,x=i=>rows.length===1?x0+pw/2:x0+i*pw/(rows.length-1),y=v=>y0+ph-v/100*ph;
 const pts=rows.map((r,i)=>`${x(i)},${y(r.risk_score)}`).join(' '),grid=[0,20,40,60,80,100].map(v=>`<line x1="${x0}" y1="${y(v)}" x2="${x0+pw}" y2="${y(v)}" stroke="#dae4ef"/><text x="${x0-16}" y="${y(v)+5}" text-anchor="end" font-size="15" fill="#294d79">${v}</text>`).join('');
 const labels=rows.map((r,i)=>{const show=rows.length<=8||i===0||i===rows.length-1||i%Math.ceil(rows.length/6)===0;return `<circle cx="${x(i)}" cy="${y(r.risk_score)}" r="5" fill="#1873e9"><title>${esc(r.date)}: ${r.risk_score}</title></circle>${show?`<text x="${x(i)}" y="${h-12}" text-anchor="middle" font-size="13" fill="#294d79">${esc(r.date.slice(0,7))}</text>`:''}`}).join('');
 return `<svg class="trend-chart" viewBox="0 0 ${w} ${h}" role="img" aria-label="${DATA.isPlaceholder?'Placeholder':'Imported'} score trend">${grid}<polygon points="${x(0)},${y(0)} ${pts} ${x(rows.length-1)},${y(0)}" fill="#b4d7fb55"/><polyline points="${pts}" fill="none" stroke="#186bdb" stroke-width="3"/>${labels}</svg>`;
}
function updateClinician(){
 const pid=$('patient-select').value,rows=personRows(pid);if(DATA.phase1?.patient_ids?.includes(pid))renderPhase1Patient(pid);
 if(DATA.isPlaceholder||!rows.length){clearPhase2();return;}
 $('assessment-section').hidden=false;
 const row=rows.at(-1),state=row.risk_level.toLowerCase(),score=row.risk_score/100;
 $('risk-box').className='risk-box '+(state==='medium'?'moderate':state);
 $('risk-box').querySelector('.status-dot').className='status-dot '+(state==='high'?'red':state==='medium'?'yellow':'');$('risk-level').textContent=row.risk_level+' model score band';$('risk-score').textContent=score.toFixed(3);$('score-label').textContent='Model score (0–1):';
 $('trend-title').textContent='Classification';
 $('trend-chart').innerHTML=`<h3>${row.predicted_label===1?'1 · MCI/Dementia class':'0 · Normal class'}</h3><p class="helper">Model classification, not a diagnosis.</p><div class="score-meter"><span style="width:${row.risk_score}%"></span></div><p class="helper">Decision threshold: 0.67. Score bands: Low below 0.50; Medium 0.50 to below 0.67; High 0.67 and above.</p><p class="helper">Assessment based on the available writing history.</p>`;
 $('reasons').innerHTML=[row.reason_1,row.reason_2,row.reason_3].map((r,i)=>`<li><span class="reason-number">${i+1}</span>${esc(r)}</li>`).join('');
 $('alert-banner').className='alert-banner '+(state==='high'?'':state==='medium'?'moderate':'low');$('alert-text').textContent=row.predicted_label===1?'Review the flagged screening result':'Review alongside the patient’s history';
 $('results-source').textContent='Patient assessments';
 $('clinical-note').textContent='Screening support, not a diagnosis. Score bands are not disease severity levels; a low score does not rule out impairment.';
 $('download-pdf').hidden=true;$('senior-result').replaceChildren();
}
$('patient-select').addEventListener('change',()=>{DATA.selectedId=$('patient-select').value;updateClinician();send('select_patient')});
$('download-pdf').addEventListener('click',()=>{const pid=$('patient-select').value;if(DATA.pdfs[pid])downloadBlob(decodeURIBytes(DATA.pdfs[pid]),'application/pdf','NEORORA_report.pdf')});
function renderData(){
 const phaseIds=DATA.phase1?.patient_ids||[];const ids=[...new Set([...phaseIds,...(DATA.isPlaceholder&&phaseIds.length?[]:DATA.results.map(r=>r.patient_id))])],current=DATA.selectedId||$('patient-select').value;
 $('patient-select').innerHTML=ids.map(id=>`<option value="${esc(id)}">${esc(id==='PLACEHOLDER'?'Placeholder case':id)}</option>`).join('');$('patient-select').value=ids.includes(current)?current:(ids[0]||'');updateClinician();
 $('metric-grid').innerHTML=Object.entries(DATA.metrics).map(([k,v])=>`<article class="panel metric"><div class="metric-label">${esc(k)}</div><div class="metric-value">${k==='ROC AUC'?v.toFixed(3):(v*100).toFixed(1)+'%'}</div></article>`).join('');
 $('test-evaluation').src=DATA.evaluationImages.final_test;$('feature-evaluation').src=DATA.evaluationImages.feature_importance;
 $('table-source').textContent=DATA.results.length?`${DATA.results.length} saved assessments. Recorded diagnoses are separate from predictions.`:'No saved patient assessments are available.';
 $('prediction-table').innerHTML=DATA.results.length?DATA.results.map(r=>`<tr><td>${esc(r.patient_id)}</td><td>${r.predicted_label===1?'1 · MCI/Dementia':'0 · Normal'}</td><td>${(r.risk_score/100).toFixed(3)} / ${esc(r.risk_level)}</td><td>Saved assessment</td></tr>`).join(''):'<tr><td colspan="4">Patient assessment results are not available yet.</td></tr>';
 if(DATA.notice)$('upload-feedback').textContent=DATA.notice.startsWith('Upload error:')?DATA.notice.replace('Upload error:','Please check your upload:'):'';
 renderPhase1();renderReceipt();renderSeniorResult();size();
}
window.addEventListener('message',event=>{
 if(event.source!==window.parent||event.data?.type!=='streamlit:render')return;
 bridge=true;DATA=event.data.args.payload;renderData();if(!receivedBackend){navigate(DATA.activePage,false);receivedBackend=true}size();
});
new ResizeObserver(()=>size()).observe(document.body);
renderData();navigate(location.hash.slice(1)||DATA.activePage,false);
if(window.parent!==window)post('streamlit:componentReady',{apiVersion:1});

// Phase 1 views consume the team's exported columns; they never assign disease risk.
function fmt(value,digits=3){return value===null||value===undefined?'Not available':typeof value==='number'?value.toLocaleString(undefined,{maximumFractionDigits:digits}):String(value)}
function featureName(key){return ({mattr:'Vocabulary richness (MATTR)',avg_words_per_post:'Words per post',avg_sentence_length:'Words per sentence',repetition_rate:'Repeated-bigram rate',filler_ratio:'Filler-word ratio',pronoun_ratio:'Pronoun ratio',own_posts:'Original posts',n_posts:'All cleaned posts',hapax_ratio:'Hapax ratio',night_post_ratio:'Night-post ratio',emoji_per_post:'Emoji count per post',copied_share:'Copied-content share'})[key]||key.replaceAll('_',' ')}
function phaseCards(items){return `<div class="phase1-cards">${items.map(([name,value])=>`<div class="metric"><div class="metric-label">${esc(name)}</div><div class="metric-value">${esc(fmt(value))}</div></div>`).join('')}</div>`}
function clearPhase2(){
 $('assessment-section').hidden=true;
 $('risk-box').className='risk-box pending-box';$('risk-level').textContent='Not available';$('risk-score').textContent='—';$('score-label').textContent='Assessment score:';$('results-source').textContent='Patient records';$('trend-title').textContent='Prediction trend';$('trend-chart').innerHTML='<div class="phase1-empty">No assessment history is available for this patient.</div>';
 $('reasons').innerHTML='<li>Assessment details are not available yet.</li>';$('alert-banner').className='alert-banner low';$('alert-text').textContent='Assessment not available';$('download-pdf').disabled=true;$('download-pdf').title='A report will be available when an assessment is ready.';$('clinical-note').textContent='Writing measurements describe communication patterns. A risk assessment is not available yet.';$('senior-result').replaceChildren();
}
function monthlySVG(monthly){
 if(!monthly.length)return '<p class="phase1-empty">Posting history is not available for this patient.</p>';
 const W=900,H=220,x0=45,pw=830,ph=160,max=Math.max(1,...monthly.map(r=>r.posts)),x=i=>monthly.length===1?x0+pw/2:x0+i*pw/(monthly.length-1),y=v=>18+ph-v/max*ph,points=monthly.map((r,i)=>`${x(i)},${y(r.posts)}`).join(' ');
 return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto;margin-top:15px" role="img" aria-label="Actual monthly post counts"><line x1="45" y1="178" x2="875" y2="178" stroke="#c4d8eb"/><text x="40" y="20" text-anchor="end" font-size="12" fill="#4b6e90">${max}</text><polyline points="${points}" fill="none" stroke="#1873de" stroke-width="3"/>${monthly.map((r,i)=>`<circle cx="${x(i)}" cy="${y(r.posts)}" r="4" fill="#1873de"><title>${esc(r.month)}: ${r.posts} posts</title></circle>${monthly.length<=8||i===0||i===monthly.length-1||i%Math.ceil(monthly.length/6)===0?`<text x="${x(i)}" y="205" text-anchor="middle" font-size="12" fill="#4b6e90">${esc(r.month)}</text>`:''}`).join('')}</svg><p class="phase1-note">Monthly post counts for the available history.</p>`;
}
function renderPhase1Patient(pid){
 const p=DATA.phase1?.patients?.find(p=>p.patient===pid);if(!p)return;
 const f=p.features,meta=p.metadata;
 const numeric=v=>typeof v==='number'&&Number.isFinite(v);
 const total=p.post_count??f.n_posts??f.own_posts;
 const months=p.monthly||[];
 let html=`<div class="patient-summary"><div><span class="eyebrow">Selected patient</span><h3>${esc(pid)}</h3></div><div><span class="eyebrow">Recorded group</span><strong>${esc(meta.group||'Not recorded')}</strong></div><div><span class="eyebrow">Recorded MoCA</span><strong>${esc(fmt(meta.moca))}</strong></div><div><span class="eyebrow">Posts in record</span><strong>${esc(fmt(total,0))}</strong></div></div><p class="helper">Group and MoCA are recorded history, not an assessment generated by NEORORA.</p>`;
 html+='<section class="review-section"><h2>What changed in their writing?</h2><p class="helper">Later writing compared with earlier writing. Increases and decreases describe writing patterns; they do not indicate a diagnosis.</p>';
 const keys=['mattr_change','avg_words_per_post_change','avg_sentence_length_change','repetition_rate_change'];
 if(p.change_supported===false)html+='<div class="phase1-empty">More original posts are needed for an earlier-to-later comparison.</div>';
 else if(keys.some(k=>numeric(f[k])))html+='<div class="change-grid">'+keys.filter(k=>numeric(f[k])).map(k=>{const v=f[k],direction=v>0?'Increased':v<0?'Decreased':'No change';return `<article class="change-card"><span>${esc(featureName(k.replace('_change','')))}</span><strong>${direction}${v===0?'':` by ${esc(fmt(Math.abs(v),4))}`}</strong><small>Difference between the two halves of the writing history</small></article>`}).join('')+'</div>';
 else html+='<div class="phase1-empty">An earlier-to-later writing comparison is not available in this record.</div>';
 html+='</section><section class="review-section"><h2>Posting activity</h2>';
 html+=months.length?monthlySVG(months):'<p class="helper">Dated posting history is not available. Writing changes above compare earlier and later groups of posts rather than calendar months.</p>';
 html+='</section><section class="assessment-status"><h3>Assessment status</h3><p>No model assessment is available for this patient. The writing measurements below are available for review.</p></section>';
 const descriptions={mattr:'Variety of vocabulary, measured over moving windows of text.',avg_words_per_post:'Average number of words in a post.',avg_sentence_length:'Average number of words in a sentence.',repetition_rate:'Frequency of repeated two-word combinations.',filler_ratio:'Proportion of words identified as fillers.',own_posts:'Number of posts identified as original writing.'};
 html+='<details class="measurement-details"><summary>View detailed writing measurements</summary><div class="phase1-table"><table class="post-preview"><thead><tr><th>Measurement</th><th>Value</th><th>Meaning</th></tr></thead><tbody>'+Object.entries(descriptions).map(([k,d])=>`<tr><td>${esc(featureName(k))}</td><td>${esc(fmt(f[k]))}</td><td>${esc(d)}</td></tr>`).join('')+'</tbody></table></div></details>';
 $('phase1-patient-details').innerHTML=html;
 if(!DATA.isPlaceholder&&personRows(pid).length)$('phase1-patient-details').querySelector('.assessment-status').hidden=true;
}
function renderReceipt(){
 const receipt=DATA.upload_summary,el=$('upload-receipt');el.hidden=!receipt;
 if(receipt)el.innerHTML=`<h2>Posts received</h2><p><strong>${esc(receipt.posts)} posts</strong> · ${esc(receipt.start)} to ${esc(receipt.end)}</p><p class="helper">${esc(receipt.name)}</p>${DATA.senior_result?'':`<p class="helper">${esc(receipt.status||'Your posts have been received. An assessment has not been generated.')}</p>`}`;
}
function renderSeniorResult(){
 const result=DATA.senior_result,el=$('senior-result');
 if(!result){el.replaceChildren();return;}
 const state=result.risk_level.toLowerCase();
 const message={low:'Your writing received a lower screening score. If you have concerns, discuss them with a clinician.',medium:'Some writing patterns may need review. Consider discussing the result with a clinician.',high:'Your writing received a higher screening score. Please arrange a review with a clinician.'}[state];
 el.innerHTML=`<article class="panel senior-assessment"><h2>Your screening summary</h2><div class="result-message ${state==='medium'?'moderate':state}"><span class="status-dot ${state==='high'?'red':state==='medium'?'yellow':''}"></span><p>${esc(message)}</p></div><p class="helper">${esc(result.risk_level)} score band · This result is not a diagnosis.</p></article>`;
}

function renderPhase1(){
 const phase=DATA.phase1||{patient_ids:[],patients:[],loaded:[],funnels:{},missing:[],target_note:''};
 const pid=$('patient-select').value;
 if(phase.patient_ids.includes(pid))renderPhase1Patient(pid);else $('phase1-patient-details').innerHTML='<div class="phase1-empty">Writing history is not available for this patient.</div>';
}
