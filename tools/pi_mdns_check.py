"""Root-only real Avahi hostname acceptance on an isolated virtual Ethernet."""
import asyncio
import json
import os
from pathlib import Path
import signal
import socket
import socketserver
import struct
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.pi_dhcp_check import command,run_lab

DESIRED='civi-mdns-lab'
AVAHI=['avahi-daemon','--debug','--no-drop-root','--no-chroot','--no-rlimits','--no-proc-title']


def config_text(host,interface):
    return f'[server]\nhost-name={host}\ndomain-name=local\nuse-ipv4=yes\nuse-ipv6=no\nallow-interfaces={interface}\nenable-dbus=yes\n[wide-area]\nenable-wide-area=no\n[publish]\npublish-workstation=no\npublish-hinfo=no\n[reflector]\nenable-reflector=no\n'


def private_avahi(base,peer=False):
    command(['mount','--make-rprivate','/'])
    empty=base/'avahi-etc';(empty/'services').mkdir(parents=True,exist_ok=True)
    command(['mount','--bind',empty,'/etc/avahi'])
    if not peer:os.execvp(AVAHI[0],AVAHI+['--file='+str(base/'client.conf')])
    runtime=base/'peer-run';(runtime/'dbus').mkdir(parents=True,exist_ok=True)
    command(['mount','--bind',runtime,'/run'])
    command(['mount','-t','sysfs','-o','ro','sysfs','/sys'])
    children=[]
    def interrupted(*args):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,interrupted)
    try:
        with (base/'peer-dbus.log').open('w') as output:
            children.append(subprocess.Popen(['dbus-daemon','--nofork','--config-file='+str(base/'dbus.conf')],stdout=output,stderr=output))
        for _ in range(50):
            if Path('/run/dbus/system_bus_socket').exists():break
            time.sleep(.1)
        with (base/'peer-avahi.log').open('a') as output:
            children.append(subprocess.Popen(AVAHI+['--file='+str(base/'peer.conf')],stdout=output,stderr=output))
        (base/'peer.pid').write_text(str(os.getpid()))
        while all(p.poll() is None for p in children):time.sleep(.2)
        raise RuntimeError('Private peer daemon exited')
    except KeyboardInterrupt:pass
    finally:
        for child in reversed(children):
            if child.poll() is None:child.terminate()
        for child in children:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:child.kill();child.wait()


def claim_host(fqdn):
    name=b''.join(bytes([len(part)])+part.encode('ascii') for part in fqdn.rstrip('.').split('.'))+b'\x00'
    packet=struct.pack('!6H',0,0x8400,0,1,0,0)+name+struct.pack('!HHIH',1,0x8001,120,4)+socket.inet_aton('192.0.2.254')
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        sock.bind(('0.0.0.0',5353))
        sock.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_IF,socket.inet_aton('192.0.2.1'))
        sock.setsockopt(socket.IPPROTO_IP,socket.IP_MULTICAST_TTL,255)
        while True:sock.sendto(packet,('224.0.0.251',5353));time.sleep(.25)


async def phase(base,mode):
    from aiohttp import ClientSession,web
    from dbus_next.aio import MessageBus
    from civi.network import Discovery
    from civi.server import make_web
    from civi.identification import identity
    from civi.pi.transactions import Transactions
    from civi.pi.broker import dispatch
    from civi.discovery_state import load_names
    config={'manufacturer':'CIVI test','serial_number':'MDNS-LAB','description':'CIVI hostname acceptance',
            'bind':'0.0.0.0','web_port':18843,'scpi_port':5025,'discovery':True,
            'network_settings_file':str(base/'.civi-network.json'),
            'pi_network':{'enabled':True,'socket':str(base/'helper.sock')}}
    tx=Transactions('lxi0',ping=SimpleNamespace(),mdns=SimpleNamespace())
    calls=[]
    class Handler(socketserver.StreamRequestHandler):
        def handle(self):
            try:
                data=json.loads(self.rfile.readline(2048))
                if data=={'op':'mdns','enabled':True}:result={'enabled':True}
                elif set(data)=={'op','hostname'} and data['op']=='mdns_hostname':
                    calls.append(data['hostname']);result=dispatch(tx,data)
                else:raise ValueError('Only scoped hostname restore and read-only discovery checks allowed')
                self.wfile.write(json.dumps({'ok':True,'result':result}).encode()+b'\n')
            except Exception as error:self.wfile.write(json.dumps({'ok':False,'error':str(error)}).encode()+b'\n')
    path=Path(config['pi_network']['socket']);path.unlink(missing_ok=True)
    helper=socketserver.ThreadingUnixStreamServer(str(path),Handler)
    thread=threading.Thread(target=helper.serve_forever,daemon=True);thread.start()
    discovery=Discovery();runner=None;peer_bus=None;claimant=None
    prior=load_names(config,DESIRED,config['description'])
    try:
        await discovery.refresh(config,identity(SimpleNamespace(config=config,identified_model='Mock')))
        if mode=='initial':assert discovery.hostname!=DESIRED+'.local.',discovery.hostname
        elif mode in ('reuse','daemon-restart'):
            assert prior and discovery.hostname==prior['hostname']+'.local.',(prior,discovery.hostname)
        elif mode=='saved-collision':
            assert discovery.hostname==DESIRED+'.local.',(calls,discovery.hostname)
            assert calls==[prior['hostname'],DESIRED],calls
        before=discovery.hostname
        errors=[]
        if mode=='live':
            peer_pid=int((base/'peer.pid').read_text())
            claimant=subprocess.Popen(['nsenter','--target',str(peer_pid),'--mount','--net','--uts','--',sys.executable,__file__,'--claim-host',before])
            for _ in range(100):
                await asyncio.sleep(.2)
                try:await discovery.refresh(config,identity(SimpleNamespace(config=config,identified_model='Mock')))
                except Exception as error:errors.append(str(error));continue
                if discovery.hostname and discovery.hostname!=before:break
            else:raise RuntimeError('Live hostname conflict did not change acquired name')
            claimant.terminate();claimant.wait(timeout=5);claimant=None
        if mode=='daemon-restart':
            (base/'restart-client.request').touch()
            for _ in range(150):
                await asyncio.sleep(.2)
                try:
                    await discovery.refresh(config,identity(SimpleNamespace(config=config,identified_model='Mock')))
                    if (base/'restart-client.done').exists() and calls and discovery.hostname==before:break
                except Exception as error:errors.append(str(error))
            else:raise RuntimeError('Discovery did not recover and restore its acquired name after daemon restart')
        saved=load_names(config,DESIRED,config['description'])
        assert saved['hostname']==discovery.hostname[:-7] and saved['desired_hostname']==DESIRED
        assert socket.gethostname()==DESIRED,'Acquired name must not overwrite the OS desired name'
        # Resolve from the independently running peer daemon, across the veth.
        peer_bus=await MessageBus(bus_address='unix:path='+str(base/'peer-run/dbus/system_bus_socket')).connect()
        intro=await peer_bus.introspect('org.freedesktop.Avahi','/')
        peer=peer_bus.get_proxy_object('org.freedesktop.Avahi','/',intro).get_interface('org.freedesktop.Avahi.Server')
        resolved=[]
        for service,port in discovery.avahi.service_ports(config):
            for _ in range(30):
                response=await asyncio.wait_for(peer.call_resolve_service(-1,0,discovery.description,service,'local',0,0),15)
                if response[5]+'.'==discovery.hostname and response[7]=='192.0.2.77' and response[8]==port:break
                await asyncio.sleep(.5)
            else:raise AssertionError(('Peer did not converge to updated SRV/A records',discovery.hostname,response))
            resolved.append({'service':service,'host':response[5],'address':response[7],'port':response[8]})
        stub=SimpleNamespace(config=config,identified_model='Mock',backend=SimpleNamespace(state='connected'))
        runner=web.AppRunner(make_web(stub,'fixture-only-password',discovery=discovery));await runner.setup()
        await web.TCPSite(runner,'127.0.0.1',18843).start()
        async with ClientSession() as http:
            for url in ('/lxi','/network'):
                async with http.get('http://127.0.0.1:18843'+url) as response:
                    html=await response.text();assert response.status==200
                    assert '<dt>Advertised mDNS hostname</dt><dd>'+discovery.hostname+'</dd>' in html
                    (base/(mode+url.replace('/','-')+'.html')).write_text(html)
        result={'mode':mode,'before':before,'hostname':discovery.hostname,'saved':saved,'helper_calls':calls,'resolved':resolved,'transient_errors':errors}
        (base/(mode+'.json')).write_text(json.dumps(result,indent=2))
        print('PASS:',mode,discovery.hostname,'helper calls:',calls,flush=True)
    finally:
        if claimant and claimant.poll() is None:claimant.terminate();claimant.wait(timeout=5)
        if runner:await runner.cleanup()
        if peer_bus:
            peer_bus.disconnect();await peer_bus.wait_for_disconnect()
        await discovery.close()
        helper.shutdown();helper.server_close();thread.join(timeout=2);path.unlink(missing_ok=True)


def scenario(*,base,manager,tx,nm,scoped,prefix,server,selected,spawn,stop,wait,log):
    host_name=socket.gethostname()
    host_pid=command(['systemctl','show','--property=MainPID','--value','avahi-daemon'])
    host_avahi=command(['busctl','--system','call','org.freedesktop.Avahi','/','org.freedesktop.Avahi.Server','GetHostNameFqdn'])
    (base/'client.conf').write_text(config_text(DESIRED,'lxi0'))
    (base/'peer.conf').write_text(config_text(DESIRED,'srv0'))
    command(prefix+['hostname',DESIRED])
    peer_process=spawn(['ip','netns','exec',server,'unshare','--mount','--uts',sys.executable,__file__,'--peer',base],'peer-wrapper.log')
    wait(lambda:(base/'peer.pid').exists(),10,'private peer startup')
    peer_prefix=['nsenter','--target',(base/'peer.pid').read_text(),'--mount','--net','--uts','--']
    def ready(scope):
        r=subprocess.run(scope+['busctl','--system','call','org.freedesktop.Avahi','/','org.freedesktop.Avahi.Server','GetState'],capture_output=True,text=True,timeout=3)
        return r.returncode==0 and r.stdout.strip()=='i 2'
    wait(lambda:ready(peer_prefix),12,'peer desired hostname established')
    def client_start():
        process=spawn(prefix+['unshare','--mount',sys.executable,__file__,'--client',base],'client-avahi.log')
        wait(lambda:ready(prefix),15,'client Avahi probing')
        return process
    client_process=client_start()
    python=ROOT/'.venv/bin/python'
    def run_phase(mode):
        process=spawn(prefix+[python,__file__,'--phase',base,mode],mode+'.log')
        deadline=time.monotonic()+100
        while process.poll() is None:
            if (base/'restart-client.request').exists() and not (base/'restart-client.done').exists():
                stop(client_process)
                restarted=client_start();replacement.append(restarted)
                (base/'restart-client.done').touch()
            if time.monotonic()>deadline:raise TimeoutError(mode+' worker; inspect artifacts')
            time.sleep(.3)
        if process.returncode:raise RuntimeError(mode+' failed: '+(base/(mode+'.log')).read_text()[-3000:])
        log((base/(mode+'.log')).read_text().strip())
        return json.loads((base/(mode+'.json')).read_text())
    replacement=[]
    results={}
    try:
        results['initial']=run_phase('initial')
        results['reuse']=run_phase('reuse')
        results['live']=run_phase('live')
        command(peer_prefix+['busctl','--system','call','org.freedesktop.Avahi','/','org.freedesktop.Avahi.Server','SetHostName','s','civi-peer-free'])
        wait(lambda:ready(peer_prefix),12,'peer releases desired name')
        results['daemon_restart']=run_phase('daemon-restart')
        client_process=replacement[-1]
        results['post_restart_reuse']=run_phase('reuse')
        saved=results['daemon_restart']['saved']['hostname']
        stop(client_process)
        command(peer_prefix+['busctl','--system','call','org.freedesktop.Avahi','/','org.freedesktop.Avahi.Server','SetHostName','s',saved])
        wait(lambda:ready(peer_prefix),12,'peer occupies saved acquired name')
        client_process=client_start()
        results['saved_collision']=run_phase('saved-collision')
        (base/'results.json').write_text(json.dumps(results,indent=2))
    finally:
        stop(client_process);stop(peer_process)
        unchanged=host_name==socket.gethostname() and host_pid==command(['systemctl','show','--property=MainPID','--value','avahi-daemon'])
        unchanged=unchanged and host_avahi==command(['busctl','--system','call','org.freedesktop.Avahi','/','org.freedesktop.Avahi.Server','GetHostNameFqdn'])
        (base/'avahi-cleanup.json').write_text(json.dumps({'production_hostname_and_avahi_unchanged':unchanged},indent=2))
        log('Production hostname and Avahi unchanged: '+str(unchanged))
        if not unchanged:raise RuntimeError('Production Avahi baseline differs')


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--peer':private_avahi(Path(sys.argv[2]),True)
    elif len(sys.argv)==3 and sys.argv[1]=='--client':private_avahi(Path(sys.argv[2]))
    elif len(sys.argv)==3 and sys.argv[1]=='--claim-host':claim_host(sys.argv[2])
    elif len(sys.argv)==4 and sys.argv[1]=='--phase':asyncio.run(phase(Path(sys.argv[2]),sys.argv[3]))
    elif len(sys.argv)==1:run_lab(scenario,'mdns')
    else:raise SystemExit('Usage: sudo python3 tools/pi_mdns_check.py')
