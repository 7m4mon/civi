import asyncio
import pytest
from civi.errors import CiviError
from civi.scpi import frequency, parse


@pytest.mark.parametrize("text,expected", [("7.1MHz",7100000),("7100 kHz",7100000),("7.1e6 Hz",7100000),("7100000",7100000)])
def test_frequency(text, expected): assert frequency(text) == expected


@pytest.mark.parametrize("text", ["NaN", "1 dBm", "0.1Hz", "-1", "1e999999999", "1e999"])
def test_invalid_frequency(text):
    with pytest.raises(CiviError): frequency(text)


@pytest.mark.parametrize("text", ["sense:frequency?", "SENS:FREQ?", "SENSe:FREQ?", ":SENS:FREQUENCY?"])
def test_mnemonics(text): assert parse(text)[0:2] == ("frequency", True)


async def test_commands_errors_and_relative_paths(service):
    assert await service.execute("test", "sens:freq 7.2MHz;FREQ?;:RAD:MODE USB;MODE?;*OPC?") == "7200000;USB;1"
    assert await service.execute("test", "*IDN?") == "CIVI Project,CIVI/IC-7300,CIVI-0001,0.1.0"
    assert await service.execute("test", "READ:SMET?") == "96"
    assert await service.execute("test", "SENS:FREQ 100MHz") is None
    assert (await service.execute("test", "SYST:ERR?")).startswith("-222,")
    assert await service.execute("test", "RAD:MODE NOPE;*RST;*CLS;SYST:ERR?") == '0,"No error"'
    assert await service.execute("test", "BAD?") == "ERROR"
    assert (await service.execute("test", "SYST:ERR?")).startswith("-113,")


async def test_default_ptt_disabled(service):
    await service.execute("test", "RAD:PTT ON")
    assert not service.backend.ptt
    assert (await service.execute("test", "SYST:ERR?")).startswith("-203,")


async def test_error_isolation_and_fault(service):
    service.connect("other")
    service.backend.failure = "USB disconnected"
    assert await service.execute("test", "SENS:FREQ?") == "ERROR"
    assert service.snapshot()["connection"] == "disconnected"
    assert service.snapshot()["values"]["frequency"] is None
    assert await service.execute("other", "SYST:ERR?") == '0,"No error"'
    assert (await service.execute("test", "SYST:ERR?")).startswith("-365,")
    await service.admin("test", "recover")
    assert await service.execute("test", "SENS:FREQ?") == "7100000"


async def test_concurrent_atomic_messages(service):
    for i in range(40): service.connect(str(i))
    results = await asyncio.gather(*(service.execute(str(i), f"SENS:FREQ {7100000+i};*OPC?;:SENS:FREQ?") for i in range(40)))
    assert results == [f"1;{7100000+i}" for i in range(40)]


async def test_mock_transmit_deadline_and_disconnect(service):
    service.config["transmit"].update(enabled=True, max_seconds=0.1)
    await service.execute("test", "RAD:PTT ON")
    assert service.backend.ptt
    await asyncio.sleep(0.6)
    assert not service.backend.ptt
    await service.execute("test", "RAD:PTT ON")
    await service.disconnect("test")
    assert not service.backend.ptt


async def test_mock_web_lease_and_ownership(service):
    service.config["transmit"].update(enabled=True, web_lease_seconds=0.1)
    service.connect("web", web=True)
    await service.execute("web", "RAD:PTT ON")
    await service.execute("test", "RAD:PTT ON")
    assert (await service.execute("test", "SYST:ERR?")).startswith("-200,")
    await asyncio.sleep(0.6)
    assert not service.backend.ptt
    assert "web" not in service.clients


async def test_identification_unknown_and_manual_firmware(service):
    assert await service.execute('test', 'RAD:FIRM?') == 'Unknown'
    service.config['radio_firmware'] = '1.42'
    assert await service.execute('test', 'RADio:FIRMware?') == '1.42'
    assert (await service.execute('test', '*IDN?')).endswith(',0.1.0')
    assert service.snapshot()['radio_model'] == 'IC-7300'
    assert service.snapshot()['radio_firmware_source'] == 'manual'
    service.backend.failure = 'USB disconnected'
    assert await service.execute('test', 'SENS:FREQ?') == 'ERROR'
    assert await service.execute('test', '*IDN?') == 'CIVI Project,CIVI/Unknown,CIVI-0001,0.1.0'
    assert service.snapshot()['radio_model'] == 'Unknown'
    assert service.snapshot()['radio_model_id'] is None


async def test_unrecognized_model_id_not_assumed_from_profile(service):
    original = service.backend.call
    service.backend.call = lambda op, value=None: 0x01 if op == 'model_id_get' else original(op, value)
    assert await service.execute('test', '*IDN?') == 'CIVI Project,CIVI/Unknown,CIVI-0001,0.1.0'
    assert service.snapshot()['radio_model_id'] == 0x01


async def test_serial_settings_clear_identification(service):
    await service.execute('test', '*IDN?')
    await service.admin('test', 'serial', {'port': 'COM_TEST'})
    assert service.snapshot()['radio_model'] == 'Unknown'
