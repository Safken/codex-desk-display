'use strict';
let data=null,received=0,offline=false,page=0;
const el=id=>document.getElementById(id);
const text=(id,value)=>{el(id).textContent=value};
const count=n=>n==null?'—':Intl.NumberFormat('en-US',{notation:'compact',maximumFractionDigits:2}).format(n);
const points=n=>n==null?'—':`${n.toFixed(1)} pts`;
function duration(n){if(n==null)return 'Collecting';n=Math.max(0,Math.floor(n));const d=Math.floor(n/86400),h=Math.floor(n%86400/3600),m=Math.floor(n%3600/60);return d?`${d}d ${h}h`:h?`${h}h ${m}m`:`${m}m`}
function date(ts){return ts==null?'—':new Date(ts*1000).toLocaleString('en-US',{timeZone:data?.timezone||'UTC',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',timeZoneName:'short'})}
function switchPage(n){page=n;el('page-main').hidden=!!n;el('page-detail').hidden=!n;el('nav-main').setAttribute('aria-pressed',String(!n));el('nav-detail').setAttribute('aria-pressed',String(!!n))}
el('nav-main').onclick=()=>switchPage(0);el('nav-detail').onclick=()=>switchPage(1);
let startX=0,swiped=false;
el('screen').addEventListener('pointerdown',e=>{startX=e.clientX;swiped=false});
el('screen').addEventListener('pointerup',e=>{if(Math.abs(e.clientX-startX)>30){switchPage(1-page);swiped=true}});
el('screen').onclick=e=>{if(!swiped&&!e.target.closest('#mini-days'))switchPage(1-page)};
el('screen').onkeydown=e=>{if(['ArrowRight','ArrowLeft','Enter',' '].includes(e.key)){e.preventDefault();switchPage(1-page)}};
function render(){
 if(!data)return;
 const elapsed=(performance.now()-received)/1000,now=data.server_time+elapsed;
 const freshness=data.stale_seconds||900;
 const tokensFresh=data.tokens_fresh&&data.tokens_updated_at!=null&&now-data.tokens_updated_at<=freshness;
 const old=data.state!=='fresh'||now-(data.updated_at||0)>freshness||now>=(data.weekly?.resets_at||Infinity);
 const label=offline?'Server offline':old?'Data stale':'Collecting normally';
 text('connection',data.demo?'Demo preview':label);el('connection').classList.toggle('warning',offline||old||data.demo);
 el('demo-banner').hidden=!data.demo;
 text('remaining',data.weekly?String(Math.round(data.weekly.remaining_percent)):'—');el('bar').value=data.weekly?.remaining_percent||0;
 const showCredits=data.weekly?.remaining_percent===0;
 el('credits').hidden=!showCredits;el('hero').classList.toggle('with-credits',showCredits);
 const creditValue=offline||old?'—':data.credits?.unlimited?'Unlimited':data.credits?.balance==null?'—':count(Math.floor(data.credits.balance));
 text('credits',`(Credits Left: ${creditValue})`);
 text('today-points',data.today?.points==null?'—':`${data.today.points.toFixed(1)}%`);text('today-tokens',tokensFresh?count(data.today?.tokens):'—');
 text('runway',offline||old?'Unavailable':duration(data.runway?.seconds));
 text('reset',data.weekly?duration(data.weekly.resets_at-now):'—');
 text('reset-label',data.weekly?.reset_local_label?`Resets in (${data.weekly.reset_local_label})`:'Resets in');
 text('freshness',offline?'SERVER OFFLINE':old?'DATA STALE':`Updated ${duration(now-data.updated_at)} ago`);
 el('dot').classList.toggle('warning',offline||old);text('detail-state',offline?'OFFLINE':old?'STALE':'LIVE');
 text('period-tokens',count(data.period?.tokens));text('average',data.period?.average_points_per_day==null?'—':`${data.period.average_points_per_day.toFixed(1)} pts/d`);
 text('period-dates',data.weekly?.period_date_label||'--/-- to --/--');
 text('lifetime',tokensFresh?count(data.lifetime_tokens):'—');
 text('status-title',offline?'The server is unreachable':data.state==='unavailable'?'Waiting for the first account reading':old?'The last reading needs a refresh':'Your collector is up to date');
 const failed=data.last_attempt&&data.last_attempt.status!=='ok';
 text('status-copy',offline?'The last known reading stays visible. Retrying automatically.':failed?`Latest collection failed (${data.last_attempt.status}). The last success is retained.`:data.runway?.reason==='collecting_history'?'Building history for your daily statistics and runway estimate.':data.runway?.beyond_reset?'At the measured pace, the allowance is projected to last beyond the next reset.':'Readings refresh automatically. No browser or PC needs to stay open.');
 text('reset-absolute',date(data.weekly?.resets_at));text('updated-absolute',date(data.updated_at));
 text('coverage',`${((data.period?.observed_seconds||0)/3600).toFixed(1)} hours · partial`);
 text('interval',`${Math.round(data.poll_seconds/60)} minutes`);text('timezone',data.timezone);
}
function rows(){
 const days=data.days||[];el('days').replaceChildren();el('mini-days').replaceChildren();
 for(const d of days){const tr=document.createElement('tr');for(const value of [d.date,points(d.points),count(d.tokens),(d.observed_seconds/3600).toFixed(1),'Observed / partial']){const td=document.createElement('td');td.textContent=value;tr.append(td)}el('days').append(tr)}
 if(!days.length){const tr=document.createElement('tr'),td=document.createElement('td');td.colSpan=5;td.textContent='History will appear after collection starts.';tr.append(td);el('days').append(tr)}
 for(const d of days){const row=document.createElement('div');row.className='mini-row';for(const value of [d.date.slice(5),d.points==null?'—':d.points.toFixed(1),count(d.tokens)]){const span=document.createElement('span');span.textContent=value;row.append(span)}el('mini-days').append(row)}
 text('reported-days',(data.reported_daily_tokens||[]).map(d=>`${d.date}  ·  ${count(d.tokens)} tokens`).join('\n')||'Unavailable');
}
async function refresh(){try{const response=await fetch('/api/status',{cache:'no-store',signal:AbortSignal.timeout(8000)});if(!response.ok)throw Error();const next=await response.json();if(next.schema_version!==1)throw Error();data=next;received=performance.now();offline=false;rows();render()}catch{offline=true;text('connection','Server offline');el('connection').classList.add('warning');if(data)render();else{text('status-title','The server is unreachable');text('status-copy','Retrying automatically.')}}}
refresh();setInterval(refresh,15000);setInterval(render,1000);
