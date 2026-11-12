"""Safety boundaries of the opt-in Windows DHCP fixture, not gateway startup."""
import os
import socket
import struct

import pytest

from tools.windows_dhcp_lab import COOKIE, Policy, option, options
from tools.windows_pktinfo import Datagram

CONFIG={'interface_index':4,'server_ip':'192.168.73.1',
        'client_ip':'192.168.73.3','client_mac':'02:c1:71:00:00:02'}
STATE={'enabled':True,'gateway':'192.168.73.1','dns':['192.168.73.53'],'hostname':''}


def packet(kind=1, *, ciaddr='0.0.0.0', extras=()):
    raw=bytearray(240)
    raw[:4]=b'\x01\x01\x06\x00';raw[4:8]=bytes.fromhex('abcdef01')
    raw[10:12]=b'\x80\x00';raw[12:16]=socket.inet_aton(ciaddr)
    raw[28:34]=bytes.fromhex('02c171000002');raw[236:]=COOKIE
    raw.extend(option(53,bytes([kind])))
    for code,value in extras:raw.extend(option(code,value))
    raw.append(255)
    return bytes(raw)


@pytest.mark.parametrize('change', ['interface','port','mac','relay','opcode','hlen','kind','foreign_server','foreign_address','foreign_ciaddr','truncated','no_end','overload'])
def test_other_interfaces_clients_and_malformed_requests_never_get_reply(change):
    raw=bytearray(packet());peer=('0.0.0.0',68);interface=4
    if change=='interface':interface=12
    elif change=='port':peer=('0.0.0.0',1068)
    elif change=='mac':raw[33]^=1
    elif change=='relay':raw[24:28]=socket.inet_aton('192.168.73.99')
    elif change=='opcode':raw[0]=2
    elif change=='hlen':raw[2]=16
    elif change=='kind':raw=packet(8)
    elif change=='foreign_server':raw=packet(3,extras=[(50,socket.inet_aton(CONFIG['client_ip'])),(54,socket.inet_aton('192.168.73.254'))])
    elif change=='foreign_address':raw=packet(3,extras=[(50,socket.inet_aton('192.168.73.9'))])
    elif change=='foreign_ciaddr':raw=packet(ciaddr='192.168.73.9')
    elif change=='truncated':raw=raw[:-1]+b'\x01\x10\x00'
    elif change=='no_end':raw=raw[:-1]
    elif change=='overload':raw=packet(extras=[(52,b'\x01')])
    assert Policy(CONFIG).reply(bytes(raw),peer,interface,STATE) is None


def test_offer_and_initial_ack_have_bounded_lease_and_echo_transaction():
    policy=Policy(CONFIG)
    for kind in [1,3]:
        request=packet(kind,extras=[(50,socket.inet_aton(CONFIG['client_ip'])),(61,b'\x01test-client')])
        reply,destination,event=policy.reply(request,('0.0.0.0',68),4,STATE)
        assert reply[4:8]==request[4:8] and reply[10:12]==request[10:12]
        assert reply[28:44]==request[28:44]
        assert socket.inet_ntoa(reply[16:20])==CONFIG['client_ip']
        assert destination==('255.255.255.255',68)
        values=options(reply)
        assert values[53]==bytes([2 if kind==1 else 5])
        assert values[54]==socket.inet_aton(CONFIG['server_ip'])
        assert [struct.unpack('!I',values[k])[0] for k in (51,58,59)]==[120,60,105]
        assert values[61]==b'\x01test-client'
        assert event['interface']==4 and len(reply)>=300


def test_natural_renewal_uses_ciaddr_unicast_and_updated_or_missing_options():
    policy=Policy(CONFIG);request=packet(3,ciaddr=CONFIG['client_ip'])
    for state in [STATE,{**STATE,'gateway':'192.168.73.254','dns':['192.168.73.54'],'hostname':'other-dhcp-name'},
                  {**STATE,'gateway':'','dns':[]}]:
        reply,destination,event=policy.reply(request,(CONFIG['client_ip'],68),4,state)
        assert destination==(CONFIG['client_ip'],68)
        values=options(reply)
        assert socket.inet_ntoa(reply[12:16])==CONFIG['client_ip']
        assert (3 in values)==bool(state['gateway'])
        assert (6 in values)==bool(state['dns'])
        assert event['gateway']==state['gateway'] and event['dns']==state['dns']
        assert values.get(12,b'').decode()==state['hostname']


def test_disabled_server_does_not_extend_lease():
    assert Policy(CONFIG).reply(packet(3,ciaddr=CONFIG['client_ip']),
        (CONFIG['client_ip'],68),4,{**STATE,'enabled':False}) is None


@pytest.mark.parametrize('kind',[1,3])
def test_reacquisition_from_zero_source_with_old_ciaddr_gets_broadcast(kind):
    request=packet(kind,ciaddr=CONFIG['client_ip'],extras=[(50,socket.inet_aton(CONFIG['client_ip']))])
    reply,destination,_=Policy(CONFIG).reply(request,('0.0.0.0',68),4,STATE)
    assert destination==('255.255.255.255',68)
    assert reply[16:20]==socket.inet_aton(CONFIG['client_ip'])


def test_explicit_short_lease_changes_server_timers_only():
    policy=Policy({**CONFIG,'lease_seconds':60})
    reply,_,event=policy.reply(packet(),('0.0.0.0',68),4,STATE)
    values=options(reply)
    assert [struct.unpack('!I',values[k])[0] for k in (51,58,59)]==[60,30,52]
    assert event['lease_seconds']==60


@pytest.mark.parametrize('seconds',[0,30,121,'60',True])
def test_unsupported_lease_is_rejected(seconds):
    with pytest.raises(ValueError,match='60 or 120'):
        Policy({**CONFIG,'lease_seconds':seconds})


@pytest.mark.parametrize('state', [{**STATE,'gateway':'192.168.4.1'},
                                  {**STATE,'dns':['8.8.8.8']},
                                  {**STATE,'hostname':'bad\nname'},
                                  {**STATE,'enabled':'yes'}])
def test_control_state_cannot_advertise_other_network_options(state):
    with pytest.raises(ValueError):Policy(CONFIG).state(state)


@pytest.mark.skipif(os.name!='nt',reason='Windows Winsock ancillary-data integration')
def test_windows_pktinfo_receives_actual_interface_and_selects_outgoing_interface():
    receiver,sender=Datagram(),Datagram()
    try:
        # Windows IPv4 loopback has index 1; no physical network traffic involved.
        sender.send(b'civi-loopback',('127.0.0.1',receiver.sock.getsockname()[1]),1,'127.0.0.1')
        received=receiver.receive(2)
        assert received is not None
        raw,peer,interface,destination=received
        assert raw==b'civi-loopback' and peer[0]=='127.0.0.1'
        assert interface==1 and destination=='127.0.0.1'
    finally:
        receiver.close();sender.close()
