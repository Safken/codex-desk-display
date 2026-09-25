const test=require('node:test');
const assert=require('node:assert/strict');
const vm=require('node:vm');
const fs=require('node:fs');
const script=fs.readFileSync('firmware/CodexDesk/setup_page.h','utf8').split('<script>')[1].split('</script>')[0];
function harness(fetch){
 const nodes=new Map();
 function element(){return {value:'',textContent:'',disabled:false,hidden:false,children:[],replaceChildren(...n){this.children=n},append(n){this.children.push(n)}}}
 const get=id=>{if(!nodes.has(id))nodes.set(id,element());return nodes.get(id)};
 const context=vm.createContext({document:{getElementById:get,createElement:element},Option:function(text,value){this.textContent=text;this.value=value},fetch,AbortSignal,URLSearchParams,FormData:function(){return []},setTimeout,Set,Promise});
 vm.runInContext(script,context);return {context,get};
}
test('scan names remain literal, duplicate SSIDs collapse, selection fills manual input',()=>{
 const {context,get}=harness(()=>new Promise(()=>{}));
 vm.runInContext(`showNetworks([{ssid:'<img src=x>',rssi:-45},{ssid:'<img src=x>',rssi:-70},{ssid:'Guest',rssi:-60,open:true}])`,context);
 assert.equal(get('networks').children.length,3);
 assert.equal(get('networks').children[1].textContent,'<img src=x> (-45 dBm)');
 assert.equal(get('networks').children[2].disabled,true);
 get('networks').value='<img src=x>';get('networks').onchange();
 assert.equal(get('ssid').value,'<img src=x>');
});
test('failed saves show the response and allow retry',async()=>{
 const {get}=harness(url=>url==='/save'?Promise.resolve({ok:false,text:async()=>'Settings could not be stored.'}):new Promise(()=>{}));
 await get('setup').onsubmit({preventDefault(){},target:{}});
 assert.equal(get('status').textContent,'Settings could not be stored.');
 assert.equal(get('save').disabled,false);
 assert.equal(get('setup').hidden,false);
});
