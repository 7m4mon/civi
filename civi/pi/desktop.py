"""Manually start the helper, CIVI and attached display from a desktop icon."""
import argparse
import contextlib
import json
import os
from pathlib import Path
import platform
import shutil
import shlex
import signal
import socket
import subprocess
import sys
import time
import psutil


def desktop_entry(root):
    # Desktop Exec quoting has a string-escape pass before argument unquoting.
    def quote(value):
        text=str(value).replace('%','%%')
        text=''.join('\\'+c if c in '\\"`$' else c for c in text)
        return '"'+text.replace('\\','\\\\')+'"'
    return ('[Desktop Entry]\nType=Application\nName=CIVI\n'
            'Comment=Start CIVI, LAN helper and local panel manually\n'
            'Icon=utilities-terminal\nTerminal=true\nStartupNotify=false\n'
            'Exec=/usr/bin/env bash '+quote(root/'desktop.sh')+'\n')


def install(root):
    desktop=Path(subprocess.check_output(['xdg-user-dir','DESKTOP'],text=True).strip())
    if not desktop.is_absolute() or desktop==Path.home():raise RuntimeError('No separate XDG desktop directory is configured')
    desktop.mkdir(parents=True,exist_ok=True)
    path=desktop/'CIVI.desktop'
    if path.is_symlink():raise RuntimeError('Refusing to replace a desktop symlink')
    if path.exists() and 'Start CIVI, LAN helper and local panel manually' not in path.read_text():
        raise RuntimeError('CIVI.desktop already exists; keep or rename it before installing this launcher')
    path.write_text(desktop_entry(root),encoding='utf-8');path.chmod(0o755)
    print('Installed:',path,flush=True)
    print('Double-click CIVI to start all three programs. No automatic startup was configured.',flush=True)


@contextlib.contextmanager
def lock(path):
    import fcntl
    with path.open('a') as file:
        try:fcntl.flock(file,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Another CIVI launch/component is already running')
        yield


def helper_ready(config):
    from .broker import BrokerClient
    path=Path(config['pi_network']['socket'])
    if not path.exists():return False
    # An existing but unresponsive socket is not permission to replace it.
    result=BrokerClient(path).request('conflict_status')
    if not result.get('running'):raise RuntimeError('LAN helper exists, but its duplicate-IP guard is not running')
    if result.get('error'):raise RuntimeError(result['error'])
    return True


def civi_ready(config):
    host='127.0.0.1' if config['bind']=='0.0.0.0' else config['bind']
    try:connection=socket.create_connection((host,config['scpi_port']),timeout=2)
    except ConnectionRefusedError:return False
    with connection:
        connection.settimeout(2);connection.sendall(b'*IDN?\n')
        with connection.makefile('rb') as stream:reply=stream.readline(1025).decode('ascii').strip().split(',')
    if len(reply)!=4 or reply[0]!=config['manufacturer'] or not reply[1].startswith('CIVI/') or reply[2]!=config['serial_number']:
        raise RuntimeError('SCPI port is already occupied by another instrument/configuration')
    return True


def panel_pid(config_path):
    for process in psutil.process_iter(['pid','uids','cmdline','cwd']):
        try:
            info=process.info;argv=info['cmdline'] or []
            if not info['uids'] or info['uids'].real!=os.getuid() or '-m' not in argv:continue
            if argv[argv.index('-m')+1]!='civi.pi.panel':continue
            candidate=argv[argv.index('--config')+1] if '--config' in argv else 'config.toml'
            path=Path(candidate)
            if not path.is_absolute():path=Path(info['cwd'])/path
            if path.resolve()==config_path:return info['pid']
        except (psutil.Error,OSError,ValueError,IndexError,TypeError):continue
    return None


def wait_ready(check,seconds,label):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        if check():return
        time.sleep(.5)
    raise RuntimeError(label+' did not become ready. Check its terminal window before trying again.')


def terminal_command(title,config_path,component):
    terminal=shutil.which('lxterminal')
    if not terminal:raise RuntimeError('This Pi desktop launcher needs lxterminal')
    command=[sys.executable,'-m','civi.pi.desktop','--config',str(config_path),'--component',component]
    return [terminal,'--title='+title,'--command='+shlex.join(command)]


def component(name,config,config_path,state):
    with lock(state/(name+'.lock')):
        if name=='helper':
            if helper_ready(config):print('LAN helper already running; reusing it.');return
            import pwd
            owner=pwd.getpwuid(os.getuid()).pw_name
            args=['sudo','--',sys.executable,'-m','civi.pi.broker','--owner',owner,
                  '--interface',config['pi_network']['interface'],'--socket',config['pi_network']['socket']]
            print('If requested, enter the Linux/sudo password here (not the CIVI Web password).',flush=True)
        else:
            if civi_ready(config):print('CIVI already running; reusing it.');return
            args=['bash',str(config_path.parent/'start.sh')]
        process=subprocess.Popen(args)
        try:
            code=process.wait()
            if code:raise RuntimeError(name+' exited with code '+str(code))
        except KeyboardInterrupt:
            # Ctrl+C reaches the terminal group, including the child. Allow its
            # socket/serial/rollback cleanup instead of subprocess.run killing
            # the sudo supervisor immediately on KeyboardInterrupt.
            print('\nWaiting for '+name+' to stop cleanly...',flush=True)
            try:process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.send_signal(signal.SIGINT);process.wait(timeout=20)
            print('Stopped '+name+'.',flush=True)


def launch(config,config_path,state):
    if not os.environ.get('DISPLAY'):raise RuntimeError('Run this launcher from the Pi graphical desktop, not a plain SSH terminal')
    with lock(state/'launch.lock'):
        if helper_ready(config):print('LAN helper already running; reusing it.',flush=True)
        else:
            subprocess.Popen(terminal_command('CIVI LAN helper',config_path,'helper'),start_new_session=True)
            print('Waiting for LAN helper. Enter the Linux/sudo password in its terminal if requested.',flush=True)
            wait_ready(lambda:helper_ready(config),120,'LAN helper')
        if civi_ready(config):print('CIVI already running; reusing it.',flush=True)
        else:
            subprocess.Popen(terminal_command('CIVI server',config_path,'civi'),start_new_session=True)
            print('Waiting for CIVI. On first use, enter its Web password in the CIVI server terminal.',flush=True)
            wait_ready(lambda:civi_ready(config),120,'CIVI')
        pid=panel_pid(config_path)
        if pid:print('Local panel already running; PID '+str(pid),flush=True)
        else:
            # Kept separate from terminal lifetime; GUI close stops only the panel.
            descriptor=os.open(state/'panel.log',os.O_WRONLY|os.O_CREAT|os.O_APPEND,0o600)
            with os.fdopen(descriptor,'a') as output:
                subprocess.Popen([sys.executable,'-m','civi.pi.panel','--config',str(config_path)],
                    stdin=subprocess.DEVNULL,stdout=output,stderr=output,start_new_session=True)
            wait_ready(lambda:panel_pid(config_path),10,'Local panel')
            time.sleep(1)
            if not panel_pid(config_path):raise RuntimeError('Local panel exited during startup; see tmp/desktop/panel.log')
        print('CIVI, LAN helper and local panel are running. Stop server/helper with Ctrl+C in their terminals.',flush=True)


def main():
    parser=argparse.ArgumentParser(description='CIVI manual Pi desktop launcher')
    parser.add_argument('--config',default='config.toml')
    parser.add_argument('--install',action='store_true',help='Install only a desktop shortcut; no autostart')
    parser.add_argument('--check',action='store_true',help='Read current component status without starting anything')
    parser.add_argument('--component',choices=['helper','civi'],help=argparse.SUPPRESS)
    args=parser.parse_args()
    try:
        if platform.system()!='Linux' or os.getuid()==0:raise RuntimeError('Run this launcher as the normal Pi desktop user, without sudo')
        config_path=Path(args.config).resolve();os.chdir(config_path.parent)
        if args.install:install(config_path.parent);return
        from ..config import load
        config=load(str(config_path))
        if not config.get('pi_network',{}).get('enabled'):raise RuntimeError('Enable pi_network in the Pi configuration first')
        if args.check:
            print(json.dumps({'helper':helper_ready(config),'civi':civi_ready(config),'panel_pid':panel_pid(config_path)}));return
        state=config_path.parent/'tmp/desktop'
        state.mkdir(mode=0o700,parents=True,exist_ok=True)
        if args.component:component(args.component,config,config_path,state)
        else:launch(config,config_path,state)
    except (OSError,ValueError,RuntimeError) as error:
        print('CIVI desktop: '+str(error),file=sys.stderr,flush=True)
        if args.component and sys.stdin.isatty():input('Press Enter to close this terminal.')
        raise SystemExit(1)


if __name__=='__main__':main()
