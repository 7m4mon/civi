"""LXI identification building blocks; no claim of LXI conformance."""
from xml.etree import ElementTree as ET
from html import escape
from . import __version__
from .network import lxi_interfaces

NAMESPACE = 'http://lxistandard.org/schemas/InstrumentIdentification/2.0'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'
SCHEMA_PATH = '/InstrumentIdentification/2.0'
STANDARD_SCHEMA_PATH = '/lxi/schemas/InstrumentIdentification/2.0'
ET.register_namespace('', NAMESPACE)
ET.register_namespace('xsi', XSI)


def identity(service):
    return {'Manufacturer': service.config['manufacturer'],
            'Model': 'CIVI/' + (service.identified_model or 'Unknown'),
            'SerialNumber': service.config['serial_number'], 'FirmwareRevision': __version__}


def identification_xml(service, network, base_url, description, connected=False):
    root = ET.Element(f'{{{NAMESPACE}}}LXIDevice',
                      {f'{{{XSI}}}schemaLocation': f'{NAMESPACE} {base_url}{STANDARD_SCHEMA_PATH}'})
    def add(parent, tag, text):
        element = ET.SubElement(parent, f'{{{NAMESPACE}}}{tag}')
        element.text = str(text)
        return element
    fields = identity(service)
    if connected:
        fields = dict(Manufacturer='Icom', Model=service.identified_model or 'Unknown',
                      SerialNumber='Unknown', FirmwareRevision=service.config.get('radio_firmware') or 'Unknown')
    for key, value in fields.items():
        add(root, key, value)
    if not connected and service.identified_model:
        devices = ET.SubElement(root, f'{{{NAMESPACE}}}ConnectedDevices')
        add(devices, 'DeviceURI', base_url + '/devices/radio')
    add(root, 'UserDescription', description)
    add(root, 'IdentificationURL', base_url + ('/devices/radio' if connected else '') + '/lxi/identification')
    if not connected:
        for interface in lxi_interfaces(service.config, network):
            item = ET.SubElement(root, f'{{{NAMESPACE}}}Interface',
                                 InterfaceType='LXI', InterfaceName=interface['name'], IPType='IPv4')
            for resource in interface['visa']:
                add(item, 'InstrumentAddressString', resource)
            for ip in interface['ipv4']:
                add(item, 'IPAddress', ip)
            if interface.get('mac'):
                add(item, 'MACAddress', interface['mac'].replace(':', '-').upper())
    # LXIVersion is deliberately omitted: the device does not yet conform to LXI.
    return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def information_page(service, network, discovery, settings=False, indicator=None):
    """Server-rendered public information, with no dependency on radio readiness."""
    e = lambda value: escape(str(value), quote=True)
    claimed_interfaces = lxi_interfaces(service.config, network)
    # Only a successfully registered name is an actual mDNS hostname. The OS
    # hostname below is configuration information, not a DNS validation claim.
    actual_hostname = (getattr(discovery, 'hostname', None)
                       if service.config.get('discovery') and discovery.services and not discovery.last_error else None)
    hostname_display = actual_hostname or ', '.join(
        ip for item in claimed_interfaces for ip in item['ipv4']) or 'Not assigned'
    rows = identity(service)
    rows.update({'Hostname': hostname_display,
                 'System hostname': network.get('hostname', 'Unknown'),
                 'Advertised mDNS hostname': actual_hostname or 'Not active',
                 'Description': discovery.description or service.config['description'],
                 'LXI version': 'Not claimed; implementation incomplete',
                 'LXI extended functions': 'None claimed',
                 'Radio connection': service.backend.state,
                 'Discovery requested': 'Enabled' if service.config.get('discovery') else 'Disabled',
                 'Discovery active': 'Yes' if discovery.services else 'No',
                 'Discovery error': discovery.last_error or 'None'})
    if service.config.get('pi_network',{}).get('enabled'):
        mdns=getattr(discovery,'device_mdns',None)
        rows['Device mDNS']=('Enabled (Avahi running)' if mdns['enabled'] else 'Disabled (Avahi stopped; activation blocked)') if mdns else 'Not verified; check discovery error'
    body = '<dl>' + ''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k,v in rows.items()) + '</dl>'
    interfaces = '<h2>LAN interfaces</h2>'
    claimed = {item['name'] for item in claimed_interfaces}
    for item in sorted(network['interfaces'], key=lambda item: not item.get('up')):
        if not item['ipv4'] and item['name'] not in claimed: continue
        if not item.get('up'):
            interfaces += f'<details><summary>{e(item["name"])} — Link down</summary>'
        interfaces += f'<h3>{e(item["name"])}</h3><dl>'
        if service.config.get('pi_network', {}).get('enabled'):
            role = 'LXI wired interface' if item['name'] in claimed else 'Management / non-LXI interface'
            interfaces += f'<dt>Interface role</dt><dd>{role}</dd>'
        for key, value in [('Link', 'Up' if item.get('up') else 'Down'),
                           # IP fallback avoids claiming an unvalidated DNS hostname.
                           ('Hostname / IP fallback', ', '.join(item['ipv4']) or 'Not assigned'),
                           ('TCP/IP address', ', '.join(item['ipv4']) or 'Not assigned'),
                           ('MAC address', (item.get('mac') or 'Unknown').replace(':','-').upper())]:
            interfaces += f'<dt>{e(key)}</dt><dd>{e(value)}</dd>'
        for resource in item['visa']:
            interfaces += f'<dt>Instrument Address String</dt><dd><code>{e(resource)}</code></dd>'
        interfaces += '</dl>'
        if not item.get('up'): interfaces += '</details>'
    if settings:
        limitation = ('Pi hostname and wired IPv4 settings are available below. LAN RESET is available from the Pi attached keyboard/display.'
                      if service.config.get('pi_network',{}).get('enabled') else
                      'Hostname, DHCP/AutoIP, static IP, gateway, DNS and LAN configuration reset are not implemented here.')
        body += f'''<h2 id="web-password">Change Web password</h2>
<form id="password-form">
<label>Current CIVI Web password<input id="password-current" name="current-password" type="password" autocomplete="current-password" required></label>
<label>New password (12–256 characters)<input id="password-new" name="new-password" type="password" autocomplete="new-password" minlength="12" maxlength="256" required></label>
<label>Confirm new password<input id="password-confirm" name="confirm-password" type="password" autocomplete="new-password" minlength="12" maxlength="256" required></label>
<button>Change password</button></form><p id="password-result" role="status"></p>
<p class="small">Use the current Web password; after LAN RESET, use the recovery password displayed on the Pi. The new password takes effect immediately and is saved for future starts. LAN RESET restores the device recovery default.</p>
<h2>Discovery settings</h2>
<p>Changes are saved for future manual launches. IP configuration remains managed by the OS.</p>
<form id="network-form"><label>Description / service name (saved as the first 63 UTF-8 bytes, without splitting characters)
<input id="description" value="{e(service.config['description'])}"></label>
<p class="small">Leave blank to restore the factory description (CIVI followed by the device serial number).</p>
<label><input id="discovery" type="checkbox" {'checked' if service.config.get('discovery') else ''}> Enable mDNS / DNS-SD</label>
<p class="small">On Pi, disabling stops device-wide Avahi hostname replies and service discovery on all interfaces, including other Avahi applications. Use the numeric IP address to reconnect and enable it again. Existing name caches may take time to expire. Windows only withdraws CIVI services.</p>
<label>CIVI Web password (username: admin)<input id="network-password" type="password" autocomplete="current-password" minlength="12" required></label>
<p class="small">Use the current CIVI Web password, not the Linux/sudo password. After LAN RESET, use the displayed recovery password.</p>
<button>Save and apply</button></form><p id="network-result" role="status"></p>
<p>{limitation}</p>'''
    body += interfaces
    if settings and service.config.get('pi_network',{}).get('enabled'):
        body += '''<h2 id="pi-lan">Pi wired LAN configuration</h2>
<p>Changes are temporary until confirmed through the new wired IPv4 address. NetworkManager rolls back after 90 seconds without confirmation.</p>
<form id="pi-network-form"><label>CIVI Web password (username: admin)<input id="pi-password" type="password" autocomplete="current-password" minlength="12" required></label>
<p class="small">Use the current CIVI Web password, not the Linux/sudo password. After LAN RESET, use the displayed recovery password.</p>
<button id="pi-read" type="button">Read wired LAN</button>
<fieldset><legend>IPv4 Ping responder</legend>
<p class="small">Controls IPv4 Ping replies on all Pi interfaces, including WLAN. HTTPS and SCPI remain available. Saved for future boots; LAN RESET enables replies again. IPv6 is unchanged.</p>
<button id="pi-read-ping" type="button">Read Ping setting</button>
<label><input id="pi-ping-enabled" type="checkbox" disabled> Enable IPv4 Ping replies</label>
<button id="pi-save-ping" type="button" disabled>Save Ping setting</button>
<p id="pi-ping-result" role="status">Read the current setting before changing it.</p></fieldset>
<fieldset><legend>System hostname</legend>
<label>Hostname<input id="pi-hostname" maxlength="63" placeholder="civi" pattern="[A-Za-z0-9][A-Za-z0-9-]*"></label>
<p class="small">Leave blank to restore the factory hostname: civi. This changes the system hostname immediately.</p>
<p class="small">Read wired LAN to load the current hostname. Save hostname applies immediately to the whole Pi and persists across restarts. It is separate from the 90-second IPv4 trial. IP addresses stay the same. Avahi resolves mDNS conflicts; the advertised name may have a numeric suffix. An existing HTTPS certificate may not cover the new name.</p>
<button id="pi-save-hostname" type="button">Save hostname</button>
<p id="pi-hostname-result" role="status"></p></fieldset>
<label>IPv4 mode<select id="pi-mode"><option value="static">Static IPv4</option><option value="automatic">DHCP with AutoIP fallback</option></select></label>
<label>IPv4 address<input id="pi-address" placeholder="192.168.73.2"></label>
<label>Prefix length<input id="pi-prefix" type="number" min="1" max="32" value="24"></label>
<p id="pi-subnet" class="small" role="status">Subnet mask: 255.255.255.0 (/24). Prefix length is the number of network bits.</p>
<label>Gateway (leave empty for direct connection)<input id="pi-gateway"></label>
<label>DNS servers (comma separated, optional)<input id="pi-dns"></label>
<div class="row"><button id="pi-preview" type="button">Preview</button><button id="pi-apply" type="button">Apply temporarily</button></div>
</form><div id="pi-guidance" class="card readiness" role="status" hidden></div>
<p id="pi-result" role="status"></p><p id="pi-reconnect"></p>
<button id="pi-confirm" type="button" disabled>Confirm and save</button>
<button id="pi-rollback" type="button" disabled>Restore previous settings</button>
<details><summary>LAN technical details</summary><pre id="pi-state"></pre></details>
<p class="small">For local LAN RESET, run bash lan-reset.sh from the Pi attached keyboard/display. See <a href="/help">local documentation</a>. Keep WLAN available as a management path during experiments.</p>'''
    script = '<script src="/static/network.js" defer></script>' if settings else ''
    if service.config.get('pi_network',{}).get('enabled'):
        body = '''<section class="card" id="lan-indicator"><h2>LAN status / Identify</h2>
<p><span id="lan-lamp" class="lan-lamp"></span> <strong id="lan-summary">Reading LAN status…</strong></p>
<p id="lan-details" role="status"></p><p id="identify-state"></p>
<form id="identify-form"><label>Current CIVI Web password<input id="identify-password" type="password" autocomplete="current-password" required></label>
<div class="row"><button type="submit" value="on">Start Identify</button><button type="submit" value="off">Stop Identify</button></div></form>
<p id="identify-result" role="status"></p>
<p class="small">Open bash panel.sh on the Pi attached display and keep the window visible. Identify flashes until stopped. The Ethernet connector LEDs continue their normal link/activity function.</p></section>''' + body
        script += '<script src="/static/indicator.js" defer></script>'
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CIVI — {'LAN information' if settings else 'Welcome'}</title>
<link rel="stylesheet" href="/static/style.css">{script}</head><body><main>
<section class="card"><h1>CIVI — {'LAN information and discovery' if settings else 'Welcome'}</h1>
<p class="badge">LXI implementation in progress · Not LXI conformant or certified</p>
<nav><a href="/">Radio control</a> · <a href="/lxi">Welcome</a> · <a href="/network">LAN information / discovery settings</a> ·
<a href="/lxi/identification">Identification XML</a> · <a href="/help">Local documentation</a></nav>
{body}</section></main></body></html>'''
