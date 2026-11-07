document.getElementById('network-form').addEventListener('submit', async event => {
  event.preventDefault();
  const result = document.getElementById('network-result');
  const button = event.target.querySelector('button');
  const password = document.getElementById('network-password');
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
    result.textContent = data.error ? `Saved; discovery could not start: ${data.error}` :
      'Saved. Reload this page to see current discovery status.';
  } catch(error) { result.textContent = error.message; }
  finally { button.disabled = false; }
});

if(document.getElementById('pi-network-form')) {
  const pi = id => document.getElementById('pi-' + id);
  let pending = null, polling = null;
  function settings() {
    const mode = pi('mode').value, value = {mode, dns:pi('dns').value.split(',').map(x=>x.trim()).filter(Boolean)};
    if(mode === 'static') Object.assign(value, {address:pi('address').value.trim(), prefix:Number(pi('prefix').value), gateway:pi('gateway').value.trim()});
    return value;
  }
  async function request(operation, data) {
    const bytes = new TextEncoder().encode('admin:' + pi('password').value);
    const response = await fetch('/api/pi/network' + (operation ? '/' + operation : ''), {
      method:data ? 'POST':'GET', headers:{Authorization:'Basic '+btoa(String.fromCharCode(...bytes)),
      'X-CIVI-Request':'1','Content-Type':'application/json'}, body:data ? JSON.stringify(data):undefined,
      signal:AbortSignal.timeout(50000)});
    const result = await response.json().catch(()=>({}));
    if(!response.ok) throw new Error(result.error || `HTTP ${response.status}`);
    return result;
  }
  function show(state) {
    pending = state.pending;
    pi('state').textContent = JSON.stringify(state,null,2);
    pi('confirm').disabled = pi('rollback').disabled = !pending;
    pi('apply').disabled = !!pending;
    if(polling) clearInterval(polling);
    polling = pending ? setInterval(()=>act('',undefined),3000):null;
    pi('result').textContent = pending ? `Waiting for confirmation: ${pending.remaining_seconds} seconds remaining.` :
      (state.last_result ? `LAN result: ${state.last_result.state}`:'Wired LAN settings read.');
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
    } catch(error) {
      pi('result').textContent = `${error.message}. If the address changed, reconnect through the new wired address. Without confirmation the change will be rolled back.`;
    }
  }
  pi('read').onclick = async () => {
    await act('',undefined);
  };
  pi('preview').onclick = () => { const value=settings(); reconnect(value); act('preview',{settings:value}); };
  pi('apply').onclick = () => { const value=settings(); reconnect(value); act('apply',{settings:value}); };
  pi('confirm').onclick = () => act('confirm',{token:pending?.token});
  pi('rollback').onclick = () => act('rollback',{token:pending?.token});
  pi('network-form').onsubmit = event => event.preventDefault();
}
