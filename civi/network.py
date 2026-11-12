import socket
import asyncio
import json
import re
import ipaddress
from pathlib import Path
import psutil
from .discovery_state import load_names, save_names, names


def network_info(port=5025):
    interfaces = []
    stats = psutil.net_if_stats()
    for name, addrs in psutil.net_if_addrs().items():
        ips = [a.address for a in addrs if a.family == socket.AF_INET]
        mac = next((a.address for a in addrs if a.family == psutil.AF_LINK), None)
        interfaces.append({"name": name, "ipv4": ips, "mac": mac,
                           "up": bool(stats.get(name) and stats[name].isup),
                           "visa": [f"TCPIP::{ip}::{port}::SOCKET" for ip in ips]})
    return {"hostname": socket.gethostname(), "interfaces": interfaces}


def lxi_interfaces(config, network):
    """Pi claims only its configured wired NIC; never claim loopback as LXI."""
    pi = config.get('pi_network', {})
    if pi.get('enabled'):
        name = pi.get('interface', 'eth0')
        return [item for item in network['interfaces'] if item['name'] == name] or [
            {'name': name, 'ipv4': [], 'mac': None, 'visa': [], 'up': False}]
    return [item for item in network['interfaces']
            if any(not ipaddress.IPv4Address(ip).is_loopback for ip in item['ipv4'])]


class Discovery:
    def __init__(self):
        self.zc, self.services = None, []
        self.description = None
        self.last_error = None
        self.lock = asyncio.Lock()
        self.signature = None
        self.avahi = None
        self.hostname = None
        self.device_mdns = None

    @staticmethod
    def server_name(config):
        if config.get('pi_network', {}).get('enabled'):
            from .pi.network import hostname_label
            try: return hostname_label(socket.gethostname()) + '.local.'
            except ValueError: pass
        return 'civi-' + re.sub('[^a-z0-9-]', '-', config['serial_number'].lower())[:50].strip('-') + '.local.'

    async def start(self, config, identity=None):
        from zeroconf import ServiceInfo, IPVersion
        from zeroconf import NonUniqueNameException
        from zeroconf.asyncio import AsyncZeroconf
        if not config.get('discovery', True): return
        ips = self.addresses(config)
        if not ips: return
        fields = identity or {'Manufacturer': config['manufacturer'], 'Model': 'CIVI/Unknown',
                              'SerialNumber': config['serial_number'], 'FirmwareRevision': 'Unknown'}
        if config.get('pi_network',{}).get('enabled'):
            from .pi.discovery import AvahiDiscovery
            self.avahi=AvahiDiscovery()
            await self.avahi.start(config,fields,self.server_name(config)[:-7])
            self._avahi_metadata(config,ips)
            return
        self.zc = AsyncZeroconf(ip_version=IPVersion.V4Only)
        server = self.server_name(config)
        txt = {'txtvers': '1', **{('FirmwareVersion' if k == 'FirmwareRevision' else k): v for k,v in fields.items()}}
        for k, v in txt.items():
            if len((k + '=' + str(v)).encode('utf-8')) > 255:
                await self.close()
                raise ValueError('Discovery identity exceeds DNS-SD TXT record limit')
        # Retry the complete group so all advertised services keep one instance name.
        name = config.get('description', f'CIVI {config["serial_number"]}')
        saved=load_names(config,server[:-7],name)
        for instance in names(name,saved['service'] if saved else None):
            try:
                for service, port in (('_http._tcp.local.', config['web_port']),
                                      ('_lxi._tcp.local.', config['web_port']),
                                      ('_scpi-raw._tcp.local.', config['scpi_port']),
                                      ('_https._tcp.local.', config['web_port'])):
                    properties = {'txtvers':'1', 'path':'/lxi'} if service in ('_http._tcp.local.','_https._tcp.local.') else txt
                    info = ServiceInfo(service, f'{instance}.{service}',
                                       addresses=[socket.inet_aton(ip) for ip in ips], port=port,
                                       server=server, properties=properties)
                    await self.zc.async_register_service(info)
                    self.services.append(info)
                self.description, self.last_error = instance, None
                self.hostname=server
                save_names(config,server[:-7],name,server[:-7],instance)
                return
            except NonUniqueNameException:
                try:
                    await self._unregister()
                    await asyncio.sleep(.1)
                except BaseException:
                    await self.close()
                    raise
            except BaseException:
                await self.close()
                raise
        await self.close()
        raise ValueError('Discovery service name conflicts exhausted')

    def _avahi_metadata(self,config,ips):
        from zeroconf import ServiceInfo
        self.description=self.avahi.name
        self.hostname=self.avahi.hostname
        self.last_error=None
        self.services=[ServiceInfo(service+'.local.',self.description+'.'+service+'.local.',
            port=port,server=self.hostname,addresses=[socket.inet_aton(ip) for ip in ips])
            for service,port in self.avahi.service_ports(config)]

    @staticmethod
    def addresses(config):
        return sorted({ip for i in lxi_interfaces(config, network_info()) if i['up'] for ip in i['ipv4']
                       if not ip.startswith('127.') and config['bind'] in ('0.0.0.0', ip)})

    async def refresh(self, config, identity):
        async with self.lock:
            signature = (config.get('discovery', True), config.get('description'),
                         tuple(self.addresses(config)), tuple(identity.items()), self.server_name(config),
                         config.get('discovery_reset_revision'))
            try:
                if config.get('pi_network',{}).get('enabled'):
                    from .pi.broker import BrokerClient
                    self.device_mdns=None
                    if not config.get('discovery',True): await self.close()
                    self.device_mdns=await asyncio.to_thread(BrokerClient(config['pi_network'].get('socket','/run/civi-lan/control.sock')).request,
                                                           'mdns',enabled=config.get('discovery',True))
                    if not config.get('discovery',True):
                        self.last_error=None;self.signature=signature
                        config.pop('_avahi_hostname_initialized',None)
                        return
                if signature == self.signature:
                    if not self.avahi: return
                    if await self.avahi.inspect():
                        self._avahi_metadata(config,self.addresses(config));return
                await self.close()
                self.last_error = None
                await self.start(config, identity)
                self.signature = signature
            except Exception as error:
                if self.avahi: config.pop('_avahi_hostname_initialized',None)
                await self.close()
                self.signature=None
                self.last_error = str(error)
                raise

    async def configure(self, config, data, identity):
        if isinstance(data, dict) and isinstance(data.get('description'), str) and not data['description'].strip():
            from .defaults import default_description
            data = {**data, 'description': default_description(config)}
        data = normalize_settings(data)
        path = config.get('network_settings_file')
        if not path: raise ValueError('Persistent network settings file is unavailable')
        async with self.lock:
            target = Path(path)
            temporary = target.with_suffix('.tmp')
            try:
                temporary.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
            config.update(data)
            self.signature = None
        # A registration failure is visible; the saved desired state is retained.
        try: await self.refresh(config, identity)
        except Exception: pass

    async def _unregister(self):
        for s in self.services:
            await self.zc.async_unregister_service(s)
        self.services.clear()

    async def close(self):
        if self.avahi:
            try: await self.avahi.close()
            finally: self.avahi=None; self.services=[]
        if self.zc:
            try: await self._unregister()
            finally:
                await self.zc.async_close()
                self.zc = None
        self.description = None
        self.hostname = None


def validate_settings(data):
    if not isinstance(data, dict) or set(data) != {'description', 'discovery'} or type(data['discovery']) is not bool:
        raise ValueError('Expected description and discovery')
    name = data['description']
    if not isinstance(name, str) or not name.strip() or len(name.encode('utf-8')) > 63 or any(ord(c) < 32 for c in name):
        raise ValueError('Description must contain 1-63 UTF-8 bytes and no control characters')


def normalize_settings(data):
    """Validate the entire input, then truncate on a complete UTF-8 boundary."""
    if not isinstance(data, dict) or set(data) != {'description', 'discovery'}:
        raise ValueError('Expected description and discovery')
    name = data['description']
    if not isinstance(name, str) or not name.strip() or any(ord(c) < 32 for c in name):
        raise ValueError('Description must be nonblank and contain no control characters')
    result = {**data, 'description': name.encode('utf-8')[:63].decode('utf-8', errors='ignore')}
    validate_settings(result)
    return result
