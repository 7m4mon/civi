"""Manual root-only duplicate IPv4 acceptance in an isolated Pi network."""
import json
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import time
import signal

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.pi_dhcp_check import command,run_lab


def arp_record(frame):
    if len(frame)<42 or frame[12:14]!=b'\x08\x06':return None
    arp=frame[14:42]
    if arp[:6]!=b'\x00\x01\x08\x00\x06\x04':return None
    return {'op':int.from_bytes(arp[6:8],'big'),'mac':arp[8:14].hex(':'),
            'sender':socket.inet_ntoa(arp[14:18]),'target':socket.inet_ntoa(arp[24:28])}


def capture(base):
    with socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(3)) as sock, (base/'arp.jsonl').open('w') as records:
        sock.bind(('srv0',0));sock.settimeout(1)
        (base/'arp.ready').touch()
        while True:
            try:frame=sock.recv(65535)
            except socket.timeout:continue
            record=arp_record(frame)
            if record:records.write(json.dumps({'time':time.time(),**record})+'\n');records.flush()


def observe():
    from civi.indicator import PiLanReader
    path=Path(sys.argv[2]) if len(sys.argv)>2 else None
    callback=(lambda:json.loads(path.read_text())) if path else None
    print(json.dumps(PiLanReader('lxi0',conflict_reader=callback)()))


def guard_daemon(base):
    import threading
    from types import SimpleNamespace
    from civi.pi.conflict import ConflictGuard
    from civi.pi.network import NetworkManager
    guard=ConflictGuard('lxi0',SimpleNamespace(lock=threading.RLock(),manager=NetworkManager()))
    def interrupted(*args):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,interrupted)
    try:
        guard.start()
        while True:
            temporary=base/'guard-state.tmp'
            temporary.write_text(json.dumps(guard.snapshot()))
            temporary.replace(base/'guard-state.json');time.sleep(.1)
    except KeyboardInterrupt:pass
    finally:guard.close()


def scenario(*,base,manager,tx,nm,scoped,prefix,server,selected,spawn,stop,wait,log):
    from civi.indicator import LanIndicator
    indicator=LanIndicator('lxi0');events=[];results={}
    guard_process=None
    spawn(['ip','netns','exec',server,sys.executable,__file__,'--capture',base],'arp-capture.log')
    wait(lambda:(base/'arp.ready').exists(),8,'ARP capture')
    def sample():
        args=[sys.executable,__file__,'--observe']
        if guard_process is not None:args.append(str(base/'guard-state.json'))
        obs=json.loads(command(prefix+args))
        indicator.update(obs);status=indicator.snapshot()
        events.append({'time':time.time(),'observation':obs,'status':status})
        with (base/'observations.jsonl').open('a') as output:output.write(json.dumps(events[-1])+'\n')
        return obs,status
    def addresses():
        return [a['local'] for nic in json.loads(command(prefix+['ip','-j','-4','address','show','dev','lxi0'])) for a in nic.get('addr_info',[])]
    def peer_add(ip):command(['ip','-n',server,'addr','add',ip+'/24','dev','srv0'])
    def peer_del(ip):command(['ip','-n',server,'addr','del',ip+'/24','dev','srv0'])
    def activate():
        return scoped(['nmcli','--wait','15','connection','up','uuid',selected],capture_output=True,text=True,timeout=20)
    def save(): (base/'results.json').write_text(json.dumps(results,indent=2))
    baseline,status=sample()
    assert baseline['uuid']==selected and baseline['addresses']==['192.0.2.77'],baseline
    assert status['state']=='normal'
    log('Normal static baseline observed')
    nm('connection','modify','uuid',selected,'connection.autoconnect','no')
    results['dad_timeout']=nm('-g','ipv4.dad-timeout','connection','show','uuid',selected)
    # The peer owns the requested address before the client activates it.
    peer_add('192.0.2.88')
    nm('connection','modify','uuid',selected,'ipv4.addresses','192.0.2.88/24')
    activated=activate()
    results['static_activation']={'returncode':activated.returncode,'stderr':activated.stderr,
                                  'observation':sample()[0],'addresses':addresses()}
    save()
    assert activated.returncode!=0 and '192.0.2.88' not in addresses(),results['static_activation']
    obs,status=sample();event=events[-1]
    assert event['status']['state']=='fault'
    results['static_fault']=event;save();log('PASS: pre-existing static duplicate rejected, LAN Fault observed')
    peer_del('192.0.2.88');activated=activate()
    assert activated.returncode==0,activated.stderr
    obs,status=sample()
    assert status['state']=='normal' and '192.0.2.88' in addresses()
    results['static_recovery']={'observation':obs,'status':status};save()
    log('Static address activation recovered after removing peer conflict; indicator state='+status['state'])
    guard_process=spawn(prefix+[sys.executable,__file__,'--guard',base],'guard.log')
    wait(lambda:(base/'guard-state.json').exists(),8,'runtime conflict guard startup')
    # Repeated conflicting claims after activation exercise address defense.
    peer_add('192.0.2.88')
    attacker=spawn(['ip','netns','exec',server,sys.executable,__file__,'--claim','192.0.2.88'],'claims.log')
    try:
        end=time.monotonic()+15
        while time.monotonic()<end:
            sample()
            if '192.0.2.88' not in addresses():break
            time.sleep(.5)
        results['runtime_static']={'addresses':addresses(),'observation':events[-1],'removed':'192.0.2.88' not in addresses()};save()
        wait(lambda:(json.loads((base/'guard-state.json').read_text()).get('fault') or {}).get('disconnected'),8,'verified conflict disconnection')
        sample();results['runtime_static']['observation']=events[-1]
        assert results['runtime_static']['removed'] and events[-1]['status']['state']=='fault'
        assert events[-1]['observation'].get('runtime_conflict',{}).get('disconnected')
        log(('PASS' if results['runtime_static']['removed'] else 'GAP')+': runtime static conflict address removed: '+str(results['runtime_static']['removed']))
    finally:stop(attacker);peer_del('192.0.2.88');stop(guard_process);guard_process=None
    # Return to a clean profile to check DHCP duplicate rejection next.
    nm('connection','modify','uuid',selected,'ipv4.addresses','192.0.2.77/24')
    assert activate().returncode==0
    blocker=spawn(['ip','netns','exec',server,sys.executable,__file__,'--block-link-local'],'link-local-blocker.log')
    applied=tx.apply({'mode':'automatic','dns':[]},180);tx.confirm(applied['pending']['token'])
    try:
        end=time.monotonic()+5
        while time.monotonic()<end:
            assert not any(ip.startswith('169.254.') for ip in addresses()),'Conflicting AutoIP candidate was assigned'
            sample();time.sleep(.3)
        arp=[json.loads(line) for line in (base/'arp.jsonl').read_text().splitlines()]
        assert any(p['sender']=='0.0.0.0' and p['target'].startswith('169.254.') for p in arp)
        results['autoip_rejected']={'observation':events[-1],'probe_seen':True};save()
        log('PASS: occupied AutoIP candidates not assigned')
    finally:stop(blocker)
    wait(lambda:any(ip.startswith('169.254.') for ip in addresses()),75,'AutoIP baseline')
    obs,status=sample();assert status['state']=='normal'
    results['autoip_recovered']={'observation':obs,'status':status};save()
    log('PASS: AutoIP acquired after peer claims stop')
    # Use ARP claims without assigning the lease to the DHCP server's own NIC;
    # otherwise Linux routes unicast DHCP replies back into the server itself.
    lease_attacker=spawn(['ip','netns','exec',server,sys.executable,__file__,'--defend-ip','192.0.2.10'],'lease-claims.log')
    (base/'dnsmasq-conflict.conf').write_text('interface=srv0\nbind-interfaces\nno-resolv\nno-hosts\nuser=root\n'
        'dhcp-authoritative\nno-ping\ndhcp-range=192.0.2.10,192.0.2.20,255.255.255.0,2m\n'
        'dhcp-host=02:c1:71:00:00:02,192.0.2.10\n'
        f'log-dhcp\nlog-facility=-\ndhcp-leasefile={base}/leases\n')
    dhcp=spawn(['ip','netns','exec',server,'dnsmasq','--keep-in-foreground','--conf-file='+str(base/'dnsmasq-conflict.conf')],'dnsmasq-conflict.log')
    try:
        def declined():
            sample()
            packets=[json.loads(line) for line in (base/'packets.jsonl').read_text().splitlines()]
            assert '192.0.2.10' not in addresses(),'Conflicting DHCP address was used'
            return next((p for p in packets if p['message_type']==4),None)
        results['dhcp_decline']=wait(declined,100,'DHCP DECLINE for duplicate offer');save()
        log('PASS: duplicate DHCP lease declined and not assigned')
    finally:stop(dhcp);stop(lease_attacker)
    autoip=next(ip for ip in addresses() if ip.startswith('169.254.'))
    (base/'guard-state.json').unlink(missing_ok=True)
    guard_process=spawn(prefix+[sys.executable,__file__,'--guard',base],'guard-autoip.log')
    wait(lambda:(base/'guard-state.json').exists(),8,'AutoIP runtime guard startup')
    attacker=spawn(['ip','netns','exec',server,sys.executable,__file__,'--claim',autoip],'autoip-claims.log')
    try:
        wait(lambda:autoip not in addresses(),15,'runtime AutoIP duplicate removal')
        wait(lambda:(json.loads((base/'guard-state.json').read_text()).get('fault') or {}).get('disconnected'),8,'verified AutoIP disconnection')
        sample();results['runtime_autoip']=events[-1];save()
        assert events[-1]['status']['state']=='fault'
        log('PASS: active AutoIP conflict disconnected and LAN Fault observed')
    finally:stop(attacker);stop(guard_process);guard_process=None
    results['final_observation']=sample()[0]
    results['acceptance_passed']=results['runtime_static']['removed']
    save()
    if not results['acceptance_passed']:raise RuntimeError('Runtime duplicate IPv4 remains in use; acceptance gap recorded')


def claim(ip):
    """Repeated peer ARP announcements on the isolated server link only."""
    mac=bytes.fromhex(Path('/sys/class/net/srv0/address').read_text().strip().replace(':',''))
    address=socket.inet_aton(ip)
    frame=b'\xff'*6+mac+b'\x08\x06'+struct.pack('!HHBBH',1,0x0800,6,4,1)+mac+address+b'\x00'*6+address
    with socket.socket(socket.AF_PACKET,socket.SOCK_RAW) as sock:
        sock.bind(('srv0',0))
        while True:sock.send(frame);time.sleep(.3)


def block_link_local(address_filter=None):
    mac=bytes.fromhex(Path('/sys/class/net/srv0/address').read_text().strip().replace(':',''))
    with socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(0x0806)) as sock:
        sock.bind(('srv0',0))
        while True:
            frame=sock.recv(65535);record=arp_record(frame)
            if record and record['sender']=='0.0.0.0' and (record['target']==address_filter if address_filter else record['target'].startswith('169.254.')):
                address=socket.inet_aton(record['target'])
                response=b'\xff'*6+mac+b'\x08\x06'+struct.pack('!HHBBH',1,0x0800,6,4,1)+mac+address+b'\x00'*6+address
                sock.send(response)


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--capture':capture(Path(sys.argv[2]))
    elif len(sys.argv)==3 and sys.argv[1]=='--guard':guard_daemon(Path(sys.argv[2]))
    elif len(sys.argv)==3 and sys.argv[1]=='--claim':claim(sys.argv[2])
    elif len(sys.argv)==3 and sys.argv[1]=='--defend-ip':block_link_local(sys.argv[2])
    elif len(sys.argv)>=2 and sys.argv[1]=='--observe':observe()
    elif sys.argv[1:]==['--block-link-local']:block_link_local()
    elif len(sys.argv)==1:run_lab(scenario,'conflict')
    else:raise SystemExit('Usage: sudo python3 tools/pi_conflict_check.py')
