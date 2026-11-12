import asyncio
import copy

import pytest

from civi.errors import CiviError
from civi.scpi import parse


@pytest.mark.parametrize('text', ['RAD:RESET?', 'RAD:RESET ON', '*RST'])
def test_receive_reset_syntax(text):
    with pytest.raises(CiviError):
        parse(text)


async def test_receive_reset_known_state_and_preserves_unrelated_settings(service):
    await service.execute('test', 'RAD:VFO:SELECT B;:SENS:FREQ 14MHz;:RAD:MODE AM')
    service.backend.memory_records[12] = b'unchanged'
    saved_profile = copy.deepcopy(service.backend.profile)
    saved_config = copy.deepcopy(service.config)
    await service.execute('test', 'RAD:SPLIT ON;:RAD:RIT ON;:RAD:XIT ON;:RAD:RIT:FREQ 250')
    assert await service.execute('test', 'RAD:RESET;*OPC?;:SYST:ERR?') == '1;0,"No error"'
    assert service.backend.selected_vfo == 0
    assert not service.backend.memory_mode
    assert service.backend.vfos[0] == {'frequency': 14100000, 'mode': 1, 'data': 0, 'filter': 2}
    assert service.backend.vfos[1] == service.backend.vfos[0]
    assert service.backend.memory_records == {12: b'unchanged'}
    assert service.backend.profile == saved_profile
    assert service.config == saved_config
    assert await service.execute('test', 'RAD:SPLIT?;:RAD:RIT?;:RAD:XIT?;:RAD:RIT:FREQ?') == 'OFF;OFF;OFF;0'
    assert not service.backend.ptt
    from civi.reset import VERIFY_COMMANDS
    for header, selector, expected in VERIFY_COMMANDS:
        assert await service.execute('test', header + '?' + (' ' + selector if selector else '')) == expected


async def test_receive_reset_stops_owned_transmit_without_enabling_transmit(service):
    # Only a simulated radio is used, never physical RF.
    service.config['transmit']['enabled'] = True
    await service.execute('test', 'RAD:PTT ON')
    service.config['transmit']['enabled'] = False
    assert service.owner == 'test'
    assert await service.execute('test', 'RAD:RESET;SYST:ERR?') == '0,"No error"'
    assert service.owner is None
    assert not service.tx_actions
    assert not service.backend.ptt
    assert not service.config['transmit']['enabled']


async def test_receive_reset_fails_fast_on_nak(service, monkeypatch):
    await service.execute('test', 'SENS:FREQ 14MHz')
    original = service.backend.execute_command
    seen = []

    def reject(spec, query, prefix, data):
        seen.append(spec.header)
        if spec.header == 'RAD:VOX':
            raise CiviError(-200, 'Radio rejected command (NAK)')
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', reject)
    result = await service.execute('test', 'RAD:RESET;SYST:ERR?')
    assert result.startswith('-200,')
    assert 'RAD:VFO:SELECT' not in seen
    assert service.backend.frequency == 14000000
    assert not any('Receive reset verified' in x['message'] for x in service.logs)


async def test_receive_reset_readback_failure_is_not_success(service, monkeypatch):
    original = service.backend.execute_command

    def mismatch(spec, query, prefix, data):
        result = original(spec, query, prefix, data)
        return 'ON' if query and spec.header == 'RAD:SPLIT' else result

    monkeypatch.setattr(service.backend, 'execute_command', mismatch)
    assert (await service.execute('test', 'RAD:RESET;SYST:ERR?')).startswith('-200,')
    assert all(v is None for v in service.cache.values())


async def test_receive_reset_not_interleaved_with_other_client(service, monkeypatch):
    service.connect('other')
    original = service.backend.execute_command
    seen = []

    def observe(spec, query, prefix, data):
        seen.append(spec.header)
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', observe)
    results = await asyncio.gather(
        service.execute('test', 'RAD:RESET;SYST:ERR?'),
        service.execute('other', 'RAD:AFGAIN 128;AFGAIN?'),
    )
    assert results == ['0,"No error"', '128']
    assert seen[-2:] == ['RAD:AFGAIN', 'RAD:AFGAIN']


async def test_receive_reset_timeout_preserves_fault(service):
    service.backend.failure = 'USB disconnected'
    assert (await service.execute('test', 'RAD:RESET;SYST:ERR?')).startswith('-365,')
    assert service.backend.state == 'disconnected'
    assert not any('Receive reset verified' in x['message'] for x in service.logs)


async def test_receive_reset_skips_unowned_cw_voice_but_does_not_ignore_owned_nak(service, monkeypatch):
    original = service.backend.execute_command

    def reject(spec, query, prefix, data):
        if spec.header in ('RAD:CW:STOP', 'RAD:VOICE'):
            raise CiviError(-200, 'Idle stop NAK')
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', reject)
    assert await service.execute('test', 'RAD:RESET;SYST:ERR?') == '0,"No error"'
    service.tx_actions.add('cw')
    service.owner = 'test'
    service.tx_started = __import__('time').monotonic()
    assert (await service.execute('test', 'RAD:RESET;SYST:ERR?')).startswith('-200,')
    assert 'cw' in service.tx_actions
