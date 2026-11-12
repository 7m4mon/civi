"""Bounded, receive-only ARP guard for the helper's selected wired interface."""
import logging
import socket
import threading
import time
import psutil
from .network import interface_name

LOGGER=logging.getLogger('civi.lan-helper')


def conflicting_sender(frame, own_mac, addresses):
    """A peer claiming our active IP conflicts; an ordinary ARP probe does not."""
    if len(frame)<42 or frame[12:14]!=b'\x08\x06':return None
    arp=frame[14:42]
    if arp[:6]!=b'\x00\x01\x08\x00\x06\x04' or arp[6:8] not in (b'\x00\x01',b'\x00\x02'):return None
    mac=arp[8:14]
    if mac==own_mac or mac!=frame[6:12] or mac==b'\x00'*6 or mac[0]&1:return None
    ip=socket.inet_ntoa(arp[14:18])
    if ip=='0.0.0.0' or ip not in addresses:return None
    return {'address':ip,'peer_mac':mac.hex(':')}


class ConflictGuard:
    def __init__(self, interface, transactions):
        self.interface=interface_name(interface)
        self.transactions=transactions
        self.lock=threading.Lock()
        self.stop_event=threading.Event()
        self.thread=None;self.sock=None
        self.fault=None;self.error=None;self.checked=None

    def start(self):
        self.sock=socket.socket(socket.AF_PACKET,socket.SOCK_RAW,socket.htons(0x0806))
        try:self.sock.bind((self.interface,0));self.sock.settimeout(.5)
        except BaseException:self.sock.close();self.sock=None;raise
        self.thread=threading.Thread(target=self.run,name='civi-arp-guard',daemon=True)
        self.thread.start()
        LOGGER.info('Duplicate IPv4 guard active on %s; a peer claim disconnects this wired interface',self.interface)

    def snapshot(self):
        with self.lock:
            return {'running':bool(self.thread and self.thread.is_alive()),'fault':dict(self.fault) if self.fault else None,
                    'error':self.error,'sample_age_seconds':None if self.checked is None else round(time.monotonic()-self.checked,1)}

    def clear(self):
        with self.lock:self.fault=None

    def inspect(self,frame):
        # Re-read current kernel assignments, including DHCP and link-local.
        stats=psutil.net_if_stats().get(self.interface)
        addrs=psutil.net_if_addrs().get(self.interface,[])
        own_mac=next((bytes.fromhex(a.address.replace(':','')) for a in addrs if a.family==psutil.AF_LINK),None)
        ips={a.address for a in addrs if a.family==socket.AF_INET}
        if not stats or not stats.isup or not own_mac:return
        conflict=conflicting_sender(frame,own_mac,ips)
        if not conflict:return
        with self.transactions.lock:
            with self.lock:self.fault={**conflict,'disconnected':False};self.error=None
            LOGGER.error('Duplicate IPv4 %s on %s claimed by %s; disconnecting wired LAN',conflict['address'],self.interface,conflict['peer_mac'])
            result=self.transactions.manager.runner(['nmcli','--wait','10','device','disconnect',self.interface],
                capture_output=True,text=True,timeout=15)
            if result.returncode:raise RuntimeError('NetworkManager could not disconnect duplicate IPv4 interface')
            remaining=psutil.net_if_addrs().get(self.interface,[])
            if any(a.family==socket.AF_INET and a.address==conflict['address'] for a in remaining):
                raise RuntimeError('Conflicting IPv4 address remains after disconnect')
            with self.lock:self.fault['disconnected']=True

    def run(self):
        while not self.stop_event.is_set():
            try:
                try:frame=self.sock.recv(65535)
                except socket.timeout:frame=None
                if frame is not None:self.inspect(frame)
                with self.lock:self.checked=time.monotonic()
            except Exception as error:
                with self.lock:self.error='Duplicate IPv4 guard failed: '+str(error);self.checked=time.monotonic()
                LOGGER.error('%s',self.error)
                self.stop_event.wait(.5)

    def close(self):
        self.stop_event.set()
        if self.thread:self.thread.join(timeout=17)
        if self.sock:self.sock.close()
