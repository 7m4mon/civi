"""LXI identification building blocks; no claim of LXI conformance."""
from xml.etree import ElementTree as ET
from html import escape
from . import __version__

NAMESPACE = 'http://lxistandard.org/schemas/InstrumentIdentification/2.0'
XSI = 'http://www.w3.org/2001/XMLSchema-instance'
SCHEMA_PATH = '/InstrumentIdentification/2.0'
ET.register_namespace('', NAMESPACE)
ET.register_namespace('xsi', XSI)


def identity(service):
    return {'Manufacturer': service.config['manufacturer'],
            'Model': 'CIVI/' + (service.identified_model or 'Unknown'),
            'SerialNumber': service.config['serial_number'], 'FirmwareRevision': __version__}


def identification_xml(service, network, base_url, description, connected=False):
    root = ET.Element(f'{{{NAMESPACE}}}LXIDevice',
                      {f'{{{XSI}}}schemaLocation': f'{NAMESPACE} {base_url}{SCHEMA_PATH}'})
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
        for interface in network['interfaces']:
            if not interface['ipv4']:
                continue
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


def information_page(service, network, discovery, settings=False):
    """Server-rendered public information, with no dependency on radio readiness."""
    e = lambda value: escape(str(value), quote=True)
    rows = identity(service)
    rows.update({'Description': discovery.description or service.config['description'],
                 'LXI version': 'Not claimed; implementation incomplete',
                 'LXI extended functions': 'None claimed',
                 'Radio connection': service.backend.state,
                 'Discovery requested': 'Enabled' if service.config.get('discovery') else 'Disabled',
                 'Discovery active': 'Yes' if discovery.services else 'No',
                 'Discovery error': discovery.last_error or 'None'})
    body = '<dl>' + ''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k,v in rows.items()) + '</dl>'
    interfaces = '<h2>LAN interfaces</h2>'
    for item in sorted(network['interfaces'], key=lambda item: not item.get('up')):
        if not item['ipv4']: continue
        if not item.get('up'):
            interfaces += f'<details><summary>{e(item["name"])} — Link down</summary>'
        interfaces += f'<h3>{e(item["name"])}</h3><dl>'
        for key, value in [('Link', 'Up' if item.get('up') else 'Down'),
                           # IP fallback avoids claiming an unvalidated DNS hostname.
                           ('Hostname / IP fallback', ', '.join(item['ipv4'])),
                           ('TCP/IP address', ', '.join(item['ipv4'])),
                           ('MAC address', (item.get('mac') or 'Unknown').replace(':','-').upper())]:
            interfaces += f'<dt>{e(key)}</dt><dd>{e(value)}</dd>'
        for resource in item['visa']:
            interfaces += f'<dt>Instrument Address String</dt><dd><code>{e(resource)}</code></dd>'
        interfaces += '</dl>'
        if not item.get('up'): interfaces += '</details>'
    if settings:
        body += f'''<h2>Discovery settings</h2>
<p>Changes are saved for future manual launches. IP configuration remains managed by the OS.</p>
<form id="network-form"><label>Description / service name (up to 63 UTF-8 bytes)
<input id="description" value="{e(service.config['description'])}" required></label>
<label><input id="discovery" type="checkbox" {'checked' if service.config.get('discovery') else ''}> Enable mDNS / DNS-SD</label>
<label>Administrator password<input id="network-password" type="password" autocomplete="current-password" required></label>
<button>Save and apply</button></form><p id="network-result" role="status"></p>
<p>Hostname, DHCP/AutoIP, static IP, gateway, DNS and LAN configuration reset are not implemented here.</p>'''
    body += interfaces
    script = '<script src="/static/network.js" defer></script>' if settings else ''
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>CIVI — {'LAN information' if settings else 'Welcome'}</title>
<link rel="stylesheet" href="/static/style.css">{script}</head><body><main>
<section class="card"><h1>CIVI — {'LAN information and discovery' if settings else 'Welcome'}</h1>
<p class="badge">LXI implementation in progress · Not LXI conformant or certified</p>
<nav><a href="/">Radio control</a> · <a href="/lxi">Welcome</a> · <a href="/network">LAN information / discovery settings</a> ·
<a href="/lxi/identification">Identification XML</a> · <a href="/help">Local documentation</a></nav>
{body}</section></main></body></html>'''
