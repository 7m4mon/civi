"""Manual root-only Ethernet audit/provisioning; no service or autostart."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from civi.pi.network import NetworkManager,interface_name
from civi.pi.transactions import Checkpoints

FIELDS=('802-3-ethernet.auto-negotiate','802-3-ethernet.speed','802-3-ethernet.duplex')


def run(args):
    result=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=40,
                          env={**os.environ,'LC_ALL':'C'})
    if result.returncode:raise RuntimeError(result.stderr.strip() or 'Command failed: '+args[0])
    return result.stdout.strip()


def link_fields(text):
    values={};key=None
    for line in text.splitlines():
        if ':' in line:
            key,value=line.strip().split(':',1);values[key]=value.strip()
        elif key in ('Supported link modes','Advertised link modes','Link partner advertised link modes'):
            values[key]+=' '+line.strip()
    return values


def main():
    parser=argparse.ArgumentParser(description='Audit wired Ethernet; explicitly provision unrestricted auto-negotiation')
    parser.add_argument('--interface',default='eth0')
    parser.add_argument('--management-interface',default='wlan0')
    parser.add_argument('--apply-auto',action='store_true',help='Persist autoneg=yes/speed=0/duplex unset and reactivate only the selected wired profile')
    args=parser.parse_args()
    if sys.platform!='linux' or os.geteuid()!=0:raise SystemExit('Run manually with sudo on the Pi/Linux target')
    target=interface_name(args.interface);management=interface_name(args.management_interface)
    manager=NetworkManager();before=manager.snapshot(target)
    def settings():return {key:manager._read('-g',key,'connection','show','uuid',before['uuid']) for key in FIELDS}
    def runtime():return link_fields(run(['ethtool',target]))
    def management_state():
        return {'uuid':manager._read('-g','GENERAL.CON-UUID','device','show',management),
                'ipv4':manager._read('-g','IP4.ADDRESS','device','show',management)}
    old=settings();observed=runtime()
    report={'interface':target,'uuid':before['uuid'],'before':{'network':before,'ethernet':old,'runtime':observed}}
    if not args.apply_auto:print(json.dumps(report,indent=2));return
    if target==management or not before['profile_active'] or not before['carrier']:
        raise RuntimeError('Use a separate management NIC and an active wired profile for this provisioning step')
    if observed.get('Supports auto-negotiation')!='Yes':raise RuntimeError('The NIC did not report auto-negotiation support')
    admin=management_state()
    if not admin['ipv4'] or not re.fullmatch(r'[0-9a-fA-F-]{36}',admin['uuid']):
        raise RuntimeError('The separate management interface needs an active profile and IPv4')
    config=ROOT/'config.toml'
    if config.exists():
        from civi.config import load
        from civi.pi.broker import BrokerClient
        c=load(str(config));socket_path=c.get('pi_network',{}).get('socket')
        if socket_path and Path(socket_path).exists():
            status=BrokerClient(socket_path).request('status')
            if status.get('pending'):raise RuntimeError('Finish the pending CIVI LAN change first')
            if status['snapshot']['uuid']!=before['uuid']:raise RuntimeError('Selected wired profile differs from the helper recovery target')
    base=ROOT/'tmp'/('ethernet-'+time.strftime('%Y%m%d-%H%M%S')+'-'+uuid.uuid4().hex[:6])
    base.mkdir(mode=0o700,parents=True)
    report['management_before']=admin
    (base/'before.json').write_text(json.dumps(report,indent=2))
    checkpoints=Checkpoints();checkpoint=checkpoints.create(target,120)
    try:
        print('Enabling unrestricted auto-negotiation on',target,'UUID',before['uuid'],flush=True)
        run(['nmcli','connection','modify','uuid',before['uuid'],FIELDS[0],'yes',FIELDS[1],'0',FIELDS[2],''])
        run(['nmcli','--wait','30','connection','up','uuid',before['uuid'],'ifname',target])
        end=time.monotonic()+25
        while True:
            after=manager.snapshot(target);actual=runtime()
            if after['carrier'] and after['active_ipv4']==before['active_ipv4'] and actual.get('Auto-negotiation')=='on':break
            if time.monotonic()>end:raise RuntimeError('Wired address/link/auto-negotiation did not recover')
            time.sleep(.5)
        expected={FIELDS[0]:'yes',FIELDS[1]:'0',FIELDS[2]:''}
        if settings()!=expected:raise RuntimeError('Saved Ethernet settings differ from requested defaults')
        if after['profile']!=before['profile']:raise RuntimeError('IPv4/autoconnect profile settings changed unexpectedly')
        if actual.get('Advertised auto-negotiation')!='Yes' or actual.get('Duplex')!='Full' or actual.get('Link detected')!='yes':
            raise RuntimeError('Runtime link is not verified as full-duplex auto-negotiated')
        supported=set(actual.get('Supported link modes','').split())
        if not supported or not supported.issubset(actual.get('Advertised link modes','').split()):
            raise RuntimeError('Not all supported link modes are advertised')
        if management_state()!=admin:raise RuntimeError('Management profile/address changed')
        checkpoints.destroy(checkpoint)
        report.update(after={'network':after,'ethernet':settings(),'runtime':actual},management_unchanged=True,confirmed=True)
        (base/'result.json').write_text(json.dumps(report,indent=2))
        print('PASS:',actual.get('Speed'),actual.get('Duplex'),'autoneg='+actual['Auto-negotiation'],after['active_ipv4'],flush=True)
        print('Management unchanged; artifacts:',base,flush=True)
    except BaseException:
        try:
            if checkpoints.exists(checkpoint):checkpoints.rollback(checkpoint)
            restore=['nmcli','connection','modify','uuid',before['uuid']]
            for key,value in old.items():restore.extend((key,value))
            run(restore)
            run(['nmcli','--wait','30','connection','up','uuid',before['uuid'],'ifname',target])
            restored=manager.snapshot(target)
            verified=settings()==old and restored['profile']==before['profile'] and restored['active_ipv4']==before['active_ipv4'] and management_state()==admin
            (base/'rollback.json').write_text(json.dumps({'verified':verified},indent=2))
            if not verified:raise RuntimeError('Restoration did not match the baseline')
        except Exception as error:raise RuntimeError('Ethernet provisioning failed and restoration needs local inspection') from error
        raise


if __name__=='__main__':main()
