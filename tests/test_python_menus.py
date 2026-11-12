"""Menu API coverage, independent wire vectors, and default-deny write gates."""

import asyncio
import datetime as dt
import json
import socket
from dataclasses import FrozenInstanceError
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest


def alternate(module, definition, value):
    kind = definition.kind
    if kind == module.MenuKind.BOOLEAN:
        return not value
    if kind == module.MenuKind.INTEGER:
        return definition.maximum if value != definition.maximum else definition.minimum
    if kind == module.MenuKind.AUDIO_FILTER:
        return module.AudioFilter(1, 20)
    if kind == module.MenuKind.BANDWIDTH:
        return module.Bandwidth(2, 3)
    if kind == module.MenuKind.RGB:
        return module.RgbColor(1, 128, 255)
    if kind == module.MenuKind.SCOPE_EDGES:
        return module.ScopeEdges(value.lower_hz + 1000, value.upper_hz)
    if kind == module.MenuKind.TEXT:
        return 'TEST'
    if kind == module.MenuKind.DATE:
        return dt.date(2028, 2, 29)
    if kind == module.MenuKind.TIME:
        return dt.time(23, 59)
    return dt.timedelta(minutes=-330)


@pytest.mark.parametrize('simulation', [False, True])
async def test_all_216_reads_and_215_changed_writes_restore(
    driver_module, driver_address, service, simulation,
):
    from civi_ic7300.menus import encode

    service.config['permissions'].update(menu=True, link=True, calibration=True)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.menus.set_simulated_write_permissions(menu=True, link=True, calibration=True)
            assert len(d.menus) == 216
            assert set(d.menus) == set(range(1, 218)) - {28}
            reads = writes = 0
            for number in d.menus:
                item = d.menus[number]
                old_wire = d.query(item.definition.header + '?')
                old = item.value
                assert encode(item.definition, old) == old_wire, item.name
                reads += 1
                if item.definition.writable:
                    changed = alternate(driver_module, item.definition, old)
                    assert changed != old, item.name
                    assert item.write_and_read(changed) == changed, item.name
                    assert item.write_and_read(old) == old, item.name
                    assert d.query(item.definition.header + '?') == old_wire, item.name
                    writes += 1
                else:
                    assert number == 74
                    with pytest.raises(AttributeError):
                        item.value = old
            assert (reads, writes) == (216, 215)
            assert not d.radio.transmitting
            assert d.ivi_utility.error_query_all() == ()

    await asyncio.to_thread(exercise)
    assert not service.backend.ptt


@pytest.mark.parametrize('simulation', [False, True])
@pytest.mark.parametrize('number,value,permission', [(2, 5, 'menu'), (75, True, 'link'), (58, 200, 'calibration')])
async def test_permissions_denied_in_checked_operations(
    driver_module, driver_address, service, monkeypatch, simulation, number, value, permission,
):
    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            item = d.menus[number]
            old = item.value
            assert item.definition.permission == permission
            calls = []
            original = d._operation

            def observe(command, query):
                calls.append(command)
                return original(command, query)

            monkeypatch.setattr(d, '_operation', observe)
            with pytest.raises(driver_module.DeviceError) as exc:
                item.write_and_read(value)
            assert exc.value.errors[0].code == -203
            assert item.definition.header + '?' not in calls  # No readback after a failed write.
            assert item.value == old

    await asyncio.to_thread(exercise)
    assert not any(service.config['permissions'][p] for p in ('menu', 'link', 'calibration'))


@pytest.mark.parametrize('simulation', [False, True])
async def test_enabling_menu_does_not_enable_link_or_calibration(
    driver_module, driver_address, service, simulation,
):
    service.config['permissions']['menu'] = True

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.menus.set_simulated_write_permissions(menu=True)
            else:
                with pytest.raises(RuntimeError, match='Simulation only'):
                    d.menus.set_simulated_write_permissions(menu=True, link=True, calibration=True)
            assert d.menus.integer_item(2).write_and_read(5) == 5
            for number, value in ((75, True), (58, 200)):
                with pytest.raises(driver_module.DeviceError) as exc:
                    d.menus[number].value = value
                assert exc.value.errors[0].code == -203

    await asyncio.to_thread(exercise)


def test_menu_types_validation_and_metadata_before_io(driver_module, monkeypatch):
    def no_socket(*args, **kwargs):
        raise AssertionError('Simulation attempted network I/O')

    monkeypatch.setattr(socket, 'create_connection', no_socket)
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        def no_io(*args):
            raise AssertionError('Invalid menu call attempted I/O')

        monkeypatch.setattr(d, '_operation', no_io)
        assert d.menus['0002'].definition.minimum == 0
        assert d.menus[2].definition.maximum == 10
        assert d.menus[31].definition.step == 1000
        assert d.menus[74].definition.writable is False
        assert d.menus[74].definition.choices == ('OFF', 'ON')
        assert d.menus[2].name == '0002'
        for number in (0, 28, 218):
            with pytest.raises(KeyError):
                d.menus[number]
        for key in (True, 2.0, '0002;RAD:PTT ON', '０００２'):
            with pytest.raises(TypeError):
                d.menus[key]
        with pytest.raises(TypeError):
            d.menus.boolean_item(2)
        with pytest.raises(FrozenInstanceError):
            d.menus[2].definition.maximum = 99
        with pytest.raises(AttributeError):
            d.menus = None
        for number, value in [
            (2, True), (2, 11), (23, 1), (31, 1250), (1, '0320'), (14, b'23'),
            (91, 'lowercase'), (91, 'ABCDEFGHIJK'), (91, 'A;RAD:PTT'), (91, 'A\nB'),
            (94, dt.datetime(2028, 2, 29)), (94, dt.date(1999, 12, 31)),
            (95, dt.time(12, 30, 1)), (95, dt.time(12, 30, tzinfo=dt.timezone.utc)),
            (96, dt.timedelta(hours=14, minutes=1)), (96, dt.timedelta(seconds=1)),
        ]:
            with pytest.raises((TypeError, ValueError)):
                d.menus[number].value = value
        with pytest.raises(AttributeError):
            d.menus[74].value = True
        for build in (
            lambda: driver_module.AudioFilter(10, 5),
            lambda: driver_module.Bandwidth(4, 0),
            lambda: driver_module.RgbColor(256, 0, 0),
        ):
            with pytest.raises(ValueError):
                build()
        assert driver_module.AudioFilter(0, 25).low_pass_code == 25


@pytest.mark.parametrize('number,reply', [
    (23, 'MAYBE'), (2, '11'), (1, '2010'), (14, '4F'),
    (104, '000001280256'), (112, '001007000007'), (91, 'UNQUOTED'),
    (94, '2026-02-30'), (95, '12:99'), (96, '+14:01'), (96, '+01:60'),
])
def test_malformed_menu_reply(driver_module, monkeypatch, number, reply):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        monkeypatch.setattr(d, '_operation', lambda *args: reply)
        with pytest.raises(driver_module.ProtocolError):
            d.menus[number].value


async def test_menu_wire_vectors(driver_module, driver_address, service, monkeypatch):
    service.config['permissions'].update(menu=True, link=True, calibration=True)
    observed = {}
    original = service.backend.execute_command

    def record(spec, query, prefix, data):
        if not query and spec.header.startswith('RAD:MENU:'):
            observed[int(spec.header.rsplit(':', 1)[1])] = (prefix.hex(), data.hex())
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', record)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            cases = [
                (1, driver_module.AudioFilter(3, 20), '0320'),
                (14, driver_module.Bandwidth(2, 3), '23'),
                (104, driver_module.RgbColor(1, 128, 255), '000101280255'),
                (31, -125000, '50120001'),
                (112, driver_module.ScopeEdges(30000, 1600000), '000300006001'),
                (91, 'TEST', '54455354202020202020'),
                (94, dt.date(2028, 2, 29), '20280229'),
                (95, dt.time(23, 59), '2359'),
                (96, dt.timedelta(minutes=-330), '053001'),
                (23, True, '01'), (2, 10, '10'),
            ]
            for number, value, wire in cases:
                assert d.menus[number].write_and_read(value) == value
                assert observed[number] == ('1a05' + f'{number:04d}', wire)

    await asyncio.to_thread(exercise)


@pytest.mark.parametrize('simulation', [False, True])
async def test_menu_reset_preservation_and_operating_alias(driver_module, driver_address, service, simulation):
    service.config['permissions']['menu'] = True

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.menus.set_simulated_write_permissions(menu=True)
            d.menus.integer_item(2).value = 3
            d.menus.integer_item(81).value = 192
            assert d.gains.backlight_raw == 192
            d.gains.backlight_raw = 128
            assert d.menus[81].value == 128
            d.ivi_utility.reset()
            assert d.menus[2].value == 3
            assert d.menus[81].value == 128
            # Reset does not silently revoke simulation/gateway permissions.
            assert d.menus.integer_item(2).write_and_read(4) == 4

    await asyncio.to_thread(exercise)


def test_packaged_menu_schema_matches_gateway():
    import importlib.util

    root = Path(__file__).resolve().parents[1]
    spec = importlib.util.spec_from_file_location('menu_export', root / 'tools/python_driver_menu_catalog.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    actual = json.loads((root / 'drivers/civi-ic7300/src/civi_ic7300/menu-catalog.json').read_text())
    assert actual == json.loads(module.render())


@pytest.mark.parametrize('simulation', [False, True])
async def test_text_normalization_and_atomic_write_read(driver_module, driver_address, service, simulation):
    service.config['permissions']['menu'] = True

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.menus.set_simulated_write_permissions(menu=True)
            text = d.menus.text_item(91)
            assert text.write_and_read('TEST ') == 'TEST'
            assert text.write_and_read('') == ''
            item = d.menus.integer_item(2)
            values = [i % 11 for i in range(30)]
            with ThreadPoolExecutor(max_workers=6) as pool:
                assert list(pool.map(item.write_and_read, values)) == values

    await asyncio.to_thread(exercise)


async def test_menu_readback_returns_actual_rounded_value(driver_module, driver_address, service, monkeypatch):
    service.config['permissions']['menu'] = True
    original = service.backend.execute_command

    def round_value(spec, query, prefix, data):
        if spec.header == 'RAD:MENU:0081' and not query and data == bytes.fromhex('0128'):
            data = bytes.fromhex('0127')
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', round_value)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            assert d.menus.integer_item(81).write_and_read(128) == 127

    await asyncio.to_thread(exercise)


@pytest.mark.parametrize('failure', ['NAK', 'timeout', 'preexisting'])
async def test_menu_write_failure_not_success(driver_module, driver_address, service, monkeypatch, failure):
    from civi.errors import CiviError

    service.config['permissions']['menu'] = True
    original = service.backend.execute_command
    writes = []

    def fail(spec, query, prefix, data):
        if spec.header == 'RAD:MENU:0002' and not query:
            writes.append(data)
            if failure == 'NAK':
                raise CiviError(-200, 'Radio rejected command (NAK)')
            if failure == 'timeout':
                service.backend.state = 'disconnected'
                raise CiviError(-365, 'Serial timeout')
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', fail)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            if failure == 'preexisting':
                d.ivi_direct_io.write_string('UNKNOWN')
            with pytest.raises(driver_module.DeviceError) as exc:
                d.menus.integer_item(2).write_and_read(5)
            assert exc.value.errors[0].code == {'NAK': -200, 'timeout': -365, 'preexisting': -113}[failure]

    await asyncio.to_thread(exercise)
    assert len(writes) == (0 if failure == 'preexisting' else 1)
