"""Physical item names are local, read-only and identify addressed records."""

import asyncio

import pytest


def test_collection_names_without_io(driver_module, monkeypatch):
    with driver_module.CiviIc7300(
        'TCPIP::unused::5025::SOCKET', options={'simulate': True}
    ) as driver:
        def no_io(*args, **kwargs):
            raise AssertionError('Item identity attempted instrument I/O')

        monkeypatch.setattr(driver, '_operation', no_io)
        for key in ('SELECTED', 'OTHER'):
            assert driver.vfos[key].name == key
        for key in driver.menus:
            assert driver.menus[key].name == f'{key:04d}'
        for key in driver.memories:
            expected = {100: 'P1', 101: 'P2'}.get(key, f'{key:02d}')
            assert driver.memories[key].name == expected
        names = []
        for key in driver.keyers:
            item = driver.keyers[key]
            assert item.name == f'M{key}' and item.number == key
            names.append(item.name)
            with pytest.raises(AttributeError):
                item.name = 'OTHER'
        assert names == [f'M{i}' for i in range(1, 9)]
        driver.close()
        assert driver.keyers[8].name == 'M8'


@pytest.mark.parametrize('simulation', [False, True])
async def test_named_keyers_address_distinct_records_and_restore(
    driver_module, driver_address, service, simulation
):
    service.config['permissions']['memory'] = True

    def exercise():
        with driver_module.CiviIc7300(
            driver_address, options={'simulate': simulation}
        ) as driver, driver.checked():
            if simulation:
                driver.keyers.set_simulated_write_permission(True)
            originals = {i: driver.keyers[i].text for i in driver.keyers}
            try:
                for i in driver.keyers:
                    item = driver.keyers[i]
                    assert item.write_and_read(f'CQ {item.name}') == f'CQ M{i}'
                for i in driver.keyers:
                    assert driver.keyers[i].text == f'CQ M{i}'
            finally:
                for i, text in originals.items():
                    driver.keyers[i].text = text
            assert {i: driver.keyers[i].text for i in driver.keyers} == originals
            assert not driver.radio.transmitting

    await asyncio.to_thread(exercise)
