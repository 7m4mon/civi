document.getElementById('password-form')?.addEventListener('submit', async event => {
  event.preventDefault();
  const form=event.target, button=form.querySelector('button');
  const result=document.getElementById('password-result');
  const value=id=>document.getElementById('password-'+id).value;
  if(!form.reportValidity()) return;
  if(value('new')!==value('confirm')) { result.textContent='New passwords do not match.'; return; }
  button.disabled=true; result.textContent='Saving the new Web password…';
  try {
    const bytes=new TextEncoder().encode('admin:'+value('current'));
    const response=await fetch('/api/password',{method:'POST',headers:{
      Authorization:'Basic '+btoa(String.fromCharCode(...bytes)),
      'Content-Type':'application/json','X-CIVI-Request':'1'},
      body:JSON.stringify({new_password:value('new'),confirm_password:value('confirm')})});
    const data=await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    form.reset();
    for(const id of ['network-password','pi-password']) {
      const field=document.getElementById(id); if(field) field.value='';
    }
    result.textContent='Password changed and saved. Use the new password on all CIVI Web pages. No restart is needed.';
  } catch(error) { result.textContent=error.message; }
  finally { button.disabled=false; }
});

document.getElementById('network-form').addEventListener('submit', async event => {
  event.preventDefault();
  const result = document.getElementById('network-result');
  const button = event.target.querySelector('button');
  const password = document.getElementById('network-password');
  if(!password.reportValidity()) return;
  button.disabled = true;
  result.textContent = 'Saving and applying discovery settings…';
  try {
    const bytes = new TextEncoder().encode('admin:' + password.value);
    const response = await fetch('/api/network', {method:'POST', headers:{
      Authorization:'Basic ' + btoa(String.fromCharCode(...bytes)),
      'Content-Type':'application/json', 'X-CIVI-Request':'1'},
      body:JSON.stringify({description:document.getElementById('description').value,
                          discovery:document.getElementById('discovery').checked})});
    const data = await response.json().catch(() => ({}));
    if(!response.ok) throw new Error(data.error || `HTTP ${response.status}`);
    password.value = '';
    if(typeof data.description === 'string') document.getElementById('description').value=data.description;
    result.textContent = data.error ? `Saved; discovery could not be applied: ${data.error}` :
      'Saved. Reload this page to see current discovery status.';
    if(!data.error && !document.getElementById('discovery').checked) {
      const url=new URL(location.href);
      const ip=location.hostname.match(/^\d+\.\d+\.\d+\.\d+$/) ? location.hostname :
        [...document.querySelectorAll('code')].map(x=>x.textContent.match(/^TCPIP::(\d+\.\d+\.\d+\.\d+)::/)).find(x=>x && !x[1].startsWith('127.'))?.[1];
      result.textContent='Saved. mDNS / DNS-SD disabled. Use a numeric IP address to reopen this page and enable it again. Cached names may still resolve temporarily. ';
      if(ip) { url.hostname=ip; const link=document.createElement('a'); link.href=url.href; link.textContent=url.href; result.append(link); }
    }
  } catch(error) { result.textContent = error.message; }
  finally { button.disabled = false; }
});

if(document.getElementById('pi-network-form')) {
  const pi = id => document.getElementById('pi-' + id);
  function subnet() {
    const value=pi('prefix').value, prefix=Number(value);
    const valid=value!=='' && Number.isInteger(prefix) && prefix>=1 && prefix<=32;
    const mask=valid ? [0,8,16,24].map(offset=>
      256-Math.pow(2,8-Math.min(8,Math.max(0,prefix-offset)))).join('.') : null;
    pi('subnet').textContent=valid ? `Subnet mask: ${mask} (/${prefix}). Prefix length is the number of network bits.` :
      'Enter a prefix length from 1 to 32 to display the subnet mask.';
  }
  pi('prefix').addEventListener('input',subnet);
  subnet();
  let pending = null, polling = null;
  let deadline = null, target = null, applying = false;
  function guide() {
    if(!deadline) return;
    const seconds = Math.max(0,Math.ceil((deadline-Date.now())/1000));
    const box = pi('guidance'); box.hidden=false; box.replaceChildren();
    const title=document.createElement('h2');
    title.textContent=seconds ? `Confirm your LAN change within ${seconds} seconds` : 'Confirmation time expired';
    box.append(title);
    if(!seconds) {
      pi('confirm').disabled=pi('rollback').disabled=true;
      box.append('The confirmation time has expired. NetworkManager restores the previous settings unless you already confirmed. Open the previous address and read wired LAN to check.');
      return;
    }
    if(target) {
      const url=new URL(location.href); url.hostname=target; url.hash='pi-lan';
      const link=document.createElement('a'); link.href=url.href; link.textContent=url.href;
      box.append('Open ',link,'. ');
    } else box.append('Open this page through the new wired IPv4 address. ');
    box.append('Enter the CIVI Web password, click “Read wired LAN”, then click “Confirm and save” below. Without confirmation, the previous LAN settings will be restored automatically.');
  }
  setInterval(guide,1000);
  function settings() {
    const mode = pi('mode').value, value = {mode, dns:pi('dns').value.split(',').map(x=>x.trim()).filter(Boolean)};
    if(mode === 'static') Object.assign(value, {address:pi('address').value.trim(), prefix:Number(pi('prefix').value), gateway:pi('gateway').value.trim()});
    return value;
  }
  async function request(operation, data) {
    if(!pi('password').reportValidity() || pi('password').value.length < 12) {
      const error = new Error('Enter the CIVI Web password (at least 12 characters), not the Linux/sudo password.');
      error.status=401; throw error;
    }
    const bytes = new TextEncoder().encode('admin:' + pi('password').value);
    const response = await fetch('/api/pi/network' + (operation ? '/' + operation : ''), {
      method:data ? 'POST':'GET', headers:{Authorization:'Basic '+btoa(String.fromCharCode(...bytes)),
      'X-CIVI-Request':'1','Content-Type':'application/json'}, body:data ? JSON.stringify(data):undefined,
      signal:AbortSignal.timeout(50000)});
    const result = await response.json().catch(()=>({}));
    if(!response.ok) {
      const error = new Error(result.error || `HTTP ${response.status}`);
      error.status=response.status; throw error;
    }
    return result;
  }
  function show(state) {
    pending = state.pending;
    pi('state').textContent = JSON.stringify(state,null,2);
    pi('confirm').disabled = pi('rollback').disabled = !pending;
    pi('apply').disabled = !!pending;
    pi('save-hostname').disabled = !!pending;
    if(pending) {
      deadline=Date.now()+pending.remaining_seconds*1000;
      target=pending.expected_ipv4 || state.snapshot.active_ipv4.split('\n')[0].split('/')[0];
      guide();
    } else {
      deadline=null;
      pi('guidance').hidden=true;
    }
    if(polling) clearInterval(polling);
    polling = pending ? setInterval(()=>act('',undefined),3000):null;
    const result=state.last_result;
    const message=result?.state==='recovery_required' ?
      'LAN restoration could not be verified. Inspect the current settings on the Pi before making another change.' :
      result?.state==='confirmed' ? 'LAN settings confirmed and saved.' :
      result?.state==='rolled_back' && result.verified ? 'Previous LAN settings restored and verified.' :
      result ? `LAN result: ${result.state}; read the technical details below.` : 'Wired LAN settings read.';
    pi('result').textContent = pending ? `Waiting for confirmation: ${pending.remaining_seconds} seconds remaining.` : message;
  }
  function reconnect(value) {
    pi('reconnect').textContent = '';
    if(value.mode !== 'static') return;
    const url = new URL(location.href); url.hostname = value.address;
    const link = document.createElement('a'); link.href = url.href; link.textContent = url.href;
    pi('reconnect').append('After applying, open ',link,', enter the password, read wired LAN, then confirm.');
  }
  async function act(operation, data) {
    try {
      const result = await request(operation,data);
      if(operation==='preview') pi('state').textContent = JSON.stringify(result,null,2);
      else show(result);
      return result;
    } catch(error) {
      if(!operation) pi('confirm').disabled=pi('rollback').disabled=true;
      if(operation==='apply' && error.status) {
        deadline=null; pi('guidance').hidden=true;
      }
      if(error.status===401) {
        if(polling) clearInterval(polling);
        pi('result').textContent=error.message;
      } else pi('result').textContent = `${error.message}. If the address changed, reconnect through the new wired address. Without confirmation the change will be rolled back.`;
    }
  }
  pi('read').onclick = async () => {
    const state = await act('',undefined);
    if(!state) return;
    const snapshot=state.snapshot, profile=snapshot.profile;
    pi('hostname').value=snapshot.hostname || '';
    pi('mode').value=profile['ipv4.method']==='auto' ? 'automatic':'static';
    const address=snapshot.active_ipv4.split('\n')[0].split('/');
    pi('address').value=address[0] || '';
    pi('prefix').value=address[1] || 24;
    subnet();
    pi('gateway').value=profile['ipv4.gateway'] || '';
    pi('dns').value=profile['ipv4.dns'] || '';
  };
  pi('preview').onclick = () => { const value=settings(); reconnect(value); act('preview',{settings:value}); };
  async function pingSetting(save) {
    pi('read-ping').disabled=pi('save-ping').disabled=true;
    pi('ping-result').textContent=save ? 'Saving IPv4 Ping setting…':'Reading IPv4 Ping setting…';
    try {
      const state=await request('ping',save ? {enabled:pi('ping-enabled').checked}:undefined);
      pi('ping-enabled').checked=state.enabled;
      pi('ping-enabled').disabled=false;
      pi('ping-result').textContent=`IPv4 Ping replies ${state.enabled ? 'enabled':'disabled'}. ` +
        (save ? 'Saved for future boots. ':`CIVI saved setting: ${state.saved_enabled===null ? 'not set':state.saved_enabled ? 'enabled':'disabled'}. `) +
        'Applies to all Pi interfaces. HTTPS and SCPI remain available.';
    } catch(error) { pi('ping-result').textContent=error.message; pi('ping-enabled').disabled=true; }
    finally { pi('read-ping').disabled=false; pi('save-ping').disabled=pi('ping-enabled').disabled; }
  }
  pi('read-ping').onclick=()=>pingSetting(false);
  pi('save-ping').onclick=()=>pingSetting(true);
  pi('save-hostname').onclick = async () => {
    const name=pi('hostname').value.trim();
    if(name && !pi('hostname').reportValidity()) {
      pi('hostname-result').textContent='Enter a hostname using 1–63 letters, digits or hyphens.'; return;
    }
    pi('save-hostname').disabled=true;
    pi('hostname-result').textContent='Saving the system hostname…';
    try {
      const result=await request('hostname',{hostname:name});
      show(result); pi('hostname').value=result.snapshot.hostname;
      pi('hostname-result').textContent=`Hostname saved: ${result.snapshot.hostname}. IP addresses are unchanged. ` +
        (result.discovery_error ? `Discovery could not update: ${result.discovery_error}` :
          'Reload this page to see the updated hostname. The HTTPS certificate may need to be updated for this name.');
    } catch(error) { pi('hostname-result').textContent=error.message; }
    finally { pi('save-hostname').disabled=!!pending; }
  };
  pi('apply').onclick = async () => {
    if(applying || !pi('password').reportValidity() || pi('password').value.length<12) return;
    applying=true;
    const value=settings(); reconnect(value);
    deadline=Date.now()+90000; target=value.mode==='static' ? value.address:null;
    guide(); pi('guidance').scrollIntoView({block:'center',behavior:'smooth'});
    pi('result').textContent='Applying temporary LAN settings… The connection may close while the address changes.';
    pi('apply').disabled=true;
    try { await act('apply',{settings:value}); }
    finally { applying=false; pi('apply').disabled=!!pending; }
  };
  pi('confirm').onclick = () => act('confirm',{token:pending?.token});
  pi('rollback').onclick = () => act('rollback',{token:pending?.token});
  pi('network-form').onsubmit = event => event.preventDefault();
  if(location.hash==='#pi-lan') {
    pi('result').textContent='To confirm the pending change: enter the CIVI Web password, click “Read wired LAN”, then “Confirm and save”.';
    pi('password').focus();
  }
  pi('password').addEventListener('change',()=> {
    if(pi('password').value.length>=12) pi('read').click();
  });
}
