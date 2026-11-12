"""Typed APIs verified against both independent simulation and the gateway mock."""

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from civi.errors import CiviError


@pytest.mark.parametrize('simulation', [False, True])
async def test_controls_vfos_and_receiver(driver_module, driver_address, simulation, service):
    def exercise():
        with driver_module.CiviIc7300(driver_address, options={
            'simulate': simulation, 'query_instrument_status': True,
        }) as d:
            d.vfos.select('A')
            d.vfos['SELECTED'].frequency_hz = 14200000
            d.vfos['SELECTED'].mode = driver_module.VfoMode('usb', True, 3)
            d.vfos['OTHER'].frequency_hz = 7040000
            d.vfos['OTHER'].mode = driver_module.VfoMode('CW', False, 1)
            assert d.radio.frequency_hz == 14200000
            assert d.vfos['SELECTED'].mode == driver_module.VfoMode('USB', True, 3)
            d.vfos.select('b')
            assert d.radio.frequency_hz == 7040000
            assert d.vfos['selected'].mode == driver_module.VfoMode('CW', False, 1)
            assert d.vfos['OTHER'].frequency_hz == 14200000
            d.vfos.copy_selected_to_other()
            assert d.vfos['OTHER'].mode == driver_module.VfoMode('CW', False, 1)
            d.vfos['OTHER'].frequency_hz = 21000000
            d.vfos.swap()
            assert d.radio.frequency_hz == 21000000
            d.vfos.enable()
            d.radio.split_enabled = True
            # The gateway's existing mock returns a canned TXFREQ value; the
            # independent client simulation derives it from its split VFO state.
            assert d.radio.tx_frequency_hz == (7040000 if simulation else 7100000)
            d.radio.rit_enabled = True
            d.radio.xit_enabled = True
            d.radio.rit_offset_hz = -1250
            assert d.radio.rit_enabled and d.radio.xit_enabled
            assert d.radio.rit_offset_hz == -1250
            d.radio.preamp = 'PRE2'
            d.radio.agc = 'slow'
            d.radio.attenuator_db = 20
            d.radio.filter_shape = 'SOFT'
            d.radio.filter_width_code = 30
            d.radio.agc_time_code = 7
            d.radio.noise_reduction_enabled = True
            assert d.radio.preamp == 'PRE2' and d.radio.agc == 'SLOW'
            assert d.radio.attenuator_db == 20 and d.radio.filter_shape == 'SOFT'
            assert d.radio.filter_width_code == 30 and d.radio.agc_time_code == 7
            assert d.radio.noise_reduction_enabled
            d.gains.af_raw = 72
            d.gains.rf_raw = 192
            d.gains.squelch_raw = 64
            d.gains.pbt_inner_raw = 128
            assert (d.gains.af_raw, d.gains.rf_raw, d.gains.squelch_raw) == (72, 192, 64)
            assert d.gains.pbt_inner_raw == 128
            assert d.meters.smeter_raw == 96
            assert 0 <= d.meters.voltage_raw <= 255
            assert isinstance(d.meters.squelch_open, bool)
            assert not d.radio.transmitting
            with ThreadPoolExecutor(max_workers=5) as pool:
                results = list(pool.map(lambda i: d.gains.af_raw if i % 2 else d.meters.smeter_raw,
                                        range(30)))
            assert results == [72 if i % 2 else 96 for i in range(30)]
            d.ivi_utility.reset()
            assert d.vfos['OTHER'].frequency_hz == d.radio.frequency_hz == 14100000
            assert d.vfos['SELECTED'].mode == driver_module.VfoMode('USB', False, 2)
            assert d.gains.af_raw == 1 and d.gains.rf_raw == 255
            assert not d.radio.split_enabled and not d.scope.streaming_enabled

    await asyncio.to_thread(exercise)
    assert not service.backend.ptt


@pytest.mark.parametrize('simulation', [False, True])
async def test_scope_units_edges_waveform(driver_module, driver_address, simulation, service):
    d = await asyncio.to_thread(driver_module.CiviIc7300, driver_address, options={'simulate': simulation, 'query_instrument_status': True})

    def configure():
        with pytest.raises(driver_module.DeviceError) as exc:
            d.scope.read_sweep()
        assert exc.value.errors[0].code == -230
        d.scope.span_hz = 25000
        d.scope.reference_db = -0.5
        assert d.scope.span_hz == 25000
        assert d.scope.reference_db == -0.5
        d.scope.mode_code = 1
        d.scope.edge_number = 2
        d.scope.hold_enabled = False
        d.scope.vbw_enabled = True
        assert d.scope.edge_number == 2 and d.scope.vbw_enabled
        d.scope.write_fixed_edges(4, 2, driver_module.ScopeEdges(7000000, 7300000))
        assert d.scope.read_fixed_edges(4, 2) == driver_module.ScopeEdges(7000000, 7300000)
        d.scope.start_stream()
        assert d.scope.enabled and d.scope.streaming_enabled

    try:
        await asyncio.to_thread(configure)
        await asyncio.sleep(0.2)  # The actual gateway mock publishes through its event loop.
        sweep = await asyncio.to_thread(d.scope.read_sweep)
        assert len(sweep.points) == 475 and all(0 <= p <= 160 for p in sweep.points)
        assert isinstance(sweep.timestamp, float)
        assert not sweep.out_of_range
        await asyncio.to_thread(d.scope.stop_stream)
        assert await asyncio.to_thread(lambda: d.scope.enabled)
        assert not await asyncio.to_thread(lambda: d.scope.streaming_enabled)
        if not simulation:
            messages = [row['message'] for row in service.logs]
            assert 'RAD:SCOPE:SPAN 0,0050020000;*OPC?' in messages
            assert 'RAD:SCOPE:REFERENCE 0,005001;*OPC?' in messages
            assert 'RAD:SCOPE:FIXEDGE 402,00000007000000300700;*OPC?' in messages
    finally:
        d.close()


def test_invalid_controls_reject_before_io(driver_module, monkeypatch):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        def no_io(*args):
            raise AssertionError('Invalid API call attempted I/O')

        monkeypatch.setattr(d, '_operation', no_io)
        for obj, name, value in [
            (d.gains, 'af_raw', 256), (d.gains, 'rf_raw', True),
            (d.radio, 'split_enabled', 1), (d.radio, 'rit_offset_hz', -10000),
            (d.radio, 'attenuator_db', 10), (d.radio, 'agc', 'FAST;RAD:PTT ON'),
            (d.radio, 'filter_width_code', -1), (d.scope, 'mode_code', 4),
            (d.scope, 'span_hz', 26000), (d.scope, 'reference_db', 0.1),
            (d.scope, 'reference_db', float('nan')),
            (d.vfos['SELECTED'], 'mode', 'USB'),
        ]:
            with pytest.raises((TypeError, ValueError)):
                setattr(obj, name, value)
        with pytest.raises(AttributeError):
            d.meters.swr_raw = 20
        with pytest.raises(AttributeError):
            d.radio.transmitting = True
        with pytest.raises(AttributeError):
            d.scope = object()
        with pytest.raises(ValueError):
            d.vfos['A']
        with pytest.raises(ValueError):
            d.vfos.select('C')
        with pytest.raises(ValueError):
            driver_module.VfoMode('USB', True, 4)
        with pytest.raises(TypeError):
            driver_module.VfoMode('USB', 1, 2)
        with pytest.raises(ValueError):
            driver_module.ScopeEdges(7300000, 7000000)
        with pytest.raises(ValueError):
            driver_module.ScopeEdges(7000001, 7300000)
        with pytest.raises(ValueError):
            d.scope.read_fixed_edges(14, 1)


@pytest.mark.parametrize('reply,access', [
    ('256', lambda d: d.gains.af_raw),
    ('MAYBE', lambda d: d.radio.split_enabled),
    ('090002', lambda d: d.vfos['OTHER'].mode),
    ('010004', lambda d: d.vfos['OTHER'].mode),
    ('0060020000', lambda d: d.scope.span_hz),
    ('205000', lambda d: d.scope.reference_db),
    ('{}', lambda d: d.scope.read_sweep()),
    (json.dumps({'mode': 0, 'frequency_1_hz': 1, 'frequency_2_hz': 2,
                 'out_of_range': False, 'points': [10], 'timestamp': 1}),
     lambda d: d.scope.read_sweep()),
])
def test_bad_typed_replies_raise_protocol_error(driver_module, monkeypatch, reply, access):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        monkeypatch.setattr(d, '_operation', lambda *args: reply)
        with pytest.raises(driver_module.ProtocolError):
            access(d)


@pytest.mark.parametrize('already_streaming', [False, True])
async def test_scope_start_failure_restores_transfer_state(
    driver_module, driver_address, service, monkeypatch, already_streaming,
):
    original = service._catalog

    async def reject(client, header, query, arg):
        if header == 'RAD:SCOPE:ENABLE' and not query and arg == '0,ON':
            raise CiviError(-200, 'NAK from scope enable')
        return await original(client, header, query, arg)

    monkeypatch.setattr(service, '_catalog', reject)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            d.scope.streaming_enabled = already_streaming
            with pytest.raises(driver_module.DeviceError):
                d.scope.start_stream()
            assert d.scope.streaming_enabled == already_streaming
            assert not d.scope.enabled

    await asyncio.to_thread(exercise)


async def test_vfo_view_follows_selection_from_another_client(driver_module, driver_address):
    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as one, driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as two:
            one.vfos.select('A')
            one.vfos['SELECTED'].frequency_hz = 7100000
            one.vfos['OTHER'].frequency_hz = 14200000
            view = one.vfos['SELECTED']
            assert view.frequency_hz == 7100000
            two.vfos.select('B')
            assert view.frequency_hz == 14200000

    await asyncio.to_thread(exercise)


def test_packaged_simulation_reset_matches_gateway_capture():
    root = Path(__file__).resolve().parents[1]
    assert json.loads((root / 'civi/profiles/ic7300-reset.json').read_text()) == json.loads(
        (root / 'drivers/civi-ic7300/src/civi_ic7300/reset-profile.json').read_text()
    )


def test_utility_contracts_are_concrete_and_references_read_only(driver_module):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        assert isinstance(d.ivi_utility, driver_module.IviUtility)
        assert isinstance(d.ivi_direct_io, driver_module.IviDirectIo)
        with pytest.raises(AttributeError):
            d.ivi_utility = None
        with pytest.raises(AttributeError):
            d.vfos = None


async def test_declared_parameters_validate_against_independent_gateway_catalog(
    driver_module, driver_address,
):
    from civi.commands import CATALOG
    from civi_ic7300.controls import Gains, Meters, ReceiverSettings, Scope, Setting

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            for interface, cls in ((d.radio, ReceiverSettings), (d.gains, Gains),
                                   (d.meters, Meters), (d.scope, Scope)):
                for name, setting in vars(cls).items():
                    if not isinstance(setting, Setting):
                        continue
                    # Every declared query must be accepted and decoded, including
                    # read-only flags and scope selectors. Gateway codecs supply
                    # independent valid values for write/read validation.
                    getattr(interface, name)
                    if setting.writable:
                        spec = CATALOG[setting.header]
                        reply = spec.codec.encode(spec.codec.sample())
                        # CI-V 1B tone requests use two bytes; replies add a zero byte.
                        if spec.codec.kind == 'tone':
                            reply = b'\x00' + reply
                        canonical = spec.codec.decode(reply)
                        expected = setting.decode(canonical)
                        setattr(interface, name, expected)
                        assert getattr(interface, name) == expected

    await asyncio.to_thread(exercise)
