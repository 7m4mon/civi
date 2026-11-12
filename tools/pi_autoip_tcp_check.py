"""Root-only AutoIP reply-routing acceptance in isolated namespaces."""
import json
from pathlib import Path
import signal
import socket
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from tools.pi_dhcp_check import run_lab,command


def daemon(base):
    from civi.pi.linklocal import LinkLocalRoutes
    router=LinkLocalRoutes('lxi0',SimpleNamespace(lock=threading.RLock()),directory=base/'routing')
    def stop(*args):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop);signal.signal(signal.SIGHUP,stop)
    try:
        router.start()
        while True:
            (base/'router-state.json').write_text(json.dumps(router.snapshot()));time.sleep(.1)
    except KeyboardInterrupt:pass
    finally:router.close()


def server(base):
    with socket.socket() as sock:
        sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);sock.bind(('0.0.0.0',15525));sock.listen()
        (base/'tcp.ready').touch()
        while True:
            connection,_=sock.accept()
            with connection:connection.sendall(b'CIVI route fixture\n')


def probe(address):
    try:
        with socket.create_connection((address,15525),2) as sock:print(sock.recv(1024).decode().strip())
    except OSError as error:print(type(error).__name__);raise SystemExit(2)


def scenario(*,base,manager,tx,nm,scoped,prefix,server,selected,spawn,stop,wait,log):
    from civi.pi.linklocal import TABLE,PRIORITY
    applied=tx.apply({'mode':'automatic','dns':[]},180);tx.confirm(applied['pending']['token'])
    def address():
        s=manager.snapshot('lxi0')
        return next((a.split('/')[0] for a in s['active_ipv4'].splitlines() if a.startswith('169.254.')),None)
    ll=wait(address,75,'AutoIP address')
    command(prefix+['ip','link','add','admin0','type','dummy'])
    command(prefix+['ip','addr','add','198.51.100.2/24','dev','admin0'])
    command(prefix+['ip','link','set','admin0','up'])
    command(prefix+['ip','route','add','default','via','198.51.100.1','dev','admin0'])
    command(['ip','-n',server,'route','add',ll+'/32','dev','srv0','src','192.0.2.1'])
    defaults=command(prefix+['ip','-j','route','show','default'])
    spawn(prefix+[sys.executable,__file__,'--server',base],'tcp.log')
    wait(lambda:(base/'tcp.ready').exists(),8,'TCP listener')
    def client():return subprocess.run(['ip','netns','exec',server,sys.executable,__file__,'--probe',ll],capture_output=True,text=True,timeout=5)
    before=client();assert before.returncode==2,before.stdout
    result={'address':ll,'before':{'returncode':before.returncode,'output':before.stdout.strip(),
        'route':command(prefix+['ip','route','get','192.0.2.1','from',ll])}}
    log('PASS: reproduced failed AutoIP TCP reply with separate management default route')
    agent=spawn(prefix+[sys.executable,__file__,'--routing',base],'routing.log')
    def routing_ready():
        return 'dev lxi0' in command(prefix+['ip','route','get','192.0.2.1','from',ll])
    wait(routing_ready,10,'source-specific route')
    after=client();assert after.returncode==0,after.stdout+after.stderr
    result['after']={'output':after.stdout.strip(),'route':command(prefix+['ip','route','get','192.0.2.1','from',ll])}
    assert command(prefix+['ip','-j','route','show','default'])==defaults
    log('PASS: routable-address peer TCP succeeds; management default route unchanged')
    agent.kill();agent.wait()
    agent=spawn(prefix+[sys.executable,__file__,'--routing',base],'routing-restart.log')
    wait(lambda:client().returncode==0,8,'restart after abrupt monitor exit')
    time.sleep(1)
    assert agent.poll() is None,(base/'routing-restart.log').read_text()
    result['restart']=True;log('PASS: stale ownership recovered after abrupt monitor exit')
    applied=tx.apply({'mode':'static','address':'192.0.2.77','prefix':24,'gateway':'','dns':[]},180);tx.confirm(applied['pending']['token'])
    def clean():
        rules=json.loads(command(prefix+['ip','-j','-4','rule','show']))
        return not any(r.get('priority')==PRIORITY or str(r.get('table'))==str(TABLE) for r in rules)
    wait(clean,12,'AutoIP rule removal after static configuration')
    routes=json.loads(command(prefix+['ip','-j','-4','route','show','table','all']))
    assert not any(str(r.get('table'))==str(TABLE) for r in routes)
    assert command(prefix+['ip','-j','route','show','default'])==defaults
    stop(agent);result['cleanup']=True
    (base/'results.json').write_text(json.dumps(result,indent=2))
    log('PASS: owned AutoIP routes removed after static configuration; other routes retained')


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--routing':daemon(Path(sys.argv[2]))
    elif len(sys.argv)==3 and sys.argv[1]=='--server':server(Path(sys.argv[2]))
    elif len(sys.argv)==3 and sys.argv[1]=='--probe':probe(sys.argv[2])
    elif len(sys.argv)==1:run_lab(scenario,'autoip-tcp')
    else:raise SystemExit('Run manually: sudo python3 tools/pi_autoip_tcp_check.py')
