"""Guarded operations run only against offline simulation or loopback MockBackend."""

import asyncio

import pytest


@pytest.mark.parametrize('simulation', [False, True])
async def test_operation_permissions_default_off(driver_module, driver_address, service, simulation):
    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            for call in [lambda: setattr(d.operations, 'vox_enabled', True),
                         lambda: setattr(d.operations, 'break_in', 'SEMI'),
                         lambda: setattr(d.operations, 'tuner', 'TUNE'),
                         lambda: setattr(d.operations, 'tuner', 'ON'),
                         lambda: d.operations.send_cw('CQ'), lambda: d.operations.play_voice(1),
                         lambda: setattr(d.operations, 'antenna_output_enabled', False),
                         d.operations.power_on, d.operations.power_off]:
                with pytest.raises(driver_module.DeviceError) as exc:
                    call()
                assert exc.value.errors[0].code == -203
            # STOP/OFF and local speech do not enable an RF path.
            d.operations.stop_cw()
            d.operations.stop_voice()
            d.operations.vox_enabled = False
            d.operations.break_in = 'OFF'
            d.operations.tuner = 'OFF'
            for code in range(3):
                d.operations.speak(code)
            old = d.operations.transmit_inhibited
            d.operations.transmit_inhibited = True
            assert d.operations.transmit_inhibited
            d.operations.transmit_inhibited = old
            if not simulation:
                with pytest.raises(RuntimeError):
                    d.operations.set_simulated_permissions(transmit=True)

    await asyncio.to_thread(exercise)
    assert service.owner is None and not service.backend.ptt


@pytest.mark.parametrize('simulation', [False, True])
async def test_operations_change_read_restore_and_wire(driver_module, driver_address, service, monkeypatch, simulation):
    service.config['transmit']['enabled'] = True
    service.config['permissions'].update(link=True, power=True)
    seen = []
    original = service.backend.execute_command

    def observe(spec, query, prefix, data):
        if not query:
            seen.append((prefix.hex(), data))
        return original(spec, query, prefix, data)
    monkeypatch.setattr(service.backend, 'execute_command', observe)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.operations.set_simulated_permissions(transmit=True, link=True, power=True)
            for name, values in [('vox_enabled', (True, False)), ('break_in', ('SEMI', 'FULL', 'OFF')),
                                 ('tuner', ('ON', 'TUNE', 'OFF')), ('transmit_inhibited', (True, False)),
                                 ('antenna_output_enabled', (True, False))]:
                old = getattr(d.operations, name)
                try:
                    for value in values:
                        setattr(d.operations, name, value)
                        assert getattr(d.operations, name) == value
                finally:
                    setattr(d.operations, name, old)
                assert getattr(d.operations, name) == old
            text = 'CQ, "TEST" + ^AR'
            d.operations.send_cw(text)
            if simulation:
                assert d._simulation.operations.cw_text == text
            d.operations.stop_cw()
            for slot in range(1, 9):
                d.operations.play_voice(slot)
                if simulation:
                    assert d._simulation.operations.voice_slot == slot
                d.operations.stop_voice()
            d.operations.speak(2)
            d.operations.power_off()
            d.operations.power_on()
            if simulation:
                assert d._simulation.operations.powered_on
                assert not d._simulation.operations.actions
            else:
                expected = [('1646', b'\x01'), ('1647', b'\x02'), ('1666', b'\x01'),
                            ('1c04', b'\x01'), ('1c01', b'\x02'), ('17', text.encode('ascii')),
                            ('17', b'\xff'), ('2800', b'\x08'), ('2800', b'\x00'),
                            ('13', b'\x02'), ('18', b'\x00'), ('18', b'\x01')]
                assert all(item in seen for item in expected)

    await asyncio.to_thread(exercise)
    assert service.owner is None


def test_operations_invalid_before_io(driver_module, monkeypatch):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        def no_io(*args):
            raise AssertionError('Invalid input reached I/O')
        monkeypatch.setattr(d, '_operation', no_io)
        for text in ('', 'A' * 31, 'CQ;RAD:PTT ON', 'CQ\n', 'あ', '*', 1):
            with pytest.raises((ValueError, TypeError)):
                d.operations.send_cw(text)
        for call in [lambda: d.operations.play_voice(0), lambda: d.operations.play_voice(9),
                     lambda: d.operations.play_voice(True), lambda: d.operations.speak(3),
                     lambda: setattr(d.operations, 'vox_enabled', 1),
                     lambda: setattr(d.operations, 'break_in', 'FULL;RAD:PTT ON'),
                     lambda: setattr(d.operations, 'tuner', 'TUNING'),
                     lambda: d.operations.set_simulated_permissions(transmit=1),
                     lambda: d.operations.set_simulated_permissions(max_transmit_seconds=float('nan')),
                     lambda: d.operations.set_simulated_permissions(max_transmit_seconds=0)]:
            with pytest.raises((ValueError, TypeError)):
                call()
        with pytest.raises(AttributeError):
            d.operations = None


@pytest.mark.parametrize('simulation', [False, True])
@pytest.mark.parametrize('auto_status', [False, True])
async def test_stop_attempted_despite_preexisting_errors(driver_module, driver_address, service, simulation, auto_status):
    service.config['transmit']['enabled'] = True
    def exercise():
        with driver_module.CiviIc7300(driver_address, options={
                'simulate': simulation, 'query_instrument_status': auto_status}) as d, d.checked():
            if simulation:
                d.operations.set_simulated_permissions(transmit=True)
            d.operations.vox_enabled = True
            # Use a known invalid setting: independent simulation queues -222.
            d.ivi_direct_io.write_string('RAD:ATT 10')
            with pytest.raises(driver_module.DeviceError) as exc:
                d.operations.vox_enabled = False
            assert exc.value.errors[0].code == -222
            assert not d.operations.vox_enabled
            assert d.ivi_utility.error_query() is None
    await asyncio.to_thread(exercise)
    assert service.owner is None


@pytest.mark.parametrize('failure', ['NAK', 'timeout', 'preexisting'])
async def test_operations_failure_not_success(driver_module, driver_address, service, monkeypatch, failure):
    from civi.errors import CiviError
    original = service.backend.execute_command
    seen = []
    def fail(spec, query, prefix, data):
        if spec.header == 'RAD:SPEECH':
            seen.append(data)
            raise CiviError(-200 if failure == 'NAK' else -365, 'Injected operation error')
        return original(spec, query, prefix, data)
    monkeypatch.setattr(service.backend, 'execute_command', fail)
    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            if failure == 'preexisting':
                d.ivi_direct_io.write_string('UNKNOWN')
            with pytest.raises(driver_module.DeviceError) as exc:
                d.operations.speak(0)
            assert exc.value.errors[0].code == {'NAK': -200, 'timeout': -365, 'preexisting': -113}[failure]
    await asyncio.to_thread(exercise)
    assert len(seen) == (0 if failure == 'preexisting' else 1)


@pytest.mark.parametrize('simulation', [False, True])
async def test_owned_operations_block_power_and_timeout(driver_module, driver_address, service, simulation):
    service.config['transmit']['enabled'] = True
    service.config['permissions']['power'] = True
    d = await asyncio.to_thread(driver_module.CiviIc7300, driver_address, options={'simulate': simulation, 'query_instrument_status': True})
    try:
        if simulation:
            d.operations.set_simulated_permissions(transmit=True, power=True, max_transmit_seconds=2)
            clock = [100.0]
            d._simulation.operations._clock = lambda: clock[0]
        await asyncio.to_thread(d.operations.send_cw, 'CQ')
        await asyncio.to_thread(setattr, d.operations, 'vox_enabled', True)
        with pytest.raises(driver_module.DeviceError) as exc:
            await asyncio.to_thread(d.operations.power_off)
        assert exc.value.errors[0].code == -200
        if simulation:
            clock[0] = 103.0
        else:
            service.tx_started -= service.config['transmit']['max_seconds'] + 1
        # The gateway checks expiry before a command. Simulation checks on I/O.
        assert await asyncio.to_thread(lambda: d.meters.smeter_raw) == 96
        if simulation:
            assert not d._simulation.operations.actions and d._simulation.operations.cw_text == ''
        else:
            assert service.owner is None and not service.tx_actions
        assert not await asyncio.to_thread(lambda: d.operations.vox_enabled)
        await asyncio.to_thread(d.operations.power_off)
        await asyncio.to_thread(d.operations.power_on)
    finally:
        d.close()


async def test_tcp_ownership_and_disconnect_cleanup(driver_module, driver_address, service, monkeypatch):
    service.config['transmit']['enabled'] = True
    original = service.backend.execute_command
    stops = []
    def observe(spec, query, prefix, data):
        if spec.header == 'RAD:VOICE' and not query and data == b'\x00':
            stops.append(data)
        return original(spec, query, prefix, data)
    monkeypatch.setattr(service.backend, 'execute_command', observe)
    first = await asyncio.to_thread(driver_module.CiviIc7300, driver_address, options={'query_instrument_status': True})
    second = await asyncio.to_thread(driver_module.CiviIc7300, driver_address, options={'query_instrument_status': True})
    try:
        await asyncio.to_thread(first.operations.play_voice, 1)
        with pytest.raises(driver_module.DeviceError) as exc:
            await asyncio.to_thread(second.operations.send_cw, 'CQ')
        assert exc.value.errors[0].code == -200
        first.close()
        for _ in range(50):
            if service.owner is None:
                break
            await asyncio.sleep(0.01)
        assert service.owner is None and not service.tx_actions
        assert stops
        await asyncio.to_thread(second.operations.send_cw, 'CQ')
        await asyncio.to_thread(second.operations.stop_cw)
    finally:
        first.close()
        second.close()


def test_offline_close_reset_and_permission_separation(driver_module):
    d = driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True})
    state = d._simulation.operations
    d.operations.set_simulated_permissions(transmit=True, link=True)
    assert d._simulation.menus.permissions['link']
    d.operations.antenna_output_enabled = True
    d.operations.transmit_inhibited = True
    d.operations.break_in = 'FULL'
    d.ivi_utility.reset()
    assert not state.actions and d.operations.break_in == 'OFF'
    assert d.operations.antenna_output_enabled and d.operations.transmit_inhibited
    assert state.transmit and d._simulation.menus.permissions['link']
    d.menus.set_simulated_write_permissions(link=False)
    with pytest.raises(driver_module.DeviceError) as exc:
        d.operations.antenna_output_enabled = False
    assert exc.value.errors[0].code == -203
    d.operations.send_cw('CQ')
    d.close()
    assert not state.actions and state.cw_text == ''


@pytest.mark.parametrize('auto_status', [False, True])
async def test_stop_failure_preserves_existing_and_new_errors(driver_module, driver_address, service, monkeypatch, auto_status):
    from civi.errors import CiviError
    original = service.backend.execute_command
    attempts = []
    def fail(spec, query, prefix, data):
        if spec.header == 'RAD:CW:STOP':
            attempts.append(data)
            raise CiviError(-200, 'Injected stop NAK')
        return original(spec, query, prefix, data)
    monkeypatch.setattr(service.backend, 'execute_command', fail)
    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': auto_status}) as d, d.checked():
            d.ivi_direct_io.write_string('RAD:ATT 10')
            with pytest.raises(driver_module.DeviceError) as exc:
                d.operations.stop_cw()
            assert [error.code for error in exc.value.errors] == [-222, -200]
    await asyncio.to_thread(exercise)
    assert attempts == [b'\xff']


@pytest.mark.parametrize('header,value', [('vox_enabled', 'MAYBE'), ('break_in', 'AUTO'), ('tuner', '3')])
def test_bad_operation_replies(driver_module, monkeypatch, header, value):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        monkeypatch.setattr(d, '_operation', lambda *args: value)
        with pytest.raises(driver_module.ProtocolError):
            getattr(d.operations, header)
