"""Opt-in, one-interface DNS-SD collision fixture; no HTTP/SCPI service.

Stop with Ctrl+C or create OUTPUT/stop. Normal shutdown withdraws all records.
Never launched by CIVI. Run only on the isolated direct-cable test interface.
"""
import argparse
import ipaddress
import json
from pathlib import Path
import re
import socket
import time

import psutil
from zeroconf import IPVersion, ServiceInfo, Zeroconf, DNSOutgoing
from zeroconf._protocol.incoming import DNSIncoming


TYPES = ('_http._tcp.local.', '_lxi._tcp.local.', '_scpi-raw._tcp.local.', '_https._tcp.local.')


def validate(address, hostname, instance, local_addresses):
    ip = ipaddress.IPv4Address(address)
    if (not ip.is_private or ip.is_loopback or ip.is_link_local or
            ip.is_unspecified or ip.is_multicast or str(ip) not in local_addresses):
        raise ValueError('Select an explicitly assigned private test-interface IPv4 address')
    if not hostname.endswith('.local.'):
        raise ValueError('Use a single-label .local. hostname')
    label = hostname[:-7]
    if not re.fullmatch(r'[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?', label):
        raise ValueError('Invalid test hostname')
    if (not isinstance(instance, str) or not instance.strip() or len(instance.encode('utf-8')) > 63
            or any(ord(c) < 32 or ord(c) == 127 for c in instance)):
        raise ValueError('Invalid test service instance')


def services(address, hostname, instance):
    """Different SRV/TXT payloads make this an actual conflict, not a duplicate."""
    fields = {'txtvers':'1', 'Manufacturer':'CIVI test fixture', 'Model':'Collision peer',
              'SerialNumber':'TEST-ONLY', 'FirmwareVersion':'fixture', 'test':'collision-only'}
    return [ServiceInfo(type_, f'{instance}.{type_}', server=hostname,
                        addresses=[socket.inet_aton(address)], port=49990+i,
                        properties={**fields, **({'path':'/collision-fixture'} if type_ in (TYPES[0], TYPES[3]) else {})},
                        host_ttl=30, other_ttl=30)
            for i, type_ in enumerate(TYPES)]


def hostname_answer(packet, hostname, record):
    """An established owner answers probes; advertisements alone are insufficient."""
    incoming = DNSIncoming(packet)
    if not incoming.valid or not incoming.is_query():
        return None
    if not any(question.name.lower()==hostname.lower() and question.type in (1,255)
               for question in incoming.questions):
        return None
    answer = DNSOutgoing(0x8400)  # authoritative mDNS response, not a competing probe
    answer.add_answer_at_time(record, 0)
    return answer.packets()[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--interface-ip', required=True)
    parser.add_argument('--hostname', required=True)
    parser.add_argument('--instance', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=900)
    parser.add_argument('--interface-index', type=int, help='Windows packet-info authority for hostname probe replies')
    args = parser.parse_args()
    if not 30 <= args.seconds <= 1800:
        parser.error('Runtime must be 30–1800 seconds')
    stats = psutil.net_if_stats()
    addresses = {a.address for name, items in psutil.net_if_addrs().items()
                 if name in stats and stats[name].isup for a in items if a.family == socket.AF_INET}
    validate(args.interface_ip, args.hostname, args.instance, addresses)
    args.output.mkdir(parents=True, exist_ok=True)
    if (args.output/'stop').exists():
        raise RuntimeError('Use a fresh output directory; a stop request already exists')
    zc = Zeroconf(interfaces=[args.interface_ip], ip_version=IPVersion.V4Only)
    registered = []
    authority = None
    try:
        if args.interface_index is not None:
            # Keep DHCP's default exclusive transport unchanged. mDNS deliberately
            # shares 5353, but every received packet is checked against this NIC.
            from windows_pktinfo import Datagram
            socket.if_indextoname(args.interface_index)
            authority = Datagram(5353, exclusive=False)
            authority.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP,
                                      socket.inet_aton('224.0.0.251')+socket.inet_aton(args.interface_ip))
            authority.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 255)
        for info in services(args.interface_ip, args.hostname, args.instance):
            zc.register_service(info, allow_name_change=False)
            registered.append(info)
        ready = {'hostname':args.hostname, 'instance':args.instance,
                 'interface_ip':args.interface_ip, 'services':len(registered), 'started':time.time()}
        (args.output/'ready.json').write_text(json.dumps(ready, indent=2))
        print(json.dumps(ready), flush=True)
        end = time.monotonic()+args.seconds
        responses = 0
        while time.monotonic() < end and not (args.output/'stop').exists():
            if authority is None:
                time.sleep(.25)
                continue
            received = authority.receive(.25)
            if not received:
                continue
            packet, peer, interface, _ = received
            if interface != args.interface_index or peer[1] != 5353 or peer[0] == args.interface_ip:
                continue
            reply = hostname_answer(packet, args.hostname, registered[0].dns_addresses()[0])
            if reply:
                authority.send(reply, ('224.0.0.251',5353), args.interface_index, args.interface_ip)
                responses += 1
                (args.output/'host-responses.json').write_text(json.dumps({'responses':responses,'time':time.time()}))
    except KeyboardInterrupt:
        pass
    finally:
        for info in reversed(registered):
            zc.unregister_service(info)
        zc.close()
        if authority:
            authority.close()
        (args.output/'stopped.json').write_text(json.dumps({'stopped':time.time(), 'withdrawn':len(registered)}))
        print('Collision fixture stopped; records withdrawn.', flush=True)


if __name__ == '__main__':
    main()
