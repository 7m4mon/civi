let auth = '', session = '', busy = false, settingsLoaded = false;
const $ = id => document.getElementById(id);
async function jsonRequest(path, options = {}) {
  const r = await fetch(path, {...options, signal: AbortSignal.timeout(5000)});
  const value = await r.json().catch(() => ({}));
  if (!r.ok) {
    const error = new Error(value.error || `HTTP ${r.status}`);
    error.status = r.status;
    throw error;
  }
  return value;
}
async function api(path, data) {
  const headers = {Authorization: auth, 'X-CIVI-Request': '1', 'X-CIVI-Session': session};
  if (data !== undefined) headers['Content-Type'] = 'application/json';
  return jsonRequest('/api/' + path, {method: data === undefined ? 'GET' : 'POST', headers, body: data === undefined ? undefined : JSON.stringify(data)});
}
function notice(e) { $('notice').textContent = e instanceof Error ? e.message : e; }
function readiness(state) {
  const messages = {
    connected: ['Radio ready', 'The radio is connected. Sign in to operate it.'],
    disconnected: ['Waiting for radio', 'CIVI is running. Turn on your radio and connect its USB cable. If the serial port is unavailable, CIVI retries automatically. Sign in to check the CI-V settings.'],
    quarantined: ['Radio not ready — recovery required', 'CIVI is running, but the radio did not respond or the CI-V connection failed. Turn on the radio, check the USB cable and CI-V settings, then reset the radio and USB link. Sign in and use Recover connection under CI-V connection settings.'],
    offline: ['CIVI server unavailable', 'The browser cannot reach CIVI. Check that the CIVI program is still running, then retry. This is separate from the radio connection.']
  };
  const [title, message] = messages[state] || messages.disconnected;
  $('radio-status').dataset.state = state;
  $('radio-status-title').textContent = title;
  $('radio-status-message').textContent = message;
  $('radio-status').querySelector('.eyebrow').textContent = state === 'offline' ? 'GATEWAY UNREACHABLE' : 'GATEWAY ONLINE';
  $('connection').textContent = state === 'connected' ? 'Radio ready' : state === 'offline' ? 'Gateway offline' : 'Radio not ready';
  for(const button of document.querySelectorAll('#frequency-form button, #mode-form button')) button.disabled = state !== 'connected';
  if(state !== 'connected') {
    $('ptt-on').disabled = true;
    $('frequency').textContent = '— MHz';
    $('mode-value').textContent = '—';
    $('ptt-value').textContent = 'PTT unknown';
    $('smeter').value = 0;
    $('smeter-value').textContent = '—';
  }
}
async function refreshHealth() {
  try { const health = await jsonRequest('/health'); readiness(health.radio); return true; }
  catch(e) { readiness('offline'); return false; }
}
async function command(text) {
  try { const r = await api('scpi', {command: text}); $('scpi-output').textContent = `${text}\n${r.response ?? '(Set command: no normal response)'}\n${r.error}`; notice(r.error.startsWith('0,') ? '' : r.error); await refresh(); }
  catch(e) { notice(e); }
}
async function refresh() {
  const s = await api('status');
  readiness(s.connection);
  $('radio-model').textContent = s.radio_model === 'Unknown' ? 'Radio not identified' : s.radio_model;
  $('backend').textContent = s.backend === 'mock' ? 'Simulated radio' : 'USB / CI-V';
  $('frequency').textContent = s.values.frequency == null ? '— MHz' : (s.values.frequency / 1e6).toFixed(6) + ' MHz';
  $('mode-value').textContent = s.values.mode ?? '—';
  $('ptt-value').textContent = s.values.ptt == null ? 'PTT unknown' : s.values.ptt ? 'TRANSMITTING' : 'RECEIVING';
  $('smeter').value = s.values.smeter ?? 0;
  $('smeter-value').textContent = s.values.smeter ?? '—';
  $('ptt-on').disabled = !s.tx_enabled || s.connection !== 'connected';
  $('identity').textContent = `${s.manufacturer}\n${s.model} / ${s.serial}\nCIVI software: ${s.version}\nRadio: ${s.radio_model}\nRadio firmware: ${s.radio_firmware}${s.radio_firmware_source === 'manual' ? ' (manually configured)' : ''}\nRadio profile: ${s.radio}\nConnection: ${s.connection}`;
  $('network').textContent = s.network.hostname + '\n\n' + s.network.interfaces.map(i => `${i.name}\nIP: ${i.ipv4.join(', ')}\nMAC: ${i.mac ?? 'Unknown'}\n${i.visa.join('\n')}`).join('\n\n');
  if (!settingsLoaded) {
    for (const mode of s.modes) { const o = document.createElement('option'); o.value = o.textContent = mode; $('mode-input').append(o); }
    if(s.values.mode != null) $('mode-input').value = s.values.mode;
    if(s.values.frequency != null) $('frequency-input').value = (s.values.frequency / 1e6).toFixed(6);
    const x = s.serial_settings;
    $('serial-port').value = x.port; $('serial-baud').value = x.baud; $('radio-address').value = x.radio_address; $('controller-address').value = x.controller_address; $('serial-timeout').value = x.timeout;
    settingsLoaded = true;
  }
  $('logs').textContent = s.logs.map(l => `${new Date(l.time * 1000).toLocaleTimeString()} ${l.code || 'INFO'} ${l.message}`).reverse().join('\n');
}
$('login-form').onsubmit = async e => {
  e.preventDefault();
  auth = 'Basic ' + btoa(String.fromCharCode(...new TextEncoder().encode('admin:' + $('password').value)));
  try {
    session = (await api('session', {})).session; $('password').value = '';
    await refresh(); $('login').hidden = true; $('dashboard').hidden = false;
    notice('');
  } catch(e) { notice(e); }
};
async function tick() {
  if(busy) return;
  busy = true;
  try {
    if(!await refreshHealth() || !session) return;
    await api('heartbeat', {});
    await refresh();
  } catch(e) {
    notice(e);
    $('ptt-on').disabled = true;
    if(e.status === 401) {
      session = '';
      $('login').hidden = false;
      $('dashboard').hidden = true;
      notice('Your session expired. Sign in again.');
    }
  } finally { busy = false; }
}
$('frequency-form').onsubmit = e => { e.preventDefault(); command('SENS:FREQ ' + $('frequency-input').value + ' MHz'); };
$('mode-form').onsubmit = e => { e.preventDefault(); command('RAD:MODE ' + $('mode-input').value); };
$('scpi-form').onsubmit = e => { e.preventDefault(); command($('scpi-input').value); };
$('ptt-on').onclick = () => command('RAD:PTT ON');
$('ptt-off').onclick = () => command('RAD:PTT OFF');
$('serial-form').onsubmit = async e => {
  e.preventDefault();
  try { await api('serial', {port: $('serial-port').value, baud: Number($('serial-baud').value), radio_address: Number($('radio-address').value), controller_address: Number($('controller-address').value), timeout: Number($('serial-timeout').value)}); notice('Connection settings applied for this run. Edit config.toml to save them permanently.'); } catch(e) { notice(e); }
};
$('recover').onclick = async () => { try { await api('recover', {link_reset_confirmed: $('recovery-confirm').checked}); notice('Connection recovered.'); await refresh(); } catch(e) { notice(e); } };
window.addEventListener('pagehide', () => { if(session) fetch('/api/release', {method:'POST', headers:{Authorization:auth,'X-CIVI-Request':'1','X-CIVI-Session':session},keepalive:true}); });
tick();
setInterval(tick, 2000);
