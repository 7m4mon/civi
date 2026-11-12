"""Manual root-only real AutoIP/NSS/TCP check in isolated Pi namespaces.

No physical interface is moved or reconfigured. Uses the existing private
NetworkManager/Avahi laboratory and removes namespaces on exit.
"""
import ipaddress
import json
from pathlib import Path
import socket
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.pi_dhcp_check import command, run_lab
from tools.pi_mdns_check import config_text, private_avahi


def serve(base, address):
    with socket.socket() as listener:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((address, 18881))
        listener.listen(1)
        listener.settimeout(45)
        (base/'tcp.ready').touch()
        connection, _ = listener.accept()
        with connection:
            connection.settimeout(5)
            if connection.recv(128) != b'CIVI AutoIP test\n':
                raise ValueError('Unexpected test payload')
            connection.sendall(b'CIVI AutoIP reply\n')


def scenario(*, base, manager, tx, nm, scoped, prefix, server, selected,
             spawn, stop, wait, log):
    result = tx.apply({'mode':'automatic', 'dns':[]}, 180)
    tx.confirm(result['pending']['token'])

    def acquired():
        snapshot = manager.snapshot('lxi0')
        for address in snapshot['active_ipv4'].splitlines():
            if address and ipaddress.ip_interface(address).ip.is_link_local:
                return address.split('/')[0]
        return None

    address = wait(acquired, 75, 'real NetworkManager AutoIP acquisition')
    snapshot = manager.snapshot('lxi0')
    assert snapshot['profile']['ipv4.method'] == 'auto'
    assert not snapshot['profile']['ipv4.addresses']
    log('PASS: NetworkManager assigned AutoIP without a DHCP server')
    # Requester needs a same-link source, distinct from the acquired peer address.
    requester = '169.254.220.1' if address != '169.254.220.1' else '169.254.220.2'
    command(['ip','-n',server,'addr','add',requester+'/16','dev','srv0'])
    (base/'client.conf').write_text(config_text('civi-autoip-peer','lxi0'))
    (base/'peer.conf').write_text(config_text('civi-autoip-requester','srv0'))
    peer = spawn(['ip','netns','exec',server,'unshare','--mount','--uts',
                  sys.executable,__file__,'--peer',base], 'requester-avahi.log')
    wait(lambda:(base/'peer.pid').exists(), 10, 'requester private D-Bus startup')
    requester_prefix = ['nsenter','--target',(base/'peer.pid').read_text(),
                        '--mount','--net','--uts','--']
    authority = spawn(prefix+['unshare','--mount',sys.executable,__file__,
                             '--client',base], 'autoip-avahi.log')

    def ready(scope):
        p = subprocess.run(scope+['busctl','--system','call','org.freedesktop.Avahi',
            '/','org.freedesktop.Avahi.Server','GetState'],capture_output=True,text=True,timeout=3)
        return p.returncode == 0 and p.stdout.strip() == 'i 2'

    wait(lambda:ready(prefix) and ready(requester_prefix), 20, 'private Avahi probes')
    forward = command(requester_prefix+['getent','ahostsv4','civi-autoip-peer.local'])
    reverse = command(requester_prefix+['getent','hosts',address])
    assert address in forward and 'civi-autoip-peer.local' in reverse
    log('PASS: standard NSS forward and reverse lookups for allocated AutoIP')
    tcp = spawn(prefix+[sys.executable,__file__,'--serve',base,address], 'tcp.log')
    wait(lambda:(base/'tcp.ready').exists(), 10, 'AutoIP TCP listener startup')
    code = ("import socket; s=socket.create_connection(('"+address+"',18881),5);"
            "s.sendall(b'CIVI AutoIP test\\n'); r=s.recv(128);s.close();"
            "assert r==b'CIVI AutoIP reply\\n',r;print('AutoIP TCP passed')")
    tcp_result = command(requester_prefix+[sys.executable,'-c',code])
    tcp.wait(timeout=5)
    assert tcp.returncode == 0
    log('PASS: actual TCP request/reply using the allocated AutoIP address')
    checks = {'scope':'isolated Pi network namespaces; not physical Ethernet',
              'allocated_autoip':address,'requester_static_linklocal':requester,
              'snapshot':snapshot,'forward':forward,'reverse':reverse,'tcp':tcp_result}
    (base/'results.json').write_text(json.dumps(checks,indent=2))
    stop(authority)
    stop(peer)


if __name__ == '__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--peer':
        private_avahi(Path(sys.argv[2]), True)
    elif len(sys.argv)==3 and sys.argv[1]=='--client':
        private_avahi(Path(sys.argv[2]))
    elif len(sys.argv)==4 and sys.argv[1]=='--serve':
        serve(Path(sys.argv[2]), sys.argv[3])
    elif len(sys.argv)==1:
        run_lab(scenario, 'mdns-autoip')
    else:
        raise SystemExit('Usage: sudo .venv/bin/python tools/pi_mdns_autoip_check.py')
