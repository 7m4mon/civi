"""Manual single-client DHCP fixture; never starts with the CIVI gateway.

Only a configured MAC on one received Windows interface may obtain one address.
Replies explicitly select the same interface and its local source IP. No relay,
NAK, routing, DNS service, address pool or automatic firewall change is provided.
"""
import argparse
import ctypes
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import struct
import time

COOKIE = b'\x63\x82\x53\x63'
ZERO = bytes(4)


def options(packet):
    if len(packet) < 240 or packet[236:240] != COOKIE:
        raise ValueError('Not a complete DHCP message')
    found, offset = {}, 240
    while offset < len(packet):
        code = packet[offset]
        offset += 1
        if code == 255:
            return found
        if code == 0:
            continue
        if offset == len(packet):
            raise ValueError('Missing option length')
        length = packet[offset]
        offset += 1
        if offset + length > len(packet) or code in found:
            raise ValueError('Truncated or repeated option')
        found[code] = packet[offset:offset+length]
        offset += length
    raise ValueError('Missing DHCP end option')


def option(code, value):
    if len(value) > 255:
        raise ValueError('DHCP option too long')
    return bytes([code, len(value)]) + value


class Policy:
    def __init__(self, config):
        required = {'interface_index', 'server_ip', 'client_ip', 'client_mac'}
        if not required <= set(config) or set(config) - required - {'lease_seconds'}:
            raise ValueError('Expected explicit interface, server/client IP and client MAC')
        self.lease = config.get('lease_seconds', 120)
        if type(self.lease) is not int or self.lease not in (60, 120):
            raise ValueError('The controlled fixture supports only 60 or 120 second leases')
        index = config['interface_index']
        if type(index) is not int or index < 1:
            raise ValueError('Invalid interface index')
        self.interface = index
        self.server = str(ipaddress.IPv4Address(config['server_ip']))
        self.client = str(ipaddress.IPv4Address(config['client_ip']))
        self.network = ipaddress.IPv4Network(self.server + '/24', strict=False)
        if not self.network.is_private or self.network.is_loopback or self.network.is_link_local:
            raise ValueError('Use an isolated private /24 test network')
        for address in (self.server, self.client):
            ip = ipaddress.IPv4Address(address)
            if ip not in self.network or ip in (self.network.network_address, self.network.broadcast_address):
                raise ValueError('Server/client must be usable addresses in the same /24')
        if self.server == self.client:
            raise ValueError('Server and client must differ')
        if not re.fullmatch(r'(?:[0-9a-fA-F]{2}:){5}[0-9a-fA-F]{2}', config['client_mac']):
            raise ValueError('Invalid client MAC')
        self.mac = bytes.fromhex(config['client_mac'].replace(':', ''))
        if self.mac[0] & 1 or self.mac == bytes(6):
            raise ValueError('Expected unicast client MAC')

    def state(self, data):
        if not isinstance(data, dict) or set(data) != {'enabled', 'gateway', 'dns', 'hostname'}:
            raise ValueError('Invalid server control state')
        if type(data['enabled']) is not bool or not isinstance(data['dns'], list):
            raise ValueError('Expected enabled boolean and DNS list')
        for value in ([data['gateway']] if data['gateway'] else []) + data['dns']:
            address = ipaddress.IPv4Address(value)
            if address not in self.network or address in (self.network.network_address, self.network.broadcast_address):
                raise ValueError('Only test-subnet gateway/DNS options may be advertised')
        if len(data['dns']) > 3 or (data['hostname'] and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9-]{0,62}', data['hostname'])):
            raise ValueError('Invalid test hostname/DNS options')
        return data

    def reply(self, packet, peer, interface, state):
        """Return (payload, destination, observation), or None without sending."""
        if interface != self.interface or peer[1] != 68:
            return None
        try:
            values = options(packet)
        except ValueError:
            return None
        if packet[:4] != b'\x01\x01\x06\x00' or packet[28:34] != self.mac or packet[24:28] != ZERO:
            return None
        # This controlled fixture does not support overloaded option fields.
        if 52 in values or values.get(53) not in (b'\x01', b'\x03'):
            return None
        kind = values[53][0]
        observation = {'request': kind, 'xid': packet[4:8].hex(),
                       'ciaddr': socket.inet_ntoa(packet[12:16]),
                       'requested_options': list(values.get(55, b'')), 'interface': interface}
        self.state(state)
        if not state['enabled']:
            return None
        if 54 in values and values[54] != socket.inet_aton(self.server):
            return None
        if kind == 3:
            wanted = values.get(50, packet[12:16])
            if wanted != socket.inet_aton(self.client):
                return None
        if packet[12:16] not in (ZERO, socket.inet_aton(self.client)):
            return None
        response = bytearray(240)
        response[:4] = b'\x02\x01\x06\x00'
        response[4:8] = packet[4:8]
        response[10:12] = packet[10:12]
        if kind == 3:
            response[12:16] = packet[12:16]
        response[16:20] = socket.inet_aton(self.client)
        response[28:44] = packet[28:44]
        response[236:240] = COOKIE
        # Explicit, short lab lease; no gateway/client timing constants change.
        entries = [(53, bytes([2 if kind == 1 else 5])), (54, socket.inet_aton(self.server)),
                   (51, struct.pack('!I', self.lease)), (58, struct.pack('!I', self.lease//2)),
                   (59, struct.pack('!I', self.lease*7//8)), (1, socket.inet_aton('255.255.255.0'))]
        if state['gateway']:
            entries.append((3, socket.inet_aton(state['gateway'])))
        if state['dns']:
            entries.append((6, b''.join(socket.inet_aton(ip) for ip in state['dns'])))
        if state['hostname']:
            entries.append((12, state['hostname'].encode('ascii')))
        if 61 in values:
            entries.append((61, values[61]))
        for code, value in entries:
            response.extend(option(code, value))
        response.append(255)
        response.extend(bytes(max(0, 300-len(response))))
        # RFC2131 4.1 permits broadcast if pre-address unicast is unavailable.
        # No static ARP entry or host networking changes are needed for this lab.
        # NM may retain the previous ciaddr in a DISCOVER sent from 0.0.0.0
        # after expiry. That address is no longer configured: do not require
        # zero ciaddr or try ARP-based unicast to it during reacquisition.
        destination = self.client if kind == 3 and peer[0] == self.client and packet[12:16] != ZERO else '255.255.255.255'
        return bytes(response), (destination, 68), {**observation, 'reply': 2 if kind == 1 else 5,
                    'lease_seconds': self.lease, 'gateway': state['gateway'], 'dns': state['dns'], 'hostname_option': state['hostname']}


def check_windows_route(policy):
    if os.name != 'nt':
        raise OSError('This manual test fixture is Windows-only')
    socket.if_indextoname(policy.interface)
    api = ctypes.WinDLL('Iphlpapi')
    api.GetBestInterface.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint32)]
    api.GetBestInterface.restype = ctypes.c_uint32
    found = ctypes.c_uint32()
    address = struct.unpack('=I', socket.inet_aton(policy.client))[0]
    if api.GetBestInterface(address, ctypes.byref(found)) or found.value != policy.interface:
        raise OSError('Client route does not use the explicitly selected test interface')
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.bind((policy.server, 0))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=600)
    parser.add_argument('--check', action='store_true', help='Check route and exclusive UDP67 bind, then close without sending')
    args = parser.parse_args()
    if not 30 <= args.seconds <= 1800:
        parser.error('Runtime must be 30–1800 seconds')
    policy = Policy(json.loads(args.config.read_text(encoding='utf-8')))
    policy.state(json.loads(args.state.read_text(encoding='utf-8')))
    check_windows_route(policy)
    from windows_pktinfo import Datagram
    transport = Datagram(67)
    try:
        if args.check:
            print('Route, local address, packet metadata and exclusive UDP67 bind OK. No packets sent.')
            return
        args.output.mkdir(parents=True, exist_ok=True)
        ready = {'pid': os.getpid(), 'interface_index': policy.interface,
                 'server_ip': policy.server, 'client_ip': policy.client, 'seconds': args.seconds,
                 'lease_seconds': policy.lease}
        (args.output/'ready.json').write_text(json.dumps(ready))
        print('Single-client DHCP test server ready; selected NIC only. Ctrl+C to stop.', flush=True)
        end = time.monotonic() + args.seconds
        with (args.output/'packets.jsonl').open('a', encoding='utf-8') as log:
            while time.monotonic() < end:
                received = transport.receive(1)
                if received is None:
                    continue
                packet, peer, interface, destination = received
                # Never log unrelated devices or accept a packet without NIC metadata.
                if interface != policy.interface or len(packet) < 34 or packet[28:34] != policy.mac:
                    continue
                state = policy.state(json.loads(args.state.read_text(encoding='utf-8')))
                reply = policy.reply(packet, peer, interface, state)
                event = {'time': time.time(), 'peer': peer, 'destination': destination,
                         'enabled': state['enabled'], 'packet_hex': packet.hex()}
                if reply:
                    payload, address, observation = reply
                    transport.send(payload, address, policy.interface, policy.server)
                    event.update(observation, sent_to=address, reply_hex=payload.hex())
                    print('OFFER' if observation['reply'] == 2 else 'ACK',
                          'ciaddr='+observation['ciaddr'], f'lease={policy.lease}s', flush=True)
                log.write(json.dumps(event)+'\n')
                log.flush()
    except KeyboardInterrupt:
        pass
    finally:
        transport.close()
        if not args.check:
            (args.output/'stopped.json').write_text(json.dumps({'time': time.time()}))
            print('DHCP test server stopped.', flush=True)


if __name__ == '__main__':
    main()
