"""Band records, calibration permissions, DATA asymmetry and IP+ alias tests."""

import asyncio
from concurrent.futures import ThreadPoolExecutor

import pytest


def test_empty_user_slot_is_not_a_band_record(driver_module, monkeypatch):
    m = driver_module
    with m.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True}) as d:
        d._simulation.bands.users[17] = None
        assert d.bands.read_user(17) is None
        with pytest.raises(TypeError):
            d.bands.write_user(17, None)
        monkeypatch.setattr(d, '_operation', lambda *args: 'FF')
        assert d.bands.read_user(17) is None
        with pytest.raises(m.ProtocolError):
            d.bands.read_factory(17)
        with pytest.raises(ValueError):
            m.BandEdges.from_hex('FF')


def test_band_and_data_independent_vectors(driver_module):
    m = driver_module
    edges = m.BandEdges(7100000, 7200000)
    assert edges.to_hex() == '00001007002D0000200700'
    assert m.BandEdges.from_hex(edges.to_hex()) == edges
    assert m.BandEdges(0, 74800000).to_hex() == '00000000002D0000807400'
    assert m.DataFilter(True, 3).to_write_hex() == '0103'
    assert m.DataFilter(False, 0).to_write_hex() == '0000'
    assert m.DataFilter.from_hex('0003') == m.DataFilter(False, 3)
    with pytest.raises(ValueError):
        m.DataFilter.from_hex('0003').to_write_hex()


@pytest.mark.parametrize('simulation', [False, True])
async def test_band_reads_all_selectors_change_read_restore(driver_module, driver_address, service, simulation):
    service.config['permissions']['calibration'] = True

    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.bands.set_simulated_calibration_permission(True)
            assert d.bands.default_edges == m.BandEdges(7100000, 7200000)
            # Counts are canned zero in both mocks; index tests verify the codec,
            # not the existence of 30 physical bands in a radio-region plan.
            assert d.bands.factory_count == d.bands.user_count == 0
            for index in range(1, 31):
                assert d.bands.read_factory(index) == d.bands.default_edges
                old = d.bands.read_user(index)
                changed = m.BandEdges(7000000 + index, 7300000 + index)
                try:
                    assert d.bands.write_and_read_user(index, changed) == changed
                finally:
                    d.bands.write_user(index, old)
                assert d.bands.read_user(index) == old
            special = m.BandEdges(0, 74800000)
            old = d.bands.read_user(30)
            try:
                assert d.bands.write_and_read_user(30, special) == special
                d.ivi_utility.reset()
                assert d.bands.read_user(30) == special
            finally:
                d.bands.write_user(30, old)
            assert not d.radio.transmitting

    await asyncio.to_thread(exercise)
    assert not service.backend.ptt


@pytest.mark.parametrize('simulation', [False, True])
async def test_calibration_gate_shared_but_other_permissions_independent(driver_module, driver_address, service, simulation):
    service.config['permissions'].update(menu=True, memory=True, link=True)

    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.menus.set_simulated_write_permissions(menu=True, link=True)
                d.memories.set_simulated_write_permission(True)
            else:
                with pytest.raises(RuntimeError):
                    d.bands.set_simulated_calibration_permission(True)
            with pytest.raises(m.DeviceError) as exc:
                d.bands.write_user(1, m.BandEdges(7000000, 7300000))
            assert exc.value.errors[0].code == -203
            if simulation:
                d.bands.set_simulated_calibration_permission(True)
                assert d._simulation.menus.permissions == {'menu': True, 'link': True, 'calibration': True}
                d.menus.integer_item(58).write_and_read(200)
                d.bands.write_user(1, m.BandEdges(7000000, 7300000))
                d.menus.set_simulated_write_permissions(menu=True)
                with pytest.raises(m.DeviceError):
                    d.bands.write_user(1, m.BandEdges(7000000, 7300000))

    await asyncio.to_thread(exercise)


@pytest.mark.parametrize('simulation', [False, True])
async def test_data_ipplus_and_wire(driver_module, driver_address, service, monkeypatch, simulation):
    seen = []
    original = service.backend.execute_command

    def observe(spec, query, prefix, data):
        if not query:
            seen.append((prefix.hex(), data))
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', observe)

    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            old_vfo = d.vfos['SELECTED'].mode
            old_data = d.radio.data_filter
            old_ip = d.radio.ip_plus_enabled
            try:
                for number in (1, 2, 3):
                    value = m.DataFilter(True, number)
                    d.radio.data_filter = value
                    assert d.radio.data_filter == value
                    if simulation:
                        assert d.vfos['SELECTED'].mode.data
                        assert d.vfos['SELECTED'].mode.filter_number == number
                d.radio.data_filter = m.DataFilter(False, 0)
                assert not d.radio.data_filter.enabled
                assert d.radio.data_filter.filter_number == (3 if simulation else 0)
                d.radio.ip_plus_alternate_enabled = True
                assert d.radio.ip_plus_enabled and d.radio.ip_plus_alternate_enabled
                d.radio.ip_plus_enabled = False
                assert not d.radio.ip_plus_alternate_enabled
                if not simulation:
                    assert ('1a06', b'\x01\x03') in seen
                    assert ('1a06', b'\x00\x00') in seen
                    assert ('1a07', b'\x01') in seen
            finally:
                if not simulation:
                    d.radio.data_filter = old_data
                d.vfos['SELECTED'].mode = old_vfo
                d.radio.ip_plus_enabled = old_ip
            assert d.radio.data_filter == old_data
            assert d.vfos['SELECTED'].mode == old_vfo

    await asyncio.to_thread(exercise)


async def test_band_exact_wire(driver_module, driver_address, service, monkeypatch):
    service.config['permissions']['calibration'] = True
    original = service.backend.execute_command
    seen = []

    def observe(spec, query, prefix, data):
        seen.append((spec.header, query, prefix.hex(), data.hex()))
        return original(spec, query, prefix, data)

    monkeypatch.setattr(service.backend, 'execute_command', observe)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            d.bands.default_edges
            d.bands.factory_count
            d.bands.user_count
            d.bands.read_factory(30)
            d.bands.write_and_read_user(12, driver_module.BandEdges(7100000, 7200000))
    await asyncio.to_thread(exercise)
    assert ('RAD:BAND:EDGES', True, '02', '') in seen
    assert ('RAD:TXBAND:COUNT', True, '1e00', '') in seen
    assert ('RAD:TXBAND:USERCOUNT', True, '1e02', '') in seen
    assert ('RAD:TXBAND:READ', True, '1e0130', '') in seen
    assert ('RAD:TXBAND:USER', False, '1e0312', '00001007002d0000200700') in seen
    assert ('RAD:TXBAND:USER', True, '1e0312', '') in seen


def test_invalid_band_and_data_before_io(driver_module, monkeypatch):
    m = driver_module
    for args in ((True, 10), (-1, 10), (20, 10), (0, 74800001)):
        with pytest.raises((TypeError, ValueError)):
            m.BandEdges(*args)
    for args in ((1, 1), (True, 0), (False, 4), (True, True)):
        with pytest.raises((TypeError, ValueError)):
            m.DataFilter(*args)
    with m.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        def no_io(*args):
            raise AssertionError('Invalid input reached I/O')
        monkeypatch.setattr(d, '_operation', no_io)
        for index in (0, 31, True, '1;RAD:PTT ON'):
            with pytest.raises((TypeError, ValueError)):
                d.bands.read_factory(index)
            with pytest.raises((TypeError, ValueError)):
                d.bands.write_user(index, m.BandEdges(0, 0))
        with pytest.raises(TypeError):
            d.bands.write_user(1, 'bad')
        with pytest.raises(ValueError):
            d.radio.data_filter = m.DataFilter(False, 2)
        with pytest.raises(TypeError):
            d.radio.data_filter = '0101'
        with pytest.raises(AttributeError):
            d.bands = None


@pytest.mark.parametrize('kind,reply', [
    ('edge', '0000100700000000200700'), ('edge', 'FA001007002D0000200700'),
    ('edge', '00002007002D0000100700'), ('edge', '00'),
    ('count', '31'), ('count', '-1'), ('count', '1.0'),
    ('data', '0100'), ('data', '0004'), ('data', '0201'), ('data', '0001;1'),
])
def test_bad_band_and_data_replies(driver_module, monkeypatch, kind, reply):
    with driver_module.CiviIc7300('TCPIP::unused::5025::SOCKET', options={'simulate': True, 'query_instrument_status': True}) as d:
        monkeypatch.setattr(d, '_operation', lambda *args: reply)
        with pytest.raises(driver_module.ProtocolError):
            if kind == 'edge':
                d.bands.read_user(1)
            elif kind == 'count':
                d.bands.factory_count
            else:
                d.radio.data_filter


@pytest.mark.parametrize('failure', ['NAK', 'timeout', 'preexisting'])
async def test_band_write_errors_stop_readback(driver_module, driver_address, service, monkeypatch, failure):
    from civi.errors import CiviError
    service.config['permissions']['calibration'] = True
    original = service.backend.execute_command
    seen = []

    def fail(spec, query, prefix, data):
        if spec.header == 'RAD:TXBAND:USER':
            seen.append(query)
            if not query:
                raise CiviError(-200 if failure == 'NAK' else -365, 'Injected band failure')
        return original(spec, query, prefix, data)
    monkeypatch.setattr(service.backend, 'execute_command', fail)

    def exercise():
        with driver_module.CiviIc7300(driver_address, options={'query_instrument_status': True}) as d:
            if failure == 'preexisting':
                d.ivi_direct_io.write_string('UNKNOWN')
            with pytest.raises(driver_module.DeviceError) as exc:
                d.bands.write_and_read_user(1, driver_module.BandEdges(7000000, 7300000))
            assert exc.value.errors[0].code == {'NAK': -200, 'timeout': -365, 'preexisting': -113}[failure]
    await asyncio.to_thread(exercise)
    assert seen == ([] if failure == 'preexisting' else [False])


@pytest.mark.parametrize('simulation', [False, True])
async def test_band_concurrent_readback(driver_module, driver_address, service, simulation):
    service.config['permissions']['calibration'] = True
    def exercise():
        m = driver_module
        with m.CiviIc7300(driver_address, options={'simulate': simulation, 'query_instrument_status': True}) as d:
            if simulation:
                d.bands.set_simulated_calibration_permission(True)
            old = d.bands.read_user(1)
            values = [m.BandEdges(7000000 + n, 7300000 + n) for n in range(20)]
            try:
                with ThreadPoolExecutor(max_workers=5) as pool:
                    assert list(pool.map(lambda v: d.bands.write_and_read_user(1, v), values)) == values
            finally:
                d.bands.write_user(1, old)
    await asyncio.to_thread(exercise)
