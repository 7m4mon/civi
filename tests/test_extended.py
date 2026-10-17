"""Wire vectors are specified separately from catalog encoders.

All ports below are fake. No physical radio or transmit operation is used.
"""
import asyncio
import json
import pytest
from civi import scpi
from civi.commands import CATALOG, Codec
from civi.backend import CivBackend, load_profile
from civi.errors import CiviError
from civi.scope import ScopeReceiver
from tests.test_civ import FakeSerial, frame


def fake_backend(config, replies):
    config['serial']['timeout'] = 0.02
    port = FakeSerial(replies)
    return CivBackend(load_profile(),config['serial'],lambda:port),port


@pytest.mark.parametrize('header,arg,wire',[
    ('RAD:AFGAIN','255','14010255'),
    ('RAD:ATT','20','1120'),
    ('RAD:RIT:FREQ','-1200','2100001201'),
    ('RAD:VFO:FREQ','SELECTED,14.074MHz','25000040071400'),
    ('RAD:VFO:MODE','OTHER,010102','2601010102'),
    ('RAD:VFO:ENABLE',None,'07'),
    ('RAD:VFO:COPY',None,'07a0'),
    ('RAD:MEM:SELECT','101','080101'),
    ('RAD:MENU:0094','2026-10-17','1a05009420261017'),
    ('RAD:MENU:0095','23:59','1a0500952359'),
    ('RAD:MENU:0096','-09:30','1a050096093001'),
    ('RAD:MENU:0031','-600000','1a05003100600001'),
    ('RAD:TONE:FREQ','88.5','1b000885'),
    ('RAD:SCOPE:FIXEDGE','101,00001007000000001400','271e010100001007000000001400'),
    ('RAD:MENU:0112','001007002007','1a050112001007002007'),
    ('RAD:TXBAND:USER','1,00001007002D0000200700','1e030100001007002d0000200700'),
    ('RAD:SCOPE:REFERENCE','0,005000','271900005000'),
    ('RAD:SCOPE:ENABLE','0,ON','271001'),
    ('RAD:SCOPE:DISPLAY','0,0','271200'),
    ('RAD:SCOPE:DUAL','0,0','271300'),
    ('RAD:SCOPE:TXDISPLAY','0,ON','271b01'),
    ('RAD:SCOPE:CENTER','0,2','271c02'),
    ('RAD:SCOPE:MARKER','0,ON','272001'),
    ('RAD:SCOPE:HOLD','0,ON','27170001'),
    ('RAD:BAND:STACK','101,9520940100030200000885000885','1a0101019520940100030200000885000885'),
])
def test_independent_wire_vectors(config,header,arg,wire):
    b,p = fake_backend(config,[[frame(b'\xfb')]])
    spec = CATALOG[header]
    prefix,data = spec.prepare(False,arg)
    b.execute_command(spec,False,prefix,data)
    assert p.writes == [frame(bytes.fromhex(wire),dest=0x94,source=0xe0)]


@pytest.mark.parametrize('header,args,payload,result',[
    ('RAD:AFGAIN',None,'14010255','255'),
    ('READ:SWR',None,'15120048','48'),
    ('RAD:RIT:FREQ',None,'2100001201','-1200'),
    ('RAD:TONE:FREQ',None,'1b00000885','88.5'),
    ('RAD:VFO:FREQ','OTHER','25010040071400','14074000'),
    ('RAD:MENU:0094',None,'1a05009420261017','2026-10-17'),
    ('RAD:MENU:0096',None,'1a050096093001','-09:30'),
    ('RAD:DATA',None,'1a060001','0001'),
    ('RAD:BAND:EDGES',None,'0200001007002d0000200700','00001007002D0000200700'),
    ('RAD:SCOPE:ENABLE','0','271001','ON'),
    ('RAD:SCOPE:STREAM','0','271101','ON'),
    ('RAD:SCOPE:CENTER','0','271c02','2'),
    ('RAD:SCOPE:HOLD','0','27170001','ON'),
    ('RAD:BAND:STACK','101','1a0101019520940100030200000885000885','9520940100030200000885000885'),
    ('RAD:SCOPE:REFERENCE','0','271900005000','005000'),
    ('RAD:SCOPE:REFERENCE','0','271900005001','005001'),
])
def test_query_vectors(config,header,args,payload,result):
    b,_=fake_backend(config,[[frame(bytes.fromhex(payload))]])
    spec=CATALOG[header]
    prefix,data=spec.prepare(True,args)
    assert b.execute_command(spec,True,prefix,data)==result


@pytest.mark.parametrize('command',[
    'RAD:AFGAIN -1','RAD:AFGAIN 256','RAD:ATT 1','RAD:RIT:FREQ -10000',
    'RAD:VFO:FREQ? WRONG','RAD:VFO:MODE OTHER,090001','RAD:VFO:MODE OTHER,010100',
    'RAD:MENU:0094 2026-02-30','RAD:MENU:0095 24:01','RAD:MENU:0096 +14:01',
    'RAD:MENU:0074 ON','RAD:MENU:0028?','RAD:MENU:0031 500','RAD:DATA 0001',
    'RAD:MENU:0001 0026','RAD:MENU:0104 999900000000','RAD:VFO:SWAP EXTRA',
    'RAD:BAND:STACK? 104','RAD:SCOPE:FIXEDGE? 105',
    'RAD:MEM:CONTENT 100,FF',
    'RAD:MENU:0014 40','RAD:MENU:0001 2005','RAD:MENU:0112 00001007000000200700',
    'RAD:SCOPE:REFERENCE 0,200500','RAD:SCOPE:REFERENCE 0,205000','RAD:SCOPE:REFERENCE 0,000500','RAD:TXBAND:USER 1,0000100700000000200700',
])
def test_invalid_parameters_rejected_before_io(command):
    with pytest.raises(CiviError): scpi.parse(command)


def test_documented_menu_inventory_and_readonly_exception():
    menus = {int(header.rsplit(':',1)[1]):spec for header,spec in CATALOG.items() if header.startswith('RAD:MENU:')}
    assert set(menus) == set(range(1,218))-{28}
    assert menus[74].access == 'r'
    assert menus[72].codec.size == 2
    assert menus[157].codec.minimum == 1
    assert menus[157].codec.maximum == 9999


async def test_all_catalog_entries_executable_on_mock(service):
    # Exercise the complete browser catalog through the parser and shared queue,
    # with every side-effect class explicitly enabled only on the mock backend.
    service.config['permissions'] = dict.fromkeys(('menu','memory','power','link','calibration'),True)
    service.config['transmit']['enabled'] = True
    for header,spec in CATALOG.items():
        if 'w' in spec.access:
            result=await service.execute('test',header+' '+spec.public()['set_example'])
            assert result is None,header
            assert await service.execute('test','SYST:ERR?') == '0,"No error"',header
        if 'r' in spec.access:
            result=await service.execute('test',header+'? '+spec.public()['query_example'])
            assert result is not None and result != 'ERROR',header
            assert await service.execute('test','SYST:ERR?') == '0,"No error"',header


async def test_permission_gates_do_not_block_reads(service):
    for command in ('RAD:MENU:0094 2026-10-17','RAD:MEM:CLEAR','RAD:POWER:ON','RAD:MENU:0075 ON','RAD:MENU:0058 128','RAD:CW:SEND CQ'):
        await service.execute('test',command)
        assert (await service.execute('test','SYST:ERR?')).startswith('-203,'),command
    assert await service.execute('test','RAD:MENU:0094?') == '2026-01-01'
    assert service.owner is None


@pytest.mark.parametrize('start,stop', [('RAD:CW:SEND CQ','RAD:CW:STOP'),('RAD:VOICE T1','RAD:VOICE STOP'),('RAD:VOX ON','RAD:VOX OFF'),('RAD:BKIN SEMI','RAD:BKIN OFF'),('RAD:TUNER TUNE','RAD:TUNER OFF')])
async def test_transmit_paths_owned_stopped_and_timed_out(service,start,stop):
    service.config['transmit'].update(enabled=True,max_seconds=0.1)
    await service.execute('test',start)
    assert service.owner == 'test'
    await service.execute('test',stop)
    assert service.owner is None
    assert not service.backend.ptt
    await service.execute('test',start)
    await asyncio.sleep(0.4)
    assert service.owner is None
    assert not service.backend.ptt


async def test_extended_queries_preserve_selectors_and_error_isolation(service):
    service.connect('other')
    assert await service.execute('test','RAD:VFO:FREQ OTHER,14.074MHz;FREQ? OTHER') == '14074000'
    await service.execute('other','RAD:AFGAIN 999')
    assert await service.execute('test','SYST:ERR?') == '0,"No error"'
    assert (await service.execute('other','SYST:ERR?')).startswith('-222,')
    service.config['permissions']['menu']=True
    assert await service.execute('test','RAD:MENU:0091 "CIVI";0091?') == '"CIVI"'


def test_bad_extended_response_quarantines(config):
    b,_=fake_backend(config,[[frame(bytes.fromhex('1401ff00'))]])
    spec=CATALOG['RAD:AFGAIN']
    with pytest.raises(CiviError,match='Malformed'):
        b.execute_command(spec,True,*spec.prepare(True,None))
    assert b.state == 'quarantined'


@pytest.mark.parametrize('payload',[
    '0200001007000000200700',  # Missing delimiter.
    '020000100700000000200700',  # Incorrect delimiter.
    '0200002007002d0000100700',  # Reversed edges.
])
def test_band_edge_response_rejects_malformed_pair(config,payload):
    b,_=fake_backend(config,[[frame(bytes.fromhex(payload))]])
    spec=CATALOG['RAD:BAND:EDGES']
    with pytest.raises(CiviError,match='Malformed'):
        b.execute_command(spec,True,*spec.prepare(True,None))
    assert b.state == 'quarantined'


def sweep_packets():
    # 7.1 MHz center, 50 kHz span, raw 0..160, 475 points.
    yield bytes.fromhex('000111000000100700000005000000')
    for number in range(2,12):
        yield bytes.fromhex(f'00{number:02}11') + bytes([number]* (25 if number==11 else 50))


def test_scope_reassembly_loss_reordering_and_freshness():
    scope=ScopeReceiver()
    packets=list(sweep_packets())
    scope.feed(packets[0]); scope.feed(packets[2])
    assert scope.snapshot() is None
    assert scope.invalid_packets == 1
    for packet in packets: scope.feed(packet)
    wave=scope.snapshot()
    assert len(wave['points'])==475
    assert wave['frequency_1_hz']==7100000
    assert wave['frequency_2_hz']==50000
    assert wave['points'][:50]==[2]*50
    assert wave['points'][-25:]==[11]*25
    scope.latest['timestamp']-=6
    assert scope.snapshot() is None


def test_scope_out_of_range_and_negative_scroll_edge():
    scope=ScopeReceiver()
    scope.feed(bytes.fromhex('0001110200100000f0000000010001'))
    wave=scope.snapshot()
    assert wave['out_of_range'] is True
    assert wave['points']==[]
    assert wave['frequency_1_hz']==-1000


async def test_mock_scope_stream_via_shared_queue(service):
    assert await service.execute('test','RAD:SCOPE:WAVE?')=='ERROR'
    await service.execute('test','*CLS;RAD:SCOPE:STREAM 0,ON')
    await service.admin('test','events')
    wave=json.loads(await service.execute('test','RAD:SCOPE:WAVE?'))
    assert len(wave['points'])==475
    await service.execute('test','RAD:SCOPE:STREAM 0,OFF')
    assert not service.backend.scope_stream


def test_scope_prerequisites_prevent_wrong_serial_configuration(config):
    config["serial"]["baud"] = 19200
    b,p=fake_backend(config,[])
    spec=CATALOG['RAD:SCOPE:STREAM']
    with pytest.raises(CiviError,match='115200'):
        b.execute_command(spec,False,*spec.prepare(False,'0,ON'))
    assert p.writes==[]


def test_scope_stream_wire_format_after_prerequisite_check(config):
    config['serial']['baud']=115200
    b,p=fake_backend(config,[[frame(bytes.fromhex('1a05007401'))],[frame(b'\xfb')],[frame(b'\xfb')]])
    spec=CATALOG['RAD:SCOPE:STREAM']
    b.execute_command(spec,False,*spec.prepare(False,'0,ON'))
    b.execute_command(spec,False,*spec.prepare(False,'0,OFF'))
    assert p.writes==[frame(bytes.fromhex(payload),dest=0x94,source=0xe0) for payload in ('1a050074','271101','271100')]


def test_nak_reports_rejected_wire_command(config):
    b,_=fake_backend(config,[[frame(b'\xfa')]])
    spec=CATALOG['RAD:SCOPE:ENABLE']
    with pytest.raises(CiviError,match='Radio rejected CI-V 27 10 01'):
        b.execute_command(spec,False,*spec.prepare(False,'0,ON'))


def test_stack_record_is_one_14_byte_record_not_memory_dual_record():
    codec=CATALOG['RAD:BAND:STACK'].codec
    captured=bytes.fromhex('9520940100030200000885000885')
    assert codec.decode(captured)=='9520940100030200000885000885'
    with pytest.raises(CiviError): codec.decode(captured*2)


def test_power_on_uses_baud_dependent_wake_preamble(config):
    config["serial"]["baud"] = 19200
    b,p=fake_backend(config,[[],[frame(b'\xfb')]])
    spec=CATALOG['RAD:POWER:ON']
    b.execute_command(spec,False,*spec.prepare(False,None))
    assert p.writes == [b'\xfe'*25,frame(b'\x18\x01',dest=0x94,source=0xe0)]


def test_scope_packets_do_not_consume_normal_replies(config):
    stream=b''.join(frame(b'\x27\x00'+part) for part in sweep_packets())
    b,p=fake_backend(config,[[stream+frame(bytes.fromhex('14010128'))]])
    b.scope_stream=True
    spec=CATALOG['RAD:AFGAIN']
    assert b.execute_command(spec,True,*spec.prepare(True,None))=='128'
    assert len(b.scope.snapshot()['points'])==475


async def test_mock_memory_and_vfo_state_is_preserved(service):
    service.config['permissions']['memory']=True
    await service.execute('test','SENS:FREQ 7100100;:RAD:MEM:WRITE')
    record=await service.execute('test','RAD:MEM:CONTENT? 1')
    assert record.startswith('000001100700')
    await service.execute('test','SENS:FREQ 7200000;:RAD:VFO:COPY;:RAD:VFO:SELECT B')
    assert await service.execute('test','SENS:FREQ?')=='7200000'
    await service.execute('test','RAD:MEM:SELECT 1')
    assert await service.execute('test','SENS:FREQ?')=='7100100'
    await service.execute('test','RAD:MEM:CLEAR')
    assert await service.execute('test','RAD:MEM:CONTENT? 1')=='FF'
    assert await service.execute('test','RAD:VFO:FREQ OTHER,70MHz') is None
    assert (await service.execute('test','SYST:ERR?')).startswith('-222,')
