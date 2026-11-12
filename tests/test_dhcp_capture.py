import socket,struct
from tools.pi_dhcp_check import dhcp_record


def packet(options):
    bootp=bytearray(240);bootp[0]=2;bootp[16:20]=socket.inet_aton('192.0.2.10');bootp[236:240]=b'\x63\x82\x53\x63'
    bootp+=options+b'\xff'
    udp=struct.pack('!HHHH',67,68,len(bootp)+8,0)+bootp
    ip=bytearray(20);ip[0]=0x45;ip[9]=17
    return b'\x00'*12+b'\x08\x00'+ip+udp


def test_decode_real_dhcp_fields_for_acceptance_evidence():
    frame=packet(b'\x35\x01\x05\x33\x04\x00\x00\x00\x78\x37\x03\x01\x03\x06\x03\x04\xc0\x00\x02\x01')
    record=dhcp_record(frame,1)
    assert record['message_type']==5 and record['lease_seconds']==120
    assert record['yiaddr']=='192.0.2.10' and record['gateway']==['192.0.2.1']
    assert record['parameter_request_list']==[1,3,6]


def test_truncated_packet_and_malformed_option_do_not_create_evidence():
    frame=packet(b'\x35\x01\x05')
    assert dhcp_record(frame[:-1],1) is None
    assert dhcp_record(packet(b'\x35\xff\x05'),1) is None
    assert dhcp_record(b'noise',1) is None
