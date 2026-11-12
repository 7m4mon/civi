"""Nested band/slot views preserve flat API, selectors, permissions and locking."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest


def test_nested_metadata_legacy_iteration_and_validation_without_io(driver_module, monkeypatch):
    m = driver_module
    with m.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True}) as d:
        def no_io(*args):
            raise AssertionError('Resolving collection metadata attempted I/O')
        monkeypatch.setattr(d, '_operation', no_io)
        assert len(d.band_stacks) == 33
        assert list(d.band_stacks) == [(b, s) for b in range(1, 12) for s in range(1, 4)]
        bands = d.band_stacks.bands
        assert isinstance(bands, m.BandStackBandCollection)
        assert len(bands) == 11 and list(bands) == list(range(1, 12))
        for b in bands:
            band = d.band_stacks[b]
            assert band is bands[b]
            assert isinstance(band, m.BandStackBand)
            assert band.name == str(b) and band.number == b
            assert band.slots is band.slots
            assert isinstance(band.slots, m.BandStackSlotCollection)
            assert band.slots.band == b
            assert len(band.slots) == 3 and list(band.slots) == [1, 2, 3]
            for s in band.slots:
                item = band.slots[s]
                assert item is d.band_stacks[b, s]
                assert isinstance(item, m.BandStackItem)
                assert (item.band, item.slot, item.name) == (b, s, str(s))
        for bad in (0, 12, True, 3.0, '3', None):
            with pytest.raises((TypeError, ValueError)):
                bands[bad]
            with pytest.raises((TypeError, ValueError)):
                d.band_stacks[bad]
        for bad in (0, 4, True, 1.0, '1', (1, 2)):
            with pytest.raises((TypeError, ValueError)):
                bands[3].slots[bad]
        for bad in ((1,), (1, 2, 3), (True, 1), (3, False), ('3', 1), (3, '1')):
            with pytest.raises((TypeError, ValueError)):
                d.band_stacks[bad]
        for obj, key in [(d.band_stacks, 'bands'), (bands[3], 'slots'),
                         (bands[3], 'number'), (bands[3], 'name'),
                         (bands[3].slots[1], 'name'), (bands[3].slots, 'band')]:
            with pytest.raises(AttributeError):
                setattr(obj, key, None)


@pytest.mark.parametrize('simulation', [False, True])
async def test_all_nested_slots_flat_roundtrip_and_restore(driver_module, driver_address, service, monkeypatch, simulation):
    service.config['permissions']['memory'] = True
    seen = []
    original = service.backend.execute_command
    def observe(spec, query, prefix, data):
        if spec.header == 'RAD:BAND:STACK' and not query:
            seen.append((prefix.hex(), data.hex()))
        return original(spec, query, prefix, data)
    monkeypatch.setattr(service.backend, 'execute_command', observe)
    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation}) as d, d.checked():
            if simulation:
                d.band_stacks[3].slots.set_simulated_write_permission(True)
            for b in d.band_stacks.bands:
                for s in d.band_stacks[b].slots:
                    item = d.band_stacks[b].slots[s]
                    old = d.band_stacks[b, s].settings
                    value = m.MemorySettings(7100000 + b * 10000 + s * 10, 'USB',
                                             s, True, 'TONE', 100.0, 88.5)
                    try:
                        assert item.write_and_read(value) == value
                        assert d.band_stacks[b, s].settings == value
                        d.band_stacks[b, s].settings = old
                        assert d.band_stacks.bands[b].slots[s].settings == old
                    finally:
                        item.settings = old
            item = d.band_stacks[3].slots[2]
            old = item.settings
            try:
                item.settings = m.MemorySettings(7100000, 'USB', 2)
                if not simulation:
                    assert ('1a010302', '0000100700010200000885000885') in seen
            finally:
                d.band_stacks[3, 2].settings = old
            assert not d.radio.transmitting
    await asyncio.to_thread(exercise)


@pytest.mark.parametrize('simulation', [False, True])
async def test_nested_permission_and_status_policy(driver_module, driver_address, monkeypatch, simulation):
    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation}) as d:
            item = d.band_stacks[3].slots[1]
            old = item.settings
            value = m.MemorySettings(7200000, 'USB')
            sent = []
            original = d._send
            def trace(data):
                sent.append(data.decode())
                return original(data)
            monkeypatch.setattr(d, '_send', trace)
            item.settings = value
            assert d.band_stacks[3, 1].settings == old
            assert all('SYST:ERR' not in line for line in sent)
            assert d.ivi_utility.error_query().code == -203
            with pytest.raises(m.DeviceError) as exc:
                with d.checked():
                    item.settings = value
            assert exc.value.errors[0].code == -203
            assert not d.ivi_utility.query_instrument_status_enabled
            assert item.settings == old
    await asyncio.to_thread(exercise)


def test_nested_view_cannot_access_closed_session(driver_module):
    d = driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True})
    item = d.band_stacks[3].slots[1]
    d.close()
    assert item.name == '1'  # Local identity stays available; settings never come from a cache.
    with pytest.raises(RuntimeError):
        item.settings
    with pytest.raises(RuntimeError):
        item.settings = driver_module.MemorySettings(7100000, 'USB')


@pytest.mark.parametrize('simulation', [False, True])
async def test_nested_and_flat_threads_share_session_lock(driver_module, driver_address, service, simulation):
    service.config['permissions']['memory'] = True
    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={
                'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.band_stacks.set_simulated_write_permission(True)
            old = d.band_stacks[3, 1].settings
            values = [m.MemorySettings(7100000 + n * 10, 'USB') for n in range(20)]
            def write(pair):
                n, value = pair
                item = d.band_stacks[3, 1] if n % 2 else d.band_stacks.bands[3].slots[1]
                return item.write_and_read(value)
            try:
                with ThreadPoolExecutor(max_workers=5) as pool:
                    assert list(pool.map(write, enumerate(values))) == values
            finally:
                d.band_stacks[3].slots[1].settings = old
    await asyncio.to_thread(exercise)
