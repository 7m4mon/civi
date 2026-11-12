"""Receiver scan command acceptance, exact wire values and tone roundtrips."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest


def actions(d):
    # Expected bytes are independent CI-V constants, not imported client tables.
    return [
        *[(lambda m=mode: d.scan.start(m), '0e', bytes.fromhex(wire)) for mode, wire in
          [('PROGRAM', '02'), ('MEMORY', '22'), ('AUTO', '01'), ('DELTA', '03'),
           ('FINEPROGRAM', '12'), ('FINEDELTA', '13'), ('SELECTMEM', '23')]],
        *[(lambda s=span: d.scan.set_delta_span_hz(s), '0e', bytes.fromhex(wire)) for span, wire in
          [(5000, 'a1'), (10000, 'a2'), (20000, 'a3'), (50000, 'a4'),
           (100000, 'a5'), (500000, 'a6'), (1000000, 'a7')]],
        (lambda: d.scan.set_select_enabled(False), '0e', b'\xb0'),
        (lambda: d.scan.set_select_enabled(True), '0e', b'\xb1'),
        (lambda: d.scan.set_resume_enabled(False), '0e', b'\xd0'),
        (lambda: d.scan.set_resume_enabled(True), '0e', b'\xd3'),
        (lambda: d.scan.assign_selected_memory_group(3), '0eb1', b'\x03'),
        (lambda: d.scan.set_memory_group(2), '0eb2', b'\x02'),
        (d.scan.stop, '0e', b'\x00'),
    ]


@pytest.mark.parametrize('simulation', [False, True])
async def test_all_scan_actions(driver_module, driver_address, service, monkeypatch, simulation):
    seen = []
    original = service.backend.execute_command

    def observe(spec, query, prefix, data):
        if spec.header.startswith('RAD:SCAN:'):
            assert not query
            seen.append((prefix.hex(), data))
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', observe)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            before = d.radio.frequency_hz
            calls = actions(d)
            assert len(calls) == 21
            try:
                for call, _, _ in calls:
                    call()
                d.scan.assign_selected_memory_group(1)
                d.scan.set_memory_group(0)
                if simulation:
                    state = d._simulation.scan
                    assert state.mode is None and state.span_hz == 1000000
                    assert state.select_enabled and state.resume_enabled
                    assert state.memory_group == 0 and state.last_assigned_group == 1
                else:
                    assert seen[:21] == [(prefix, data) for _, prefix, data in calls]
                assert d.radio.frequency_hz == before  # Neither mock models scan motion.
                assert not d.radio.transmitting
            finally:
                d.scan.stop()

    await asyncio.to_thread(exercise)
    assert not service.backend.ptt


@pytest.mark.parametrize('simulation', [False, True])
async def test_tones_and_single_scope_codes(driver_module, driver_address, service, monkeypatch, simulation):
    seen = []
    original = service.backend.execute_command

    def observe(spec, query, prefix, data):
        if not query:
            seen.append((prefix.hex(), data))
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', observe)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={
                'simulate': simulation, 'query_instrument_status': True}) as d:
            for name in ('repeater_tone_hz', 'tone_squelch_hz'):
                old = getattr(d.radio, name)
                try:
                    for value in (67.0, 88.5, 100.0, 123.4, 254.1):
                        setattr(d.radio, name, value)
                        assert getattr(d.radio, name) == value
                finally:
                    setattr(d.radio, name, old)
                assert getattr(d.radio, name) == old
            for name in ('display_code', 'dual_scope_code'):
                assert getattr(d.scope, name) == 0
                setattr(d.scope, name, 0)
                assert getattr(d.scope, name) == 0
            if not simulation:
                for prefix in ('1b00', '1b01'):
                    assert (prefix, bytes.fromhex('0670')) in seen
                    assert (prefix, bytes.fromhex('1234')) in seen
                    assert (prefix, bytes.fromhex('2541')) in seen
                assert ('2712', b'\x00') in seen
                assert ('2713', b'\x00') in seen

    await asyncio.to_thread(exercise)


def test_scan_and_tone_validation_before_io(driver_module, monkeypatch):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        def no_io(*args):
            raise AssertionError('Invalid input reached I/O')
        monkeypatch.setattr(d, '_operation', no_io)
        for call in [lambda: d.scan.start('PROGRAM;RAD:PTT ON'), lambda: d.scan.start(1),
                     lambda: d.scan.set_delta_span_hz(25000), lambda: d.scan.set_delta_span_hz(True),
                     lambda: d.scan.set_select_enabled(1), lambda: d.scan.set_resume_enabled('ON'),
                     lambda: d.scan.assign_selected_memory_group(0), lambda: d.scan.set_memory_group(4)]:
            with pytest.raises((TypeError, ValueError)):
                call()
        for name in ('repeater_tone_hz', 'tone_squelch_hz'):
            for bad in (True, '88.5', 66.9, 254.2, 88.55, float('nan'), float('inf')):
                with pytest.raises((TypeError, ValueError)):
                    setattr(d.radio, name, bad)
        for name in ('display_code', 'dual_scope_code'):
            with pytest.raises(ValueError):
                setattr(d.scope, name, 1)
        with pytest.raises(AttributeError):
            d.scan = None


@pytest.mark.parametrize('reply', ['NaN', '67.01', '66.9', '254.2', '88.5;1', 'ON'])
def test_bad_tone_replies(driver_module, monkeypatch, reply):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        monkeypatch.setattr(d, '_operation', lambda *args: reply)
        with pytest.raises(driver_module.ProtocolError):
            d.radio.repeater_tone_hz


@pytest.mark.parametrize('failure', ['NAK', 'timeout', 'preexisting'])
async def test_scan_errors_with_status_checking(driver_module, driver_address, service, monkeypatch, failure):
    from civi.errors import CiviError
    original = service.backend.execute_command
    writes = []

    def fail(spec, query, prefix, data):
        if spec.header == 'RAD:SCAN:PROGRAM':
            writes.append(data)
            raise CiviError(-200 if failure == 'NAK' else -365, 'Injected scan error')
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', fail)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            if failure == 'preexisting':
                d.ivi_direct_io.write_string('UNKNOWN')
            with pytest.raises(driver_module.DeviceError) as exc:
                d.scan.start('PROGRAM')
            assert exc.value.errors[0].code == {'NAK': -200, 'timeout': -365, 'preexisting': -113}[failure]
    await asyncio.to_thread(exercise)
    assert len(writes) == (0 if failure == 'preexisting' else 1)


@pytest.mark.parametrize('simulation', [False, True])
async def test_scan_interleaved_meter_queries(driver_module, driver_address, simulation):
    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            def work(n):
                d.scan.start('PROGRAM') if n % 2 else d.scan.stop()
                return d.meters.smeter_raw
            with ThreadPoolExecutor(max_workers=5) as pool:
                assert list(pool.map(work, range(25))) == [96] * 25
            d.scan.stop()
            d.ivi_utility.reset()
            if simulation:
                assert d._simulation.scan.mode is None
    await asyncio.to_thread(exercise)
