"""Exercise the separate client distribution against the real mock SCPI server."""

import asyncio
import socket
from concurrent.futures import ThreadPoolExecutor

import pytest

from civi.server import scpi_client


def test_simulation_performs_no_network_io(driver_module, monkeypatch):
    def no_socket(*args, **kwargs):
        raise AssertionError("simulation attempted network I/O")

    monkeypatch.setattr(socket, "create_connection", no_socket)
    with driver_module.CiviIc7300(
        "TCPIP::nonexistent.invalid::5025::SOCKET", options="simulate=true"
    ) as driver:
        assert driver.ivi_utility.simulation_enabled
        assert driver.ivi_utility.instrument_model == "CIVI/IC-7300"
        driver.radio.frequency_hz = 14000000
        driver.radio.mode = "am"
        assert driver.radio.frequency_hz == 14000000
        assert driver.radio.mode == "AM"
        assert driver.radio.smeter_raw == 96
        driver.ivi_direct_io.write_string("*IDN?")
        assert driver.ivi_direct_io.read_bytes().endswith(b"\n")
        assert driver.ivi_utility.error_query() is None
        driver.radio.split_enabled = True
        driver.vfos['OTHER'].frequency_hz = 7200000
        driver.gains.rf_raw = 100
        assert driver.radio.split_enabled and driver.radio.tx_frequency_hz == 7200000
        assert driver.gains.rf_raw == 100
        driver.scope.start_stream()
        assert len(driver.scope.read_sweep().points) == 475
        driver.scope.stop_stream()
        driver.ivi_utility.reset()
        assert driver.radio.frequency_hz == 14100000
        assert driver.radio.mode == "USB"
        with pytest.raises(NotImplementedError):
            driver.query("UNKNOWN?")
    with pytest.raises(RuntimeError, match="closed"):
        driver.query("*IDN?")


@pytest.mark.parametrize("resource", [
    "TCPIP::localhost::inst0::SOCKET", "TCPIPx::localhost::5025::SOCKET",
    "TCPIP::localhost::0::SOCKET", "TCPIP::localhost::65536::SOCKET",
])
def test_invalid_address(driver_module, resource):
    with pytest.raises(ValueError):
        driver_module.CiviIc7300(resource, options={"simulate": True})


def test_reject_options_before_connecting(driver_module, monkeypatch):
    def no_socket(*args, **kwargs):
        raise AssertionError("invalid initialization attempted I/O")

    monkeypatch.setattr(socket, "create_connection", no_socket)
    address = "TCPIP0::localhost::5025::SOCKET"
    for options in ({"simulate": "false"}, {"unknown": True}, "simulate=maybe"):
        with pytest.raises((ValueError, TypeError)):
            driver_module.CiviIc7300(address, options=options)
    with driver_module.CiviIc7300(address, reset=True, options={"simulate": True}) as driver:
        assert driver.radio.frequency_hz == 14100000


async def test_real_mock_server_controls_errors_threads(service, driver_module):
    handlers = set()

    async def client(reader, writer):
        task = asyncio.current_task()
        handlers.add(task)
        try:
            await scpi_client(reader, writer, service)
        finally:
            handlers.remove(task)

    server = await asyncio.start_server(client, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    def exercise():
        with driver_module.CiviIc7300(
            f"TCPIP0::127.0.0.1::{port}::SOCKET",
            options={"query_instrument_status": True},
        ) as driver:
            assert driver.ivi_utility.instrument_manufacturer == "CIVI Project"
            driver.radio.frequency_hz = 14200000
            driver.radio.mode = "CW"
            assert driver.radio.frequency_hz == 14200000
            assert driver.radio.mode == "CW"
            with ThreadPoolExecutor(max_workers=6) as pool:
                results = list(pool.map(lambda _: driver.radio.smeter_raw, range(30)))
            assert results == [96] * 30
            with pytest.raises(driver_module.QueryError):
                driver.query("NOPE?")
            assert driver.ivi_utility.error_query().code == -113
            assert driver.ivi_utility.error_query_all() == ()
            driver.ivi_direct_io.write_string("SENS:FREQ 100MHz;*OPC?")
            assert driver.ivi_direct_io.read_string() == "1"
            with pytest.raises(driver_module.DeviceError) as exc:
                driver.ivi_utility.raise_on_device_error()
            assert exc.value.errors[0].code == -222
            assert driver.radio.frequency_hz == 14200000
            for value in (True, float("nan"), 1, 60000001, 7100000.5):
                with pytest.raises((ValueError, TypeError)):
                    driver.radio.frequency_hz = value
            with pytest.raises(ValueError):
                driver.radio.mode = "USB;RAD:PTT ON"
            with pytest.raises(ValueError):
                driver.ivi_direct_io.write_string("*IDN?\nRAD:PTT ON")
            driver.ivi_direct_io.io_timeout_ms = 1000
            assert driver.ivi_direct_io.io_timeout_ms == 1000
            driver.ivi_utility.query_instrument_status_enabled = False
            driver.ivi_utility.reset()
            assert driver.radio.frequency_hz == 14100000
            assert driver.radio.mode == "USB"
            assert driver.ivi_direct_io.io_timeout_ms == 1000
            driver.radio.frequency_hz = 14000000
            driver.ivi_direct_io.write_string("NOPE")
            # Existing errors abort the reset before it changes anything.
            with pytest.raises(driver_module.DeviceError), driver.checked():
                driver.ivi_utility.reset()
            assert driver.radio.frequency_hz == 14000000
            assert driver.ivi_direct_io.io_timeout_ms == 1000
            with pytest.raises(ValueError):
                driver.ivi_utility.reset(timeout_ms=0)


    try:
        await asyncio.to_thread(exercise)
    finally:
        server.close()
        await server.wait_closed()
        if handlers:
            await asyncio.gather(*list(handlers))
    assert not service.backend.ptt


async def test_timeout_closes_session_and_discards_late_reply(driver_module):
    async def stall(reader, writer):
        await reader.readline()
        await asyncio.sleep(0.08)
        writer.write(b"late\n")
        try:
            await writer.drain()
        except ConnectionError:
            pass
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(stall, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]

    def exercise():
        with driver_module.CiviIc7300(
            f"TCPIP::127.0.0.1::{port}::SOCKET", id_query=False, timeout_ms=20
        ) as driver:
            with pytest.raises(TimeoutError):
                driver.query("*IDN?")
            with pytest.raises(RuntimeError, match="closed"):
                driver.query("*IDN?")

    try:
        await asyncio.to_thread(exercise)
        await asyncio.sleep(0.1)
    finally:
        server.close()
        await server.wait_closed()
