"""Check actual outgoing traffic, queue preservation and scoped status policy."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

import pytest


@pytest.mark.parametrize('auto_status', [False, True])
@pytest.mark.parametrize('id_query', [False, True])
async def test_constructor_status_traffic(driver_module, driver_address, service, auto_status, id_query):
    start = len(service.logs)
    d = await asyncio.to_thread(driver_module.CiviIc7300, driver_address, id_query=id_query,
                               options={'query_instrument_status': auto_status})
    try:
        lines = [entry['message'] for entry in list(service.logs)[start:]]
        assert ('*IDN?' in lines) is id_query
        assert ('SYST:ERR?' in lines) is auto_status
    finally:
        d.close()


@pytest.mark.parametrize('simulation', [False, True])
async def test_off_has_no_automatic_error_queries_across_api(driver_module, driver_address, monkeypatch, simulation):
    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation}) as d:
            assert not d.ivi_utility.query_instrument_status_enabled
            sent = []
            original = d._send
            def trace(data):
                sent.append(data.decode('ascii'))
                return original(data)
            monkeypatch.setattr(d, '_send', trace)
            with pytest.raises(m.QueryError):
                d.scope.read_sweep()
            d.radio.frequency_hz = 14200000
            d.radio.frequency_hz
            d.menus.integer_item(2).value = 5
            record = m.MemoryRecord.simple(m.MemorySettings(7100000, 'LSB'))
            d.memories[99].write_and_read(record)
            d.memories[99].clear()
            d.band_stacks[3, 1].write_and_read(record.receive)
            d.keyers[1].write_and_read('CQ')
            d.bands.write_and_read_user(1, m.BandEdges(7000000, 7300000))
            d.scan.start('PROGRAM')
            d.scan.stop()
            d.operations.vox_enabled = True
            d.operations.vox_enabled = False
            d.operations.send_cw('CQ')
            d.operations.stop_cw()
            d.operations.play_voice(1)
            d.operations.stop_voice()
            d.operations.power_off()
            d.scope.start_stream()
            d.scope.stop_stream()
            d.ivi_utility.reset()
            with pytest.raises(m.QueryError):
                d.query('RAD:SCAN:STOP?')
            assert all('SYST:ERR' not in line.upper() for line in sent)
            assert 'RAD:RESET;*OPC?\n' in sent
            # Permission failures still exist in the gateway, and are not cleared.
            errors = d.ivi_utility.error_query_all()
            assert any(error.code == -203 for error in errors)
            assert errors[0].code == -230
            assert d.radio.frequency_hz == 14100000
    await asyncio.to_thread(exercise)


@pytest.mark.parametrize('simulation', [False, True])
async def test_checked_reports_denials_and_restores_off(driver_module, driver_address, monkeypatch, simulation):
    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation}) as d:
            for call in [lambda: setattr(d.menus.integer_item(2), 'value', 5),
                         lambda: d.bands.write_user(1, m.BandEdges(7000000, 7300000)),
                         lambda: d.operations.send_cw('CQ'),
                         lambda: d.memories[99].clear()]:
                with pytest.raises(m.DeviceError) as exc:
                    with d.checked() as checked:
                        assert checked is d
                        assert d.ivi_utility.query_instrument_status_enabled
                        call()
                assert exc.value.errors[0].code == -203
                assert not d.ivi_utility.query_instrument_status_enabled
            with pytest.raises(m.DeviceError) as exc:
                with d.checked():
                    d.scope.read_sweep()
            assert exc.value.errors[0].code == -230
            assert not d.ivi_utility.query_instrument_status_enabled
            # Explicit queue operations keep their behavior while OFF.
            d.ivi_direct_io.write_string('RAD:ATT 10')
            assert d.ivi_utility.error_query().code == -222
    await asyncio.to_thread(exercise)


def test_checked_nested_exception_and_thread_visibility(driver_module):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True}) as d:
        entered = threading.Event()
        def read_policy():
            entered.set()
            return d.ivi_utility.query_instrument_status_enabled
        with ThreadPoolExecutor(max_workers=1) as pool:
            with pytest.raises(ValueError):
                with d.checked():
                    assert d.ivi_utility.query_instrument_status_enabled
                    with d.checked():
                        assert d.ivi_utility.query_instrument_status_enabled
                    assert d.ivi_utility.query_instrument_status_enabled
                    future = pool.submit(read_policy)
                    assert entered.wait(1)
                    raise ValueError('User code failed')
            assert future.result(timeout=1) is False
        d.ivi_utility.query_instrument_status_enabled = True
        with d.checked():
            pass
        assert d.ivi_utility.query_instrument_status_enabled
    with pytest.raises(RuntimeError):
        with d.checked():
            pass


@pytest.mark.parametrize('auto_status', [False, True])
async def test_raw_query_error_preserves_queue_regardless_of_policy(driver_module, driver_address, auto_status):
    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': auto_status}) as d:
            with pytest.raises(driver_module.QueryError):
                d.query('NOPE?')
            assert d.ivi_utility.error_query().code == -113
            assert d.ivi_utility.error_query() is None
    await asyncio.to_thread(exercise)
