import socket
import struct
from tools.pi_conflict_check import arp_record


def test_arp_probe_and_peer_announcement_are_distinguished():
    def packet(sender,target):
        return b'\xff'*6+bytes.fromhex('02c171000003')+b'\x08\x06'+struct.pack('!HHBBH',1,0x0800,6,4,1)+bytes.fromhex('02c171000003')+socket.inet_aton(sender)+b'\x00'*6+socket.inet_aton(target)
    probe=arp_record(packet('0.0.0.0','192.0.2.88'))
    assert probe=={'op':1,'mac':'02:c1:71:00:00:03','sender':'0.0.0.0','target':'192.0.2.88'}
    claim=arp_record(packet('192.0.2.88','192.0.2.88'))
    assert claim['sender']==claim['target']=='192.0.2.88'
    assert arp_record(packet('0.0.0.0','192.0.2.88')[:-1]) is None
    assert arp_record(b'noise') is None
