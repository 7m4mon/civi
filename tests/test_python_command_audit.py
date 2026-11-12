"""Unified base/extended/alias inventory and new base APIs; no physical radio."""

import asyncio
from dataclasses import FrozenInstanceError
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def audit_tool():
    spec = importlib.util.spec_from_file_location('command_audit', ROOT / 'tools/python_driver_command_audit.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_complete_inventory_and_alias_directions_match_gateway_parser():
    tool = audit_tool()
    data = tool.inventory()
    rows = data['commands']
    assert len(rows) == 350
    assert {r['header'] for r in rows} == set(tool.CATALOG) | set(tool.BASE)
    assert all(r['status'] == 'mapped' for r in rows)
    for alias, handler in tool.scpi.HEADERS.items():
        assert any(alias in r['aliases'] and handler == r['handler'] for r in rows)
    for row in rows:
        for direction in row['gateway_access']:
            query = direction == 'r'
            if row['header'] in tool.CATALOG:
                public = tool.CATALOG[row['header']].public()
                argument = public['query_example' if query else 'set_example'] or None
            else:
                argument = None if query else row['sample']
            for alias in row['aliases']:
                for spelling in (alias, alias.lower(), ':' + alias.swapcase()):
                    program = spelling + ('?' if query else '') + (' ' + argument if argument is not None else '')
                    parsed = tool.scpi.parse(program)
                    assert parsed[:2] == (row['handler'], query), program


def test_unsupported_forms_are_explicitly_rejected():
    from civi.errors import CiviError
    tool = audit_tool()
    for probe, reason in tool.EXCLUSIONS:
        assert reason
        with pytest.raises(CiviError) as exc:
            tool.scpi.parse(probe)
        assert exc.value.code == -113


@pytest.mark.parametrize('simulation', [False, True])
async def test_identity_clear_completion_and_manual_firmware(driver_module, driver_address, service, simulation):
    service.config['radio_firmware'] = '1.42'
    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation}) as d:
            identity = d.ivi_utility.identification
            assert isinstance(identity, m.GatewayIdentification)
            assert (identity.manufacturer, identity.model) == ('CIVI Project', 'CIVI/IC-7300')
            assert identity.software_revision == '0.1.0'  # Gateway, not client or radio firmware.
            assert identity.serial_number == ('SIMULATED' if simulation else service.config['serial_number'])
            with pytest.raises(FrozenInstanceError):
                identity.model = 'changed'
            assert d.radio.firmware_revision == ('Unknown' if simulation else '1.42')
            d.ivi_direct_io.write_string('RAD:ATT 10')
            d.ivi_utility.wait_for_complete()  # OFF preserves error; completion is not success.
            assert d.ivi_utility.error_query().code == -222
            d.ivi_direct_io.write_string('RAD:ATT 10')
            with pytest.raises(m.DeviceError) as exc:
                with d.checked():
                    d.ivi_utility.wait_for_complete()
            assert exc.value.errors[0].code == -222
            d.ivi_direct_io.write_string('RAD:ATT 10')
            d.ivi_utility.clear_status()
            assert d.ivi_utility.error_query() is None
            with d.checked():
                d.ivi_direct_io.write_string('RAD:ATT 10')
                d.ivi_utility.clear_status()  # Explicit clear must not abort on old errors.
                assert d.ivi_utility.error_query() is None
                assert d.ivi_utility.identification.model == 'CIVI/IC-7300'
    await asyncio.to_thread(exercise)


@pytest.mark.parametrize('reply', ['CIVI,MODEL,ONLYTHREE', 'A,B,C,D,E', 'A,"unterminated,C,D', 'A,B,C,\x00'])
def test_bad_identification_replies(driver_module, monkeypatch, reply):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True}) as d:
        monkeypatch.setattr(d, '_operation', lambda *args: reply)
        with pytest.raises(driver_module.ProtocolError):
            d.ivi_utility.identification


def test_quoted_identity_and_invalid_completion(driver_module, monkeypatch):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True}) as d:
        monkeypatch.setattr(d, '_operation', lambda *args: 'CIVI Project,CIVI/IC-7300,"SER,IAL",0.1.0')
        assert d.ivi_utility.identification.serial_number == 'SER,IAL'
        monkeypatch.setattr(d, '_operation', lambda *args: '0')
        with pytest.raises(driver_module.ProtocolError):
            d.ivi_utility.wait_for_complete()


@pytest.mark.parametrize('simulation', [False, True])
async def test_ptt_explicit_start_stop_guards_and_owned_paths(driver_module, driver_address, service, simulation):
    d = await asyncio.to_thread(driver_module.CiviIc7300, driver_address, options={'simulate': simulation})
    try:
        def denied():
            with d.checked():
                with pytest.raises(driver_module.DeviceError) as exc:
                    d.operations.start_transmit()
                assert exc.value.errors[0].code == -203
                assert not d.radio.transmitting
        await asyncio.to_thread(denied)
        service.config['transmit']['enabled'] = True
        def exercise():
            if simulation:
                d.operations.set_simulated_permissions(transmit=True)
            with d.checked():
                try:
                    d.operations.vox_enabled = True
                    d.operations.send_cw('CQ')
                    d.operations.start_transmit()
                    assert d.radio.transmitting
                finally:
                    d.operations.stop_transmit()
                assert not d.radio.transmitting
                assert not d.operations.vox_enabled
                if simulation:
                    assert not d._simulation.operations.actions
                    assert d._simulation.operations.cw_text == ''
        await asyncio.to_thread(exercise)
        if not simulation:
            assert service.owner is None and not service.tx_actions
            assert not service.backend.ptt
    finally:
        d.close()


def test_ptt_offline_timeout_and_close(driver_module):
    d = driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True})
    try:
        d.operations.set_simulated_permissions(transmit=True, max_transmit_seconds=2)
        clock = [100.0]
        d._simulation.operations._clock = lambda: clock[0]
        with d.checked():
            d.operations.start_transmit()
            assert d.radio.transmitting
            clock[0] = 103.0
            assert not d.radio.transmitting
            d.operations.start_transmit()
            assert d.radio.transmitting
        d.close()
        assert d._simulation.values['RAD:PTT'] == 'OFF'
    finally:
        d.close()


async def test_clear_is_session_local_and_ptt_owner_disconnects(driver_module, driver_address, service):
    service.config['transmit']['enabled'] = True
    first = await asyncio.to_thread(driver_module.CiviIc7300, driver_address)
    second = await asyncio.to_thread(driver_module.CiviIc7300, driver_address)
    try:
        def prepare():
            first.ivi_direct_io.write_string('RAD:ATT 10')
            second.ivi_direct_io.write_string('RAD:ATT 10')
            first.ivi_utility.clear_status()
            assert first.ivi_utility.error_query() is None
            assert second.ivi_utility.error_query().code == -222
            with first.checked():
                first.operations.start_transmit()
                assert first.radio.transmitting
            with second.checked():
                with pytest.raises(driver_module.DeviceError) as exc:
                    second.operations.start_transmit()
                assert exc.value.errors[0].code == -200
        await asyncio.to_thread(prepare)
        first.close()
        for _ in range(50):
            if service.owner is None:
                break
            await asyncio.sleep(0.01)
        assert service.owner is None and not service.backend.ptt
        def acquire():
            with second.checked():
                try:
                    second.operations.start_transmit()
                    assert second.radio.transmitting
                finally:
                    second.operations.stop_transmit()
        await asyncio.to_thread(acquire)
    finally:
        first.close()
        second.close()
