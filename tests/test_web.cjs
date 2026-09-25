const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

// Deterministic clock and minimal DOM exercise actual rendering during an outage.
test('offline values age, runway is suppressed, and recovery restores freshness', () => {
  const elements = new Map();
  const element = id => { if (!elements.has(id)) elements.set(id, {textContent:'',hidden:false,classList:{toggle(){},add(){}},addEventListener(){},setAttribute(){}}); return elements.get(id); };
  const context = vm.createContext({document:{getElementById:element},performance:{now:()=>0},Intl,Date,Math,String,setInterval(){},fetch:()=>new Promise(()=>{}),AbortSignal});
  vm.runInContext(fs.readFileSync('web/app.js','utf8'),context);
  vm.runInContext(`data={schema_version:1,server_time:1000,updated_at:1000,state:'fresh',stale_seconds:600,tokens_updated_at:1000,tokens_fresh:true,weekly:{remaining_percent:70,resets_at:99999},today:{points:8.4,tokens:1000},lifetime_tokens:9000000,runway:{seconds:3600},poll_seconds:300}; received=0;render();`,context);
  assert.equal(element('today-points').textContent,'8.4%');
  assert.equal(element('reset-label').textContent,'Resets in');
  assert.equal(element('period-dates').textContent,'--/-- to --/--');
  vm.runInContext("data.weekly.period_date_label='09/17 to 09/24';render();",context);
  assert.equal(element('period-dates').textContent,'09/17 to 09/24');
  vm.runInContext("data.weekly.reset_local_label='9/24 @ 6:14pm';render();",context);
  assert.equal(element('reset-label').textContent,'Resets in (9/24 @ 6:14pm)');
  assert.equal(element('lifetime').textContent,'9M');
  vm.runInContext('offline=true; data.server_time=1700;render();',context);
  assert.equal(element('freshness').textContent,'SERVER OFFLINE');
  assert.equal(element('lifetime').textContent,'—');
  assert.equal(element('today-tokens').textContent,'—');
  assert.equal(element('runway').textContent,'Unavailable');
  vm.runInContext('offline=false; data.updated_at=1700;data.tokens_updated_at=1700;render();',context);
  assert.equal(element('lifetime').textContent,'9M');
  assert.equal(element('runway').textContent,'1h 0m');
});

 test('credits appear only at exhausted allowance and do not remain live when stale', () => {
  const elements=new Map();
  const element=id=>{if(!elements.has(id))elements.set(id,{textContent:'',hidden:false,classList:{toggle(){},add(){}},addEventListener(){},setAttribute(){}});return elements.get(id)};
  const context=vm.createContext({document:{getElementById:element},performance:{now:()=>0},Intl,Date,Math,String,setInterval(){},fetch:()=>new Promise(()=>{}),AbortSignal});
  vm.runInContext(fs.readFileSync('web/app.js','utf8'),context);
  vm.runInContext("data={server_time:1000,updated_at:1000,state:'fresh',weekly:{remaining_percent:0,resets_at:99999},credits:{balance:123.75},poll_seconds:300};render()",context);
  assert.equal(element('credits').hidden,false);
  assert.equal(element('credits').textContent,'(Credits Left: 123)');
  vm.runInContext('data.weekly.remaining_percent=1;render()',context);
  assert.equal(element('credits').hidden,true);
  vm.runInContext('data.weekly.remaining_percent=0;data.credits=null;render()',context);
  assert.equal(element('credits').textContent,'(Credits Left: \u2014)');
  vm.runInContext('data.credits={unlimited:true};render()',context);
  assert.equal(element('credits').textContent,'(Credits Left: Unlimited)');
  vm.runInContext('offline=true;render()',context);
  assert.equal(element('credits').textContent,'(Credits Left: \u2014)');
 });
