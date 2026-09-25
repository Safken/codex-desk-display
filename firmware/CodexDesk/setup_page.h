#pragma once
const char SETUP_PAGE[] PROGMEM = R"PAGE(<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Connect your display</title>
<style>body{font:17px system-ui;max-width:460px;margin:24px auto;padding:20px;background:#101819;color:#eef4ed}input,select,button{box-sizing:border-box;width:100%;padding:12px;margin:6px 0 12px;font:inherit;border-radius:8px;border:1px solid #61716b}button{background:#c5ee83;color:#172019;cursor:pointer}small{color:#bdc9c3}#status{white-space:pre-wrap}label{display:block;margin-top:12px}</style>
<h1>Connect your display</h1><p>Choose your home Wi-Fi, then save to connect.</p>
<button id="scan" type="button">Find Wi-Fi networks</button><p id="scan-status" role="status"></p>
<label>Available 2.4 GHz networks<select id="networks"><option value="">Choose a network or enter its name below</option></select></label>
<form id="setup" method="post" action="/save"><label>Wi-Fi name<input id="ssid" name="ssid" maxlength="32" required autocomplete="off"></label><small>You can type a hidden network's name.</small>
<label>Wi-Fi password<input name="password" type="password" minlength="8" maxlength="63" required autocomplete="new-password"></label>
<label>Dashboard address<input id="server" name="server" placeholder="http://192.168.1.100:8790" required inputmode="url" autocapitalize="none" spellcheck="false"></label><small>Use your Ubuntu collector address. The example is not an automatic server address.</small>
<button id="save" type="submit">Save and connect</button></form><p id="status" role="status"></p><p><small>Settings stay on this display. No OpenAI credentials are needed.</small></p>
<script>
const byId=id=>document.getElementById(id);
byId('networks').onchange=()=>{if(byId('networks').value)byId('ssid').value=byId('networks').value};
function showNetworks(items){const list=byId('networks');list.replaceChildren(new Option('Choose a network or type below',''));const seen=new Set();for(const n of items){if(!n.ssid||seen.has(n.ssid))continue;seen.add(n.ssid);const option=document.createElement('option');option.value=n.ssid;option.textContent=n.ssid+' ('+n.rssi+' dBm)'+(n.open?' - open, unsupported':'');option.disabled=!!n.open;list.append(option)}byId('scan-status').textContent=seen.size?seen.size+' networks found.':'No visible networks found. Enter the name manually or scan again.'}
async function scan(){byId('scan').disabled=true;byId('scan-status').textContent='Scanning...';try{for(let tries=0;tries<20;tries++){const response=await fetch('/networks',{cache:'no-store',signal:AbortSignal.timeout(5000)});if(!response.ok)throw Error();const result=await response.json();if(!result.scanning){showNetworks(result.networks||[]);return}await new Promise(resolve=>setTimeout(resolve,750))}throw Error()}catch{byId('scan-status').textContent='Scan unavailable. You can enter your Wi-Fi name manually.'}finally{byId('scan').disabled=false}}
byId('scan').onclick=scan;
byId('setup').onsubmit=async event=>{event.preventDefault();byId('save').disabled=true;byId('status').textContent='Saving...';try{const response=await fetch('/save',{method:'POST',body:new URLSearchParams(new FormData(event.target)),signal:AbortSignal.timeout(10000)});const message=await response.text();byId('status').textContent=message;if(!response.ok)byId('save').disabled=false;else byId('setup').hidden=true}catch{byId('status').textContent='Connection lost before confirmation. Check whether the display restarted; otherwise reconnect and try again.';byId('save').disabled=false}};
fetch('/settings',{cache:'no-store'}).then(r=>r.json()).then(s=>{byId('server').value=s.server||'';byId('ssid').value=s.ssid||''}).catch(()=>{});
scan();
</script></html>)PAGE";
