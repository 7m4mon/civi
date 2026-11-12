"""Empty displayed memory is missing data, not a lost CI-V connection."""
import pytest


async def test_empty_memory_poll_keeps_connection_and_scpi_reports_no_data(service, monkeypatch):
    original = service.backend.call
    empty = True
    def call(op, value=None):
        if empty and op in ('frequency_get', 'mode_get'):
            service.backend.state = 'connected'
            return None
        return original(op, value)
    monkeypatch.setattr(service.backend, 'call', call)
    service.cache.update(frequency=7100000, mode='USB')
    await service._submit(None, 'poll', None)
    status = service.snapshot()
    assert status['connection'] == 'connected'
    assert status['values']['frequency'] is status['values']['mode'] is None
    assert status['unavailable_values'] == ['frequency', 'mode']
    assert status['values']['ptt'] is False
    assert status['radio_model'] != 'Unknown'
    for command in ['SENS:FREQ?', 'RAD:MODE?']:
        assert await service._submit('test', 'scpi', command) == 'ERROR'
        error = await service._submit('test', 'scpi', 'SYST:ERR?')
        assert error.startswith('-230,') and 'empty memory' in error
        assert service.backend.state == 'connected'
    empty = False
    await service._submit(None, 'poll', None)
    status = service.snapshot()
    assert status['values']['frequency'] is not None
    assert status['values']['mode'] is not None
    assert status['unavailable_values'] == []
    assert await service._submit('test', 'scpi', 'SYST:ERR?') == '0,"No error"'
