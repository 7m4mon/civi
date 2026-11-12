"""Keep replies sourced from this NIC's AutoIP on its physical link."""
import ipaddress
import json
import logging
import os
from pathlib import Path
import socket
import stat
import subprocess
import threading
import time
import psutil
from .network import interface_name
from .lci import write_private

LOGGER=logging.getLogger('civi.lan-helper')
TABLE=31927
PRIORITY=11927


def source_addresses(interface):
    return {a.address for a in psutil.net_if_addrs().get(interface,[])
            if a.family==socket.AF_INET and ipaddress.IPv4Address(a.address).is_link_local}


class LinkLocalRoutes:
    def __init__(self,interface,transactions,directory='/run/civi-lan',runner=subprocess.run,addresses=source_addresses):
        self.interface=interface_name(interface);self.transactions=transactions
        self.directory=Path(directory);self.path=self.directory/'autoip-routing.json'
        self.runner=runner;self.addresses=addresses
        self.owned=set();self.lock_file=None;self.thread=None
        self.done=threading.Event();self.lock=threading.Lock()
        self.checked=None;self.error=None;self.report_sources=[]

    def command(self,*args):
        result=self.runner(['ip','-4',*map(str,args)],capture_output=True,text=True,timeout=5)
        if result.returncode:raise RuntimeError(result.stderr.strip() or 'AutoIP routing command failed')
        return result.stdout

    def layout(self):
        rules=[r for r in json.loads(self.command('-j','rule','show')) if r.get('priority')==PRIORITY or str(r.get('table'))==str(TABLE)]
        routes=[r for r in json.loads(self.command('-j','route','show','table','all')) if str(r.get('table'))==str(TABLE)]
        for rule in rules:
            source=rule.get('src','').removesuffix('/32')
            if rule.get('priority')!=PRIORITY or str(rule.get('table'))!=str(TABLE) or source not in self.owned or set(rule)-{'priority','src','table','flags','protocol'}:
                raise RuntimeError('CIVI AutoIP rule priority/table is occupied by an unowned rule')
        for route in routes:
            if route.get('dst')!='default' or route.get('dev')!=self.interface or route.get('gateway') or route.get('scope')!='link' or route.get('protocol')!='static':
                raise RuntimeError('CIVI AutoIP table contains an unowned route')
        if routes and not self.path.exists():raise RuntimeError('CIVI AutoIP table has no ownership record')
        return rules,routes

    def persist(self):
        data={'version':1,'interface':self.interface,'table':TABLE,'priority':PRIORITY,'sources':sorted(self.owned)}
        if self.path.exists() and json.loads(self.path.read_text())==data:return
        write_private(self.path,data)

    def update(self):
        with self.transactions.lock:
            wanted=set(self.addresses(self.interface))
            if any(not isinstance(ipaddress.ip_address(ip),ipaddress.IPv4Address) or not ipaddress.ip_address(ip).is_link_local for ip in wanted):
                raise RuntimeError('Invalid AutoIP source observation')
            rules,routes=self.layout()
            old=self.owned.copy()
            # Journal intended ownership before mutation so a restarted helper
            # can clean only the exact rules left by an interrupted update.
            self.owned|=wanted;self.persist()
            if wanted and not routes:
                self.command('route','add','table',TABLE,'default','dev',self.interface,'scope','link','proto','static')
            present={r['src'].removesuffix('/32') for r in rules}
            for source in sorted(wanted-present):
                self.command('rule','add','priority',PRIORITY,'from',source+'/32','table',TABLE)
            for rule in rules:
                source=rule['src'].removesuffix('/32')
                if source not in wanted:self.command('rule','del','priority',PRIORITY,'from',source+'/32','table',TABLE)
            if not wanted and routes:
                self.command('route','del','table',TABLE,'default','dev',self.interface,'scope','link','proto','static')
            self.owned=wanted;self.persist()
            verified_rules,verified_routes=self.layout()
            if {r['src'].removesuffix('/32') for r in verified_rules}!=wanted or bool(verified_routes)!=bool(wanted):
                raise RuntimeError('AutoIP source-routing verification failed')
            if old!=wanted:LOGGER.info('AutoIP on-link replies | %s | sources=%s',self.interface,', '.join(sorted(wanted)) or '(none)')
            with self.lock:self.checked=time.monotonic();self.error=None;self.report_sources=sorted(wanted)

    def start(self):
        import fcntl
        self.directory.mkdir(mode=0o755,parents=True,exist_ok=True)
        info=self.directory.lstat()
        if info.st_uid!=0 or info.st_mode & 0o022 or stat.S_ISLNK(info.st_mode):raise RuntimeError('Unsafe AutoIP routing state directory')
        self.lock_file=(self.directory/'autoip-routing.lock').open('a')
        try:
            fcntl.flock(self.lock_file,fcntl.LOCK_EX|fcntl.LOCK_NB)
            if self.path.exists() or self.path.is_symlink():
                info=self.path.lstat()
                if info.st_uid!=0 or info.st_mode & 0o077 or not stat.S_ISREG(info.st_mode):raise RuntimeError('Unsafe AutoIP ownership record')
                saved=json.loads(self.path.read_text())
                if (saved.get('version'),saved.get('interface'),saved.get('table'),saved.get('priority'))!=(1,self.interface,TABLE,PRIORITY):
                    raise RuntimeError('AutoIP ownership record belongs to another interface/configuration')
                self.owned=set(saved['sources'])
                if any(not ipaddress.IPv4Address(ip).is_link_local for ip in self.owned):raise RuntimeError('Invalid saved AutoIP source')
            self.update()
        except BaseException:
            self.lock_file.close();self.lock_file=None;raise
        self.thread=threading.Thread(target=self.run,name='civi-autoip-routing',daemon=True);self.thread.start()

    def run(self):
        while not self.done.wait(1):
            try:self.update()
            except Exception as error:
                with self.lock:self.error='AutoIP routing unavailable: '+str(error);self.checked=time.monotonic()
                LOGGER.error('%s',self.error)

    def snapshot(self):
        with self.lock:
            return {'running':bool(self.thread and self.thread.is_alive()),'sources':list(self.report_sources),'table':TABLE,'priority':PRIORITY,
                    'error':self.error,'sample_age_seconds':None if self.checked is None else round(time.monotonic()-self.checked,1)}

    def close(self):
        self.done.set()
        if self.thread:self.thread.join(timeout=35)
        if self.lock_file:
            try:
                saved=self.addresses;self.addresses=lambda interface:set()
                self.update();self.addresses=saved
            finally:self.lock_file.close();self.lock_file=None
