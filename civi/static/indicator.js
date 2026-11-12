(() => {
  const byId=id=>document.getElementById(id);
  if(!byId('lan-indicator')) return;
  function show(state) {
    const mode=['normal','fault','unknown'].includes(state.state)?state.state:'unknown';
    const identifying=mode==='normal' && state.identify && state.display_connected;
    byId('lan-lamp').className='lan-lamp '+(identifying?'identifying':mode);
    byId('lan-summary').textContent=`${state.interface}: LAN ${mode.toUpperCase()}`;
    byId('lan-details').textContent=`${state.hostname || 'Unknown'} · IPv4: ${state.addresses.join(', ') || '(none)'}`+
      (state.faults.length?' · '+state.faults.join('; '):'');
    byId('identify-state').textContent=!state.display_connected ?
      'Local panel is offline or hidden. Open bash panel.sh on the Pi and keep it visible.' :
      identifying ? (state.display_acknowledged?'Identify is on; local display acknowledged.':'Identify is on; waiting for local display acknowledgement.') :
      'Local panel is connected. Identify is off.';
  }
  async function poll() {
    try {
      const response=await fetch('/lan-status',{signal:AbortSignal.timeout(3000)});
      if(!response.ok) throw new Error(`HTTP ${response.status}`);
      show(await response.json());
    } catch(error) {
      byId('lan-summary').textContent='LAN status unavailable';
      byId('lan-lamp').className='lan-lamp unknown';
      byId('lan-details').textContent=error.message;
      byId('identify-state').textContent='Local panel and Identify status are unknown until LAN status is available again.';
    } finally {setTimeout(poll,1500);}
  }
  byId('identify-form').addEventListener('submit',async event=>{
    event.preventDefault();
    const form=event.target, result=byId('identify-result');
    if(!form.reportValidity())return;
    const enabled=event.submitter?.value==='on';
    const buttons=form.querySelectorAll('button');buttons.forEach(b=>b.disabled=true);
    result.textContent=enabled?'Requesting Identify…':'Stopping Identify…';
    try {
      const bytes=new TextEncoder().encode('admin:'+byId('identify-password').value);
      const response=await fetch('/api/identify',{method:'POST',headers:{
        Authorization:'Basic '+btoa(String.fromCharCode(...bytes)),
        'Content-Type':'application/json','X-CIVI-Request':'1'},body:JSON.stringify({enabled})});
      const data=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(data.error || `HTTP ${response.status}`);
      show(data); result.textContent=enabled?'Identify requested. Keep the local panel visible; press Stop Identify to finish.':'Identify stopped.';
    } catch(error){result.textContent=error.message;}
    finally{buttons.forEach(b=>b.disabled=false);}
  });
  poll();
})();
