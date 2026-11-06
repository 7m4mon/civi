import socket
import asyncio
import json
import re
from pathlib import Path
import psutil


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


class Discovery:
    def __init__(self):
        self.zc, self.services = None, []
        self.description = None
        self.last_error = None
        self.lock = asyncio.Lock()
        self.signature = None

    async def start(self, config, identity=None):
        from zeroconf import ServiceInfo, IPVersion
        from zeroconf import NonUniqueNameException
        from zeroconf.asyncio import AsyncZeroconf
        if not config.get('discovery', True): return
        ips = self.addresses(config)
        if not ips: return
        self.zc = AsyncZeroconf(ip_version=IPVersion.V4Only)
        server = 'civi-' + re.sub('[^a-z0-9-]', '-', config['serial_number'].lower())[:50].strip('-') + '.local.'
        fields = identity or {'Manufacturer': config['manufacturer'], 'Model': 'CIVI/Unknown',
                              'SerialNumber': config['serial_number'], 'FirmwareRevision': 'Unknown'}
        txt = {'txtvers': '1', **{('FirmwareVersion' if k == 'FirmwareRevision' else k): v for k,v in fields.items()}}
        for k, v in txt.items():
            if len((k + '=' + str(v)).encode('utf-8')) > 255:
                await self.close()
                raise ValueError('Discovery identity exceeds DNS-SD TXT record limit')
        # Retry the complete group so all advertised services keep one instance name.
        name = config.get('description', f'CIVI {config["serial_number"]}')
        for attempt in range(1, 101):
            suffix = '' if attempt == 1 else f' ({attempt})'
            instance = name.encode('utf-8')[:63-len(suffix)].decode('utf-8', errors='ignore') + suffix
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
                return
            except NonUniqueNameException:
                await self._unregister()
            except BaseException:
                await self.close()
                raise
        await self.close()
        raise ValueError('Discovery service name conflicts exhausted')

    @staticmethod
    def addresses(config):
        return sorted({ip for i in network_info()['interfaces'] if i['up'] for ip in i['ipv4']
                       if not ip.startswith('127.') and config['bind'] in ('0.0.0.0', ip)})

    async def refresh(self, config, identity):
        async with self.lock:
            signature = (config.get('discovery', True), config.get('description'),
                         tuple(self.addresses(config)), tuple(identity.items()))
            if signature == self.signature: return
            await self.close()
            self.last_error = None
            try:
                await self.start(config, identity)
                self.signature = signature
            except Exception as error:
                self.last_error = str(error)
                raise

    async def configure(self, config, data, identity):
        validate_settings(data)
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
        if self.zc:
            try: await self._unregister()
            finally:
                await self.zc.async_close()
                self.zc = None
        self.description = None


def validate_settings(data):
    if set(data) != {'description', 'discovery'} or type(data['discovery']) is not bool:
        raise ValueError('Expected description and discovery')
    name = data['description']
    if not isinstance(name, str) or not name.strip() or len(name.encode('utf-8')) > 63 or any(ord(c) < 32 for c in name):
        raise ValueError('Description must contain 1-63 UTF-8 bytes and no control characters')
