"""Read NetworkManager state and prepare IPv4 changes without applying them."""
from dataclasses import dataclass
import ipaddress
import os
import platform
import re
import subprocess


class NetworkError(RuntimeError):
    pass


def version_tuple(text):
    match = re.search(r'\b(\d+)\.(\d+)(?:\.(\d+))?\b', text)
    if not match:
        raise NetworkError('Cannot determine NetworkManager version')
    return tuple(int(part or 0) for part in match.groups())


def interface_name(value):
    if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,14}', value):
        raise ValueError('Invalid Linux interface name')
    return value


def ipv4(value):
    try:
        address = ipaddress.IPv4Address(value)
    except (ValueError, TypeError) as error:
        raise ValueError('Expected an IPv4 address') from error
    if address.is_multicast or address.is_unspecified or address.is_loopback or int(address) == 0xffffffff:
        raise ValueError('Expected a unicast LAN IPv4 address')
    return address


@dataclass(frozen=True)
class IPv4Settings:
    mode: str
    hostname: str = ''
    address: str = ''
    prefix: int | None = None
    gateway: str = ''
    dns: tuple[str, ...] = ()

    @classmethod
    def parse(cls, data):
        if not isinstance(data, dict) or set(data) - {'mode','hostname','address','prefix','gateway','dns'}:
            raise ValueError('Unknown network settings')
        if data.get('mode') not in ('automatic','static'):
            raise ValueError('mode must be automatic or static')
        hostname = data.get('hostname', '')
        if not isinstance(hostname, str) or (hostname and not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?', hostname)):
            raise ValueError('hostname must be a single DNS label of 1-63 characters')
        dns = data.get('dns', [])
        if not isinstance(dns, list) or len(dns) > 8 or any(not isinstance(x, str) for x in dns):
            raise ValueError('dns must be a list of up to eight IPv4 addresses')
        dns = tuple(str(ipv4(x)) for x in dns)
        address, prefix, gateway = data.get('address', ''), data.get('prefix'), data.get('gateway', '')
        if not isinstance(address, str) or not isinstance(gateway, str):
            raise ValueError('address and gateway must be strings')
        if data['mode'] == 'automatic':
            if address or prefix is not None or gateway:
                raise ValueError('Automatic mode cannot contain static address/prefix/gateway')
        else:
            if type(prefix) is not int or not 1 <= prefix <= 32:
                raise ValueError('Static mode requires prefix 1-32')
            ip = ipv4(address)
            network = ipaddress.IPv4Network(f'{ip}/{prefix}', strict=False)
            if prefix < 31 and ip in (network.network_address, network.broadcast_address):
                raise ValueError('Static address cannot be the network or broadcast address')
            if gateway:
                gw = ipv4(gateway)
                if gw not in network or gw == ip or (prefix < 31 and gw in (network.network_address, network.broadcast_address)):
                    raise ValueError('Gateway must be another usable address in the subnet')
        return cls(data['mode'], hostname, address, prefix, gateway, dns)


class NetworkManager:
    """Only read commands are executed. Mutation commands are returned as data."""
    def __init__(self, runner=None):
        self.runner = runner or subprocess.run

    def _read(self, *arguments):
        if platform.system() != 'Linux':
            raise NetworkError('Raspberry Pi network integration requires Linux and NetworkManager')
        try:
            result = self.runner(['nmcli','--colors','no','--escape','no', *arguments],
                                 capture_output=True, text=True, timeout=10,
                                 env={**os.environ, 'LC_ALL':'C'})
        except FileNotFoundError as error:
            raise NetworkError('nmcli is not installed') from error
        except subprocess.TimeoutExpired as error:
            raise NetworkError('NetworkManager query timed out') from error
        if result.returncode:
            raise NetworkError(result.stderr.strip() or f'nmcli failed with exit code {result.returncode}')
        return result.stdout.strip()

    def snapshot(self, interface):
        interface_name(interface)
        version = self._read('--version')
        daemon_version = self._read('-g','VERSION','general','status')
        active = self._read('-t','-f','UUID,DEVICE','connection','show','--active')
        matches = [line.split(':',1)[0] for line in active.splitlines() if line.partition(':')[2] == interface]
        if len(matches) != 1:
            raise NetworkError('Interface must have exactly one active NetworkManager profile')
        uuid = matches[0]
        if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', uuid):
            raise NetworkError('Invalid active connection UUID')
        fields = ('connection.id','connection.type','ipv4.method','ipv4.addresses','ipv4.gateway','ipv4.dns',
                  'ipv4.ignore-auto-dns','ipv4.never-default','ipv4.link-local')
        values = {field:self._read('-g',field,'connection','show','uuid',uuid) for field in fields}
        if values['connection.type'] != '802-3-ethernet':
            raise NetworkError('The initial Raspberry Pi target requires a wired Ethernet profile')
        return {'interface':interface, 'uuid':uuid, 'version':version, 'daemon_version':daemon_version,
                'autoip_fallback_supported':min(version_tuple(version), version_tuple(daemon_version)) >= (1,52,0),
                'hostname':self._read('general','hostname'), 'profile':values,
                'active_ipv4':self._read('-g','IP4.ADDRESS','device','show',interface),
                'active_gateway':self._read('-g','IP4.GATEWAY','device','show',interface),
                'active_dns':self._read('-g','IP4.DNS','device','show',interface)}


def plan_changes(snapshot, data):
    settings = IPv4Settings.parse(data)
    interface = interface_name(snapshot['interface'])
    uuid = snapshot['uuid']
    if not re.fullmatch(r'[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}', uuid):
        raise ValueError('Invalid profile UUID')
    if settings.mode == 'automatic' and not snapshot['autoip_fallback_supported']:
        raise NetworkError('DHCP plus AutoIP fallback needs NetworkManager >= 1.52; no fallback is silently omitted')
    commands = []
    if settings.hostname and settings.hostname != snapshot['hostname']:
        commands.append(['nmcli','general','hostname',settings.hostname])
    command = ['nmcli','connection','modify','uuid',uuid]
    command += ['ipv4.method', 'auto' if settings.mode == 'automatic' else 'manual']
    command += ['ipv4.addresses', f'{settings.address}/{settings.prefix}' if settings.mode == 'static' else '']
    command += ['ipv4.gateway', settings.gateway,
                'ipv4.dns', ','.join(settings.dns), 'ipv4.ignore-auto-dns', 'yes' if settings.dns else 'no']
    command += ['ipv4.never-default', 'yes' if not settings.gateway else 'no']
    if snapshot['autoip_fallback_supported']:
        command += ['ipv4.link-local', 'fallback' if settings.mode == 'automatic' else 'disabled']
    commands += [command, ['nmcli','connection','up','uuid',uuid,'ifname',interface]]
    return {'applied':False, 'interface':interface, 'profile_uuid':uuid,
            'requires_privileges':True, 'requires_rollback_and_confirmation':True,
            'commands':commands,
            'note':'Review only. No commands in this plan have been executed. Applying network settings may disconnect clients.'}
