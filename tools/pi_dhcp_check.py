"""Manual root-only DHCP acceptance in isolated namespaces; never a pytest test.

Run from the Pi checkout: sudo python3 tools/pi_dhcp_check.py
Artifacts stay under ignored tmp/. No host interface is moved or reconfigured.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def command(args,**kwargs):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=kwargs.pop('timeout',20),**kwargs)
    if result.returncode:raise RuntimeError(f'{args[0:4]} failed: {result.stderr.strip()}')
    return result.stdout.strip()


def dhcp_record(frame,stamp):
    """Decode only unfragmented Ethernet/IPv4/UDP BOOTP packets from our lab."""
    if len(frame)<42 or frame[12:14]!=b'\x08\x00':return None
    ip=frame[14:];header=(ip[0]&15)*4
    if ip[0]>>4!=4 or header<20 or len(ip)<header+8 or ip[9]!=17:return None
    if struct.unpack('!H',ip[6:8])[0]&0x3fff:return None
    udp=ip[header:]
    source,dest,length=struct.unpack('!HHH',udp[:6])
    if {source,dest}!={67,68} or length<248 or length>len(udp):return None
    bootp=udp[8:length]
    if len(bootp)<240 or bootp[236:240]!=b'\x63\x82\x53\x63':return None
    options={};pos=240
    while pos<len(bootp):
        key=bootp[pos];pos+=1
        if key==255:break
        if key==0:continue
        if pos>=len(bootp):return None
        size=bootp[pos];pos+=1
        if pos+size>len(bootp):return None
        options[key]=bootp[pos:pos+size];pos+=size
    result={'time':stamp,'message_type':int.from_bytes(options.get(53,b''),'big'),
            'ciaddr':socket.inet_ntoa(bootp[12:16]),'yiaddr':socket.inet_ntoa(bootp[16:20]),
            'parameter_request_list':list(options.get(55,b''))}
    for key,name in ((1,'mask'),(3,'gateway'),(6,'dns'),(54,'server')):
        value=options.get(key,b'')
        if value and len(value)%4==0:result[name]=[socket.inet_ntoa(value[i:i+4]) for i in range(0,len(value),4)]
    if len(options.get(51,b''))==4:result['lease_seconds']=struct.unpack('!I',options[51])[0]
    return result


def capture(base):
    with socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(3)) as sock, (base/'traffic.pcap').open('wb') as pcap, (base/'packets.jsonl').open('w') as records:
        sock.bind(('srv0',0));sock.settimeout(1)
        pcap.write(struct.pack('<IHHIIII',0xa1b2c3d4,2,4,0,0,65535,1));pcap.flush()
        (base/'capture.ready').touch()
        while True:
            try:frame=sock.recv(65535)
            except socket.timeout:continue
            stamp=time.time();sec=int(stamp)
            pcap.write(struct.pack('<IIII',sec,int((stamp-sec)*1e6),len(frame),len(frame))+frame);pcap.flush()
            item=dhcp_record(frame,stamp)
            if item:records.write(json.dumps(item)+'\n');records.flush()


def daemon(base):
    def interrupted(*args):raise KeyboardInterrupt
    for sig in (signal.SIGTERM,signal.SIGHUP):signal.signal(sig,interrupted)
    command(['mount','--make-rprivate','/'])
    private_run=base/'run-root'
    for relative in ('NetworkManager','dbus','netplan','systemd/network','udev/rules.d'):
        (private_run/relative).mkdir(parents=True,exist_ok=True)
    command(['mount','--bind',private_run,'/run'])
    mappings={'etc':'/etc/NetworkManager','run':'/run/NetworkManager','lib':'/var/lib/NetworkManager','dbus':'/run/dbus'}
    for name,target in mappings.items():command(['mount','--bind',base/name,target])
    if Path('/usr/lib/NetworkManager/conf.d').is_dir():
        command(['mount','--bind',base/'vendor-conf','/usr/lib/NetworkManager/conf.d'])
    # Debian's patched keyfile plugin invokes Netplan generation on writes.
    # Hide host Netplan input AND generated output, not just NM's own files.
    for index,target in enumerate(('/etc/netplan','/run/netplan','/lib/netplan','/run/systemd/network')):
        if Path(target).is_dir():
            private=base/('netplan-'+str(index));private.mkdir(exist_ok=True)
            command(['mount','--bind',private,target])
    resolver=Path('/etc/resolv.conf').resolve()
    resolver.parent.mkdir(parents=True,exist_ok=True);resolver.touch(exist_ok=True)
    command(['mount','--bind',base/'resolv.conf',resolver])
    command(['mount','-t','sysfs','-o','ro','sysfs','/sys'])
    command(['hostname','civi-dhcp-lab'])
    children=[]
    try:
        with (base/'dbus.log').open('w') as log:
            children.append(subprocess.Popen(['dbus-daemon','--nofork','--config-file='+str(base/'dbus.conf')],stdout=log,stderr=log))
        for _ in range(30):
            if Path('/run/dbus/system_bus_socket').exists():break
            time.sleep(.1)
        with (base/'nm.log').open('w') as log:
            children.append(subprocess.Popen(['NetworkManager','--debug','--no-daemon','--config=/etc/NetworkManager/NetworkManager.conf','--pid-file=/run/NetworkManager/lab.pid'],stdout=log,stderr=log))
        (base/'daemon.pid').write_text(str(os.getpid()))
        while all(p.poll() is None for p in children):time.sleep(.5)
        raise RuntimeError('Private D-Bus / NetworkManager exited; inspect lab logs')
    finally:
        for child in reversed(children):
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait()


def run_lab(check=None,kind='dhcp'):
    if sys.platform!='linux' or os.geteuid()!=0:raise SystemExit('Run manually as root on the Pi/Linux target')
    from civi.pi.network import NetworkManager as NM
    from civi.pi.transactions import Transactions,Checkpoints
    from types import SimpleNamespace
    os.chdir(ROOT)
    base=ROOT/'tmp'/(kind+'-lab-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    base.mkdir(parents=True,mode=0o700)
    suffix=uuid.uuid4().hex[:6];client='civi-dhcpc-'+suffix;server='civi-dhcps-'+suffix
    children=[];namespaces=[];dhcp=None;checks={}
    host=NM().snapshot('eth0');host_pid=command(['systemctl','show','--property=MainPID','--value','NetworkManager'])
    host_resolver=hashlib.sha256(Path('/etc/resolv.conf').read_bytes()).hexdigest()
    def netplan_hashes():
        return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/etc/netplan').glob('*.yaml')}
    host_netplan=netplan_hashes()
    (base/'baseline.json').write_text(json.dumps({'network':host,'nm_pid':host_pid,'resolver_sha256':host_resolver,'netplan_sha256':host_netplan},indent=2))
    def log(message):
        line=time.strftime('%H:%M:%S')+' '+message
        print(line,flush=True)
        with (base/'steps.log').open('a') as output:output.write(line+'\n')
    def spawn(args,name):
        with (base/name).open('a') as output:
            p=subprocess.Popen(list(map(str,args)),stdout=output,stderr=output,start_new_session=True)
        children.append(p);return p
    def stop(p):
        if p is not None and p.poll() is None:
            os.killpg(p.pid,signal.SIGTERM)
            try:p.wait(timeout=6)
            except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    def wait(predicate,seconds,label):
        end=time.monotonic()+seconds;notice=time.monotonic()+25
        while time.monotonic()<end:
            value=predicate()
            if value:return value
            if time.monotonic()>notice:log('Waiting: '+label);notice=time.monotonic()+25
            time.sleep(1)
        raise TimeoutError(label)
    def packets():
        path=base/'packets.jsonl'
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []
    def start_server(gateway,dns):
        config=base/'dnsmasq.conf'
        config.write_text(f'interface=srv0\nbind-interfaces\nno-resolv\nno-hosts\nuser=root\n'
            f'dhcp-authoritative\ndhcp-range=192.0.2.10,192.0.2.20,255.255.255.0,2m\n'
            f'dhcp-host=02:c1:71:00:00:02,192.0.2.10\ndhcp-option=option:router,{gateway}\n'
            f'dhcp-option=option:dns-server,{dns}\naddress=/civi-dhcp.test/192.0.2.100\n'
            f'log-dhcp\nlog-facility=-\ndhcp-leasefile={base}/leases\npid-file={base}/dnsmasq.pid\n')
        return spawn(['ip','netns','exec',server,'dnsmasq','--keep-in-foreground','--conf-file='+str(config)],'dnsmasq.log')
    def interrupted(*args):raise KeyboardInterrupt
    for sig in (signal.SIGTERM,signal.SIGHUP):signal.signal(sig,interrupted)
    try:
        for name in (client,server):command(['ip','netns','add',name]);namespaces.append(name)
        command(['ip','-n',server,'link','add','srv0','type','veth','peer','name','lxi0','netns',client])
        for namespace,device in ((server,'srv0'),(client,'lxi0')):
            command(['ip','-n',namespace,'link','set','lo','up'])
            command(['ip','-n',namespace,'link','set',device,'up'])
        command(['ip','-n',client,'link','set','lxi0','address','02:c1:71:00:00:02'])
        for address in ('192.0.2.1','192.0.2.53','192.0.2.54','192.0.2.254'):
            command(['ip','-n',server,'addr','add',address+'/24','dev','srv0'])
        for name in ('etc','etc/system-connections','etc/conf.d','run','run/conf.d','lib','dbus','vendor-conf'):
            (base/name).mkdir(parents=True,exist_ok=True)
        (base/'resolv.conf').write_text('')
        (base/'etc/NetworkManager.conf').write_text('[main]\nplugins=keyfile\ndhcp=internal\ndns=default\nrc-manager=file\nhostname-mode=none\nno-auto-default=*\n[device-lab]\nmatch-device=interface-name:lxi0\nmanaged=1\n[logging]\nlevel=DEBUG\ndomains=DHCP4,IP4,CORE,DEVICE\n')
        (base/'dbus.conf').write_text('<busconfig><type>system</type><listen>unix:path=/run/dbus/system_bus_socket</listen><auth>EXTERNAL</auth><policy context="default"><allow user="root"/><allow own="*"/><allow send_destination="*"/><allow receive_sender="*"/></policy></busconfig>')
        spawn(['ip','netns','exec',server,sys.executable,__file__,'--capture',base],'capture.log')
        wait(lambda:(base/'capture.ready').exists(),10,'packet capture startup')
        wrapper=spawn(['ip','netns','exec',client,'unshare','--mount','--uts',sys.executable,__file__,'--daemon',base],'wrapper.log')
        wait(lambda:(base/'daemon.pid').exists(),10,'private NetworkManager wrapper startup')
        pid=int((base/'daemon.pid').read_text())
        prefix=['nsenter','--target',str(pid),'--mount','--net','--uts','--']
        def scoped(args,**kwargs):
            return subprocess.run(prefix+list(args),**kwargs)
        def nm(*args):return command(prefix+['nmcli','--colors','no',*args])
        def ready():
            result=scoped(['nmcli','-g','RUNNING','general'],capture_output=True,text=True,timeout=3)
            return result.returncode==0 and result.stdout.strip()=='running'
        wait(ready,15,'private NetworkManager D-Bus startup')
        visible=set(json.loads(command(prefix+['ip','-j','link','show']))[i]['ifname'] for i in range(2))
        assert visible=={'lo','lxi0'},visible
        nm('device','set','lxi0','managed','yes')
        nm('connection','add','type','ethernet','ifname','lxi0','con-name','CIVI DHCP lab',
           'ipv4.method','manual','ipv4.addresses','192.0.2.77/24','ipv6.method','disabled')
        selected=nm('-g','connection.uuid','connection','show','CIVI DHCP lab')
        nm('--wait','15','connection','up','uuid',selected)
        manager=NM(scoped,selected_uuid=selected)
        tx=Transactions('lxi0',manager=manager,checkpoints=Checkpoints(scoped),
                        ping=SimpleNamespace(),mdns=SimpleNamespace())
        if check is not None:
            check(base=base,manager=manager,tx=tx,nm=nm,scoped=scoped,prefix=prefix,
                  server=server,selected=selected,spawn=spawn,stop=stop,wait=wait,log=log)
            return
        result=tx.apply({'mode':'automatic','dns':[]},180)
        tx.confirm(result['pending']['token'])
        log('CIVI automatic-mode apply/confirm succeeded in private NetworkManager')
        def snapshot():return manager.snapshot('lxi0')
        wait(lambda:any(a.startswith('169.254.') for a in snapshot()['active_ipv4'].splitlines()),75,'AutoIP without DHCP')
        checks['initial_autoip']=snapshot();log('PASS: initial AutoIP, no DHCP server')
        dhcp=start_server('192.0.2.1','192.0.2.53')
        wait(lambda:'192.0.2.10/24' in snapshot()['active_ipv4'].splitlines(),100,'first DHCP lease')
        first=wait(lambda:next((p for p in reversed(packets()) if p['message_type']==5),None),8,'first DHCP ACK capture')
        s=snapshot();assert s['active_gateway']=='192.0.2.1' and s['active_dns']=='192.0.2.53',s
        requests=[p for p in packets() if p['message_type'] in (1,3)]
        assert any({1,3,6}.issubset(p['parameter_request_list']) for p in requests)
        checks['first_lease']={'snapshot':s,'ack':first};log('PASS: DHCP lease, mask/gateway/DNS and request options 1/3/6')
        stop(dhcp);dhcp=start_server('192.0.2.254','192.0.2.54');changed=time.time()
        def renewed():
            s=snapshot()
            return s if s['active_gateway']=='192.0.2.254' and s['active_dns']=='192.0.2.54' else None
        s=wait(renewed,100,'lease renewal with changed gateway/DNS')
        renewal=next(p for p in reversed(packets()) if p['message_type']==5 and p['time']>=changed)
        assert any(p['message_type']==3 and p['time']>=changed and p['ciaddr']=='192.0.2.10' for p in packets())
        checks['renewal']={'snapshot':s,'ack':renewal};log('PASS: actual DHCP renewal accepted changed gateway/DNS')
        stop(dhcp);dhcp=None;log('DHCP server stopped; waiting for lease expiry')
        s=wait(lambda:snapshot() if '192.0.2.10/24' not in snapshot()['active_ipv4'].splitlines() else None,
               int(renewal['lease_seconds'])+35,'expired DHCP address removal')
        assert s['active_gateway']!='192.0.2.254'
        checks['expired']=s;log('PASS: expired DHCP address and gateway removed')
        wait(lambda:any(a.startswith('169.254.') for a in snapshot()['active_ipv4'].splitlines()),75,'AutoIP after expiry')
        checks['expiry_autoip']=snapshot();log('PASS: AutoIP usable after DHCP loss')
        dhcp=start_server('192.0.2.254','192.0.2.54')
        wait(lambda:'192.0.2.10/24' in snapshot()['active_ipv4'].splitlines(),100,'DHCP return after AutoIP')
        checks['returned']=snapshot();log('PASS: DHCP address reacquired after server return')
        (base/'results.json').write_text(json.dumps(checks,indent=2))
        log('PASS: isolated DHCP acceptance completed')
    finally:
        for child in reversed(children):stop(child)
        for name in reversed(namespaces):
            # Descendants may still be exiting after their wrapper was reaped.
            deadline=time.monotonic()+8
            while True:
                remaining=command(['ip','netns','pids',name])
                if not remaining or time.monotonic()>=deadline:break
                time.sleep(.2)
            if remaining:raise RuntimeError('Lab processes remain in '+name+'; cleanup requires inspection')
            command(['ip','netns','del',name])
        after=NM().snapshot('eth0')
        unchanged=host['uuid']==after['uuid'] and host['profile']==after['profile'] and host['active_ipv4']==after['active_ipv4']
        unchanged=unchanged and host_pid==command(['systemctl','show','--property=MainPID','--value','NetworkManager'])
        unchanged=unchanged and host_resolver==hashlib.sha256(Path('/etc/resolv.conf').read_bytes()).hexdigest()
        unchanged=unchanged and host_netplan==netplan_hashes()
        (base/'cleanup.json').write_text(json.dumps({'host_network_unchanged':unchanged,'namespaces_removed':namespaces},indent=2))
        log('Host network unchanged: '+str(unchanged)+' | artifacts: '+str(base))
        if not unchanged:raise RuntimeError('Host baseline differs; inspect locally')


if __name__=='__main__':
    try:
        if len(sys.argv)==3 and sys.argv[1]=='--capture':capture(Path(sys.argv[2]))
        elif len(sys.argv)==3 and sys.argv[1]=='--daemon':daemon(Path(sys.argv[2]))
        elif len(sys.argv)==1:run_lab()
        else:raise SystemExit('Usage: sudo python3 tools/pi_dhcp_check.py')
    except KeyboardInterrupt:raise SystemExit('Interrupted; cleanup attempted')
