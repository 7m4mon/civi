import socket
import struct
import threading
from types import SimpleNamespace
import pytest
from civi.pi.conflict import conflicting_sender,ConflictGuard
from civi.pi.broker import dispatch
from civi.indicator import LanIndicator


MAC=bytes.fromhex('02c171000002')
PEER=bytes.fromhex('02c171000003')


def frame(ip='192.0.2.88',mac=PEER,op=1):
    return b'\xff'*6+mac+b'\x08\x06'+struct.pack('!HHBBH',1,0x0800,6,4,op)+mac+socket.inet_aton(ip)+b'\x00'*6+socket.inet_aton('192.0.2.88')


def test_only_foreign_claims_for_active_own_addresses_trigger():
    assert conflicting_sender(frame(),MAC,{'192.0.2.88'})=={'address':'192.0.2.88','peer_mac':'02:c1:71:00:00:03'}
    for packet in (frame(mac=MAC),frame('0.0.0.0'),frame('192.0.2.89'),frame(op=3),frame()[:-1],b'noise',frame(mac=b'\xff'*6)):
        assert conflicting_sender(packet,MAC,{'192.0.2.88'}) is None
    assert conflicting_sender(frame(),MAC,set()) is None


def test_guard_disconnects_only_target_and_verifies_removal(monkeypatch):
    active=[True];calls=[]
    import psutil
    def addrs():
        return {'eth0':([SimpleNamespace(family=socket.AF_INET,address='192.0.2.88')] if active[0] else [])+[SimpleNamespace(family=psutil.AF_LINK,address=MAC.hex(':'))]}
    monkeypatch.setattr(psutil,'net_if_addrs',addrs)
    monkeypatch.setattr(psutil,'net_if_stats',lambda:{'eth0':SimpleNamespace(isup=True)})
    def runner(args,**kwargs):calls.append(args);active[0]=False;return SimpleNamespace(returncode=0)
    tx=SimpleNamespace(lock=threading.RLock(),manager=SimpleNamespace(runner=runner))
    guard=ConflictGuard('eth0',tx);guard.inspect(frame())
    assert calls==[['nmcli','--wait','10','device','disconnect','eth0']]
    assert guard.snapshot()['fault']['disconnected']
    indicator=LanIndicator()
    indicator.update({'present':True,'link':True,'addresses':[],'runtime_conflict':guard.snapshot()['fault']})
    assert indicator.snapshot()['state']=='fault'
    assert any('Duplicate IPv4' in message for message in indicator.snapshot()['faults'])
    tx.conflict_guard=guard
    tx.confirm=lambda token:{'confirmed':True}
    assert dispatch(tx,{'op':'conflict_status'})['fault']
    dispatch(tx,{'op':'confirm','token':'test'})
    assert guard.snapshot()['fault'] is None


def test_guard_does_not_claim_success_when_disconnect_fails(monkeypatch):
    import psutil
    monkeypatch.setattr(psutil,'net_if_addrs',lambda:{'eth0':[SimpleNamespace(family=socket.AF_INET,address='192.0.2.88'),SimpleNamespace(family=psutil.AF_LINK,address=MAC.hex(':'))]})
    monkeypatch.setattr(psutil,'net_if_stats',lambda:{'eth0':SimpleNamespace(isup=True)})
    tx=SimpleNamespace(lock=threading.RLock(),manager=SimpleNamespace(runner=lambda *a,**k:SimpleNamespace(returncode=1)))
    guard=ConflictGuard('eth0',tx)
    with pytest.raises(RuntimeError,match='could not disconnect'):guard.inspect(frame())
    assert guard.snapshot()['fault']['disconnected'] is False


def test_missing_guard_is_unknown_instead_of_normal():
    indicator=LanIndicator()
    indicator.update({'present':True,'link':True,'addresses':['192.0.2.88'],'guard_error':'Guard offline'})
    assert indicator.snapshot()['state']=='unknown'
