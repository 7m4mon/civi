"""Full stored-record preservation and guarded mock/TCP operation tests."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest


def record(module, number=1, *, split=True):
    return module.MemoryRecord(
        module.MemorySettings(7100000 + number * 1000, 'LSB', 2, True, 'TONE', 100.0, 88.5),
        module.MemorySettings(14074000, 'FM', 3, False, 'TSQL', 67.0, 254.1),
        split, number % 4 if split else 0, f'M{number}',
    )


def test_independent_lossless_memory_vectors(driver_module):
    m = driver_module
    rx = bytes.fromhex('0000100700 00 02 11 001000 000885')
    tx = bytes.fromhex('0000200700 05 03 02 000670 002541')
    name = b'\xb1, A"; X  '
    expected = b'\x13' + rx + tx + name
    value = m.MemoryRecord(
        m.MemorySettings(7100000, 'LSB', 2, True, 'TONE', 100.0, 88.5),
        m.MemorySettings(7200000, 'FM', 3, False, 'TSQL', 67.0, 254.1),
        True, 3, 'ｱ, A"; X',
    )
    assert len(expected) == 39
    assert value.to_bytes() == expected
    assert value.receive.to_bytes() == rx
    assert value.transmit.to_bytes() == tx
    assert m.MemoryRecord.from_hex(expected.hex()) == value
    assert m.MemoryRecord.from_bytes(expected).to_bytes() == expected
    assert value.display_name == 'ｱ, A"; X'
    assert value.name.encode('cp932') == name
    # The secondary block remains intact even with Split OFF.
    nonsplit = m.MemoryRecord(value.receive, value.transmit, name='TEST')
    assert m.MemoryRecord.from_hex(nonsplit.to_hex()).transmit == value.transmit
    # The record format can read a protocol-valid frequency outside current profile writes.
    edge = m.MemorySettings(74800000, 'USB')
    assert m.MemorySettings.from_hex(edge.to_hex()) == edge


@pytest.mark.parametrize('simulation', [False, True])
async def test_all_memory_channels_band_slots_and_keyers_restore(
    driver_module, driver_address, service, simulation,
):
    service.config['permissions']['memory'] = True

    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.memories.set_simulated_write_permission(True)
            assert len(d.memories) == 101 and len(d.band_stacks) == 33 and len(d.keyers) == 8
            for number in d.memories:
                item = d.memories[number]
                if number >= 100:
                    # Disposable mocks start empty. Seed P1/P2 because the real
                    # addressed protocol cannot clear them back to empty.
                    item.record = m.MemoryRecord.simple(m.MemorySettings(14100000, 'USB'), item.name)
                old = item.record
                changed = record(m, number, split=number < 100)
                assert item.write_and_read(changed) == changed, item.name
                if old is None:
                    item.clear()
                    assert item.record is None
                else:
                    assert item.write_and_read(old) == old
            assert d.memories['P1'].number == 100 and d.memories['P2'].number == 101
            frequencies = [1850000, 3700000, 7100000, 10100000, 14100000, 18100000,
                           21100000, 24900000, 28500000, 50100000, 2500000]
            for band, slot in d.band_stacks:
                item = d.band_stacks[band, slot]
                old = item.settings
                changed = m.MemorySettings(frequencies[band - 1] + slot * 1000, 'USB', 2, True)
                assert item.write_and_read(changed) == changed
                assert item.write_and_read(old) == old
            for number in d.keyers:
                item = d.keyers[number]
                old = item.text
                changed = f'CQ, TEST {number} ^AR' + (' * ' if number == 8 else ' ')
                assert item.write_and_read(changed) == changed.rstrip()
                assert item.write_and_read(old) == old
            assert d.keyers[1].write_and_read('A' * 70) == 'A' * 70
            assert d.keyers[1].write_and_read('') == ''
            assert not d.radio.transmitting
            assert d.ivi_utility.error_query_all() == ()

    await asyncio.to_thread(exercise)


@pytest.mark.parametrize('kind', ['memory', 'stack', 'keyer'])
@pytest.mark.parametrize('failure', ['NAK', 'timeout', 'preexisting'])
async def test_storage_failure_stops_readback(driver_module, driver_address, service, monkeypatch, kind, failure):
    from civi.errors import CiviError

    service.config['permissions']['memory'] = True
    header = {'memory': 'RAD:MEM:CONTENT', 'stack': 'RAD:BAND:STACK',
              'keyer': 'RAD:KEYER:TEXT'}[kind]
    original = service.backend.execute_command
    operations = []

    def fail(spec, query, prefix, data):
        if spec.header == header:
            operations.append(query)
            if not query:
                raise CiviError(-200 if failure == 'NAK' else -365, 'Injected storage failure')
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', fail)

    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            if failure == 'preexisting':
                d.ivi_direct_io.write_string('UNKNOWN')
            with pytest.raises(m.DeviceError) as exc:
                if kind == 'memory':
                    d.memories[99].write_and_read(m.MemoryRecord.simple(m.MemorySettings(7100000, 'USB')))
                elif kind == 'stack':
                    d.band_stacks[3, 1].write_and_read(m.MemorySettings(7100000, 'USB'))
                else:
                    d.keyers[1].write_and_read('CQ')
            assert exc.value.errors[0].code == {'NAK': -200, 'timeout': -365, 'preexisting': -113}[failure]

    await asyncio.to_thread(exercise)
    assert operations == ([] if failure == 'preexisting' else [False])
    assert not service.backend.ptt
    assert not any('RAD:CW:SEND' in row['message'] for row in service.logs)


@pytest.mark.parametrize('simulation', [False, True])
async def test_selection_actions_and_reset_keep_storage(driver_module, driver_address, service, simulation):
    service.config['permissions']['memory'] = True

    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.keyers.set_simulated_write_permission(True)
            item = d.memories[12]
            value = m.MemoryRecord.simple(m.MemorySettings(7200000, 'LSB'))
            item.record = value
            d.memories.select(12)
            d.memories.enable()
            assert d.radio.frequency_hz == 7200000 and d.radio.mode == 'LSB'
            d.vfos.select('B')
            d.radio.frequency_hz = 14200000
            d.radio.mode = 'USB'
            d.memories.store_current_in_selected()
            assert item.record.receive.frequency_hz == 14200000
            d.vfos['SELECTED'].frequency_hz = 14300000
            d.memories.select(12)
            assert d.radio.frequency_hz == 14300000
            with pytest.raises(m.DeviceError) as error:
                d.memories.clear_selected()
            assert error.value.errors[0].code == -200
            assert item.record.receive.frequency_hz == 14200000
            d.memories.enable()
            assert d.radio.frequency_hz == 14200000
            d.memories.copy_selected_to_vfo()
            assert d.vfos['SELECTED'].frequency_hz == 14200000
            d.memories.clear_selected()
            assert item.record is None
            saved = record(m)
            item.record = saved
            d.band_stacks[3, 1].settings = saved.receive
            d.keyers[8].text = 'CQ, TEST ^AR *'
            d.ivi_utility.reset()
            assert item.record == saved
            assert d.band_stacks[3, 1].settings == saved.receive
            assert d.keyers[8].text == 'CQ, TEST ^AR *'
            # The memory permission is retained across receive reset.
            assert item.write_and_read(value) == value

    await asyncio.to_thread(exercise)


@pytest.mark.parametrize('simulation', [False, True])
async def test_storage_default_deny_and_menu_permission_isolation(
    driver_module, driver_address, service, simulation,
):
    service.config['permissions']['menu'] = True

    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.menus.set_simulated_write_permissions(menu=True)
            else:
                with pytest.raises(RuntimeError, match='Simulation only'):
                    d.memories.set_simulated_write_permission(True)
            for operation in (
                lambda: d.memories[1].write_and_read(record(m)),
                lambda: d.memories[1].clear(),
                lambda: d.band_stacks[3, 1].write_and_read(record(m).receive),
                lambda: d.keyers[1].write_and_read('CQ'),
                d.memories.store_current_in_selected,
                d.memories.clear_selected,
            ):
                with pytest.raises(m.DeviceError) as exc:
                    operation()
                assert exc.value.errors[0].code == -203
            assert d.memories[1].record is None

    await asyncio.to_thread(exercise)


def test_storage_invalid_values_rejected_before_io(driver_module, monkeypatch):
    m = driver_module
    with m.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        def no_io(*args):
            raise AssertionError('Invalid storage call attempted I/O')

        monkeypatch.setattr(d, '_operation', no_io)
        for build in (
            lambda: m.MemorySettings(True, 'USB'),
            lambda: m.MemorySettings(29999, 'USB'),
            lambda: m.MemorySettings(74800001, 'USB'),
            lambda: m.MemorySettings(7100000, 'NOPE'),
            lambda: m.MemorySettings(7100000, 'USB', 4),
            lambda: m.MemorySettings(7100000, 'USB', data=1),
            lambda: m.MemorySettings(7100000, 'USB', tone_mode='NOPE'),
            lambda: m.MemorySettings(7100000, 'USB', repeater_tone_hz=88.55),
            lambda: m.MemorySettings(7100000, 'USB', repeater_tone_hz=float('nan')),
            lambda: m.MemoryRecord.simple(record(m).receive, '日本語'),
            lambda: m.MemoryRecord.simple(record(m).receive, 'A' * 11),
            lambda: m.MemoryRecord.simple(record(m).receive, 'A\nB'),
        ):
            with pytest.raises((TypeError, ValueError)):
                build()
        for key in (0, 102, True, '1;RAD:PTT ON'):
            with pytest.raises((TypeError, ValueError)):
                d.memories[key]
        for key in ((0, 1), (1, 4), (True, 1), 101):
            with pytest.raises((TypeError, ValueError)):
                d.band_stacks[key]
        for key in (0, 9, True):
            with pytest.raises((TypeError, ValueError)):
                d.keyers[key]
        with pytest.raises(ValueError):
            d.memories['P1'].clear()
        with pytest.raises(ValueError):
            d.memories['P2'].record = record(m)
        with pytest.raises(TypeError):
            d.memories[1].record = None
        with pytest.raises(TypeError):
            d.band_stacks[3, 1].settings = 'BAD'
        for text in ('A' * 71, 'CQ;RAD:PTT ON', 'CQ\nTEST', '日本語'):
            with pytest.raises(ValueError):
                d.keyers[1].text = text


@pytest.mark.parametrize('kind,bad', [
    ('memory', '00'), ('memory', '0' * 78),
    ('stack', '00'), ('stack', 'FA' + '00' * 13),
    ('keyer', 'UNQUOTED'), ('keyer', '"BAD;TEXT"'),
])
def test_bad_storage_replies(driver_module, monkeypatch, kind, bad):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        monkeypatch.setattr(d, '_operation', lambda *args: bad)
        with pytest.raises(driver_module.ProtocolError):
            if kind == 'memory':
                d.memories[1].record
            elif kind == 'stack':
                d.band_stacks[3, 1].settings
            else:
                d.keyers[1].text


async def test_storage_independent_wire_vectors(driver_module, driver_address, service, monkeypatch):
    service.config['permissions']['memory'] = True
    seen = []
    original = service.backend.execute_command

    def observe(spec, query, prefix, data):
        if not query:
            seen.append((prefix.hex(), data))
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', observe)

    def exercise():
        m = driver_module
        expected_block = bytes.fromhex('0000100700010100000885000885')
        expected_record = b'\x00' + expected_block * 2 + b'TEST      '
        with m.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            value = m.MemoryRecord.simple(m.MemorySettings(7100000, 'USB'), 'TEST')
            assert d.memories[99].write_and_read(value) == value
            assert ('1a000099', expected_record) in seen
            assert d.band_stacks[3, 1].write_and_read(value.receive) == value.receive
            assert ('1a010301', expected_block) in seen
            assert d.keyers[8].write_and_read('CQ, TEST ^AR *') == 'CQ, TEST ^AR *'
            assert ('1a0208', b'CQ, TEST ^AR *'.ljust(70)) in seen
            d.memories[99].clear()
            assert ('1a000099', b'\xff') in seen

    await asyncio.to_thread(exercise)


@pytest.mark.parametrize('simulation', [False, True])
async def test_storage_concurrent_readback_and_profile_range(driver_module, driver_address, service, simulation):
    service.config['permissions']['memory'] = True

    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.memories.set_simulated_write_permission(True)
            item = d.memories[99]
            values = [record(m, n) for n in range(1, 15)]
            with ThreadPoolExecutor(max_workers=6) as pool:
                assert list(pool.map(item.write_and_read, values)) == values
            before = item.record
            unsupported = m.MemoryRecord.simple(m.MemorySettings(61000000, 'USB'))
            with pytest.raises(m.DeviceError) as exc:
                item.record = unsupported
            assert exc.value.errors[0].code == -222
            assert item.record == before

    await asyncio.to_thread(exercise)
