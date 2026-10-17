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
function formatSmeter(raw, profile) {
  if(!Number.isInteger(raw) || raw < 0 || raw > 255) return '—';
  const suffix = ` (raw ${raw})`, curve = profile?.display_curve;
  if(!curve?.length) return `raw ${raw}`;
  const last = curve[curve.length - 1];
  if(raw > last[0]) return `≈ S9 +${last[1]} dB or more${suffix}`;
  let db = curve[0][1];
  for(let i = 1; i < curve.length; i++) {
    const [x0,y0] = curve[i-1], [x1,y1] = curve[i];
    if(raw <= x1) { db = y0 + (raw-x0)*(y1-y0)/(x1-x0); break; }
  }
  return (db <= 0 ? `≈ S${Math.max(0, Math.round(9+db/6))}` : `≈ S9 +${Math.round(db)} dB`) + suffix;
}
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
  $('smeter-value').textContent = formatSmeter(s.values.smeter, s.smeter);
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
  $('scope-settings').textContent = s.backend === 'mock' ? 'Simulated scope — no radio required.' : `CIVI USB baud rate: ${s.serial_settings.baud}${s.serial_settings.baud !== 115200 ? ' — change both the radio and CIVI to 115200 for scope data.' : ''}`;
  $('scope-start').disabled = scopeChanging || s.connection !== 'connected';
  $('scope-stop').disabled = scopeChanging || s.connection !== 'connected';
  $('logs').textContent = s.logs.map(l => `${new Date(l.time * 1000).toLocaleTimeString()} ${l.code || 'INFO'} ${l.message}`).reverse().join('\n');
}
$('login-form').onsubmit = async e => {
  e.preventDefault();
  auth = 'Basic ' + btoa(String.fromCharCode(...new TextEncoder().encode('admin:' + $('password').value)));
  try {
    session = (await api('session', {})).session; $('password').value = '';
    await refresh(); await loadCommands(); $('login').hidden = true; $('dashboard').hidden = false;
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
    await refreshScope();
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

let catalog = [], lastWaterfallTimestamp = null, scopeError = '', scopeChanging = false;
async function loadCommands() {
  if(catalog.length) return;
  const result = await api('commands');
  catalog = result.commands;
  for(const spec of catalog) {
    const option = document.createElement('option');
    option.value = spec.header;
    option.textContent = spec.header + ' — ' + spec.description;
    $('command-select').append(option);
  }
  selectCommand();
}
function selectedCommand() { return catalog.find(s => s.header === $('command-select').value); }
function selectCommand() {
  const spec = selectedCommand(); if(!spec) return;
  $('command-description').textContent = `CI-V ${spec.civ} · ${spec.format} · ${spec.guard ? 'Write permission: ' + spec.guard : 'Normal control'} · Hardware coverage: see validation report`;
  $('command-args').value = spec.access.includes('w') ? spec.set_example : spec.query_example;
  $('command-read').disabled = !spec.access.includes('r');
  $('command-write').disabled = !spec.access.includes('w');
}
$('command-select').onchange = selectCommand;
$('command-read').onclick = () => {
  const spec = selectedCommand(); if(!spec) return;
  command(spec.header + '?' + (spec.query_example ? ' ' + $('command-args').value.split(',')[0] : ''));
};
$('command-write').onclick = () => {
  const spec = selectedCommand(); if(!spec) return;
  command(spec.header + ($('command-args').value ? ' ' + $('command-args').value : ''));
};
async function refreshScope() {
  try {
    const result = await api('scope');
    const canvas = $('scope-plot'), context = canvas.getContext('2d');
    context.clearRect(0,0,canvas.width,canvas.height);
    const wave = result.sweep;
    if(!wave) { $('scope-status').textContent = scopeError || (result.enabled ? 'Waveform transfer enabled; waiting for a complete sweep. Check that the radio scope is on, USB baud is 115200, and the USB port is unlinked from [REMOTE].' : 'Scope stopped. Select Start scope to receive waveforms.'); return; }
    const frequencyInfo = wave.mode === 0 || wave.mode === 2 ? `Center ${wave.frequency_1_hz/1e6} MHz · Span ${wave.frequency_2_hz/1000} kHz` : `${wave.frequency_1_hz/1e6}–${wave.frequency_2_hz/1e6} MHz`;
    $('scope-status').textContent = wave.out_of_range ? 'Scope out of range.' : `${frequencyInfo} · ${wave.points.length} samples · ${new Date(wave.timestamp*1000).toLocaleTimeString()} · Raw levels 0–160`;
    if(!wave.points.length) return;
    context.strokeStyle = '#a8e5c2'; context.lineWidth = 2; context.beginPath();
    wave.points.forEach((p,i) => { const x=i*canvas.width/(wave.points.length-1), y=canvas.height-p*canvas.height/160; i ? context.lineTo(x,y) : context.moveTo(x,y); });
    context.stroke();
    if(wave.timestamp !== lastWaterfallTimestamp) {
      const waterfall = $('scope-waterfall'), wc = waterfall.getContext('2d');
      wc.drawImage(waterfall,0,0,475,159,0,1,475,159);
      wave.points.forEach((p,i) => { const f=p/160; wc.fillStyle=`rgb(${Math.round(f*168)},${Math.round(f*229)},${Math.round(f*194)})`; wc.fillRect(i,0,1,1); });
      lastWaterfallTimestamp = wave.timestamp;
    }
  } catch(e) { notice(e); }
}
$('scope-refresh').onclick = refreshScope;

async function setScope(enabled) {
  if(scopeChanging) return;
  scopeChanging = true;
  scopeError = '';
  $('scope-start').disabled = $('scope-stop').disabled = true;
  $('scope-status').textContent = enabled ? 'Starting scope…' : 'Stopping scope…';
  try {
    // Separate calls allow a failed prerequisite to stop the sequence.
    // Fully qualified SCPI headers share the normal authenticated control queue.
    const commands = enabled ? ['RAD:SCOPE:STREAM 0,ON', 'RAD:SCOPE:ENABLE 0,ON'] : ['RAD:SCOPE:STREAM 0,OFF'];
    for(const text of commands) {
      const r = await api('scpi', {command:text});
      $('scpi-output').textContent = `${text}\n${r.response ?? '(Set command: no normal response)'}\n${r.error}`;
      if(!r.error.startsWith('0,')) throw new Error(`${text}: ${r.error}`);
    }
    notice('');
  } catch(e) {
    scopeError = `Scope ${enabled ? 'start' : 'stop'} failed: ${e.message}`;
    notice(e);
  } finally {
    scopeChanging = false;
    await refresh().catch(notice);
    await refreshScope();
    if(scopeError) $('scope-status').textContent = scopeError;
  }
}
$('scope-start').onclick = () => setScope(true);
$('scope-stop').onclick = () => setScope(false);
