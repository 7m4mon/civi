import asyncio
import copy
import importlib
from pathlib import Path
import pytest
import pytest_asyncio
from civi.config import load
from civi.backend import MockBackend, load_profile
from civi.service import ControlService
from civi.server import scpi_client


@pytest.fixture
def driver_module(monkeypatch):
    monkeypatch.syspath_prepend(str(
        Path(__file__).resolve().parents[1] / 'drivers/civi-ic7300/src'
    ))
    return importlib.import_module('civi_ic7300')


@pytest_asyncio.fixture
async def driver_address(service):
    handlers = set()

    async def client(reader, writer):
        task = asyncio.current_task()
        handlers.add(task)
        try:
            await scpi_client(reader, writer, service)
        finally:
            handlers.remove(task)

    server = await asyncio.start_server(client, '127.0.0.1', 0)
    yield f'TCPIP::127.0.0.1::{server.sockets[0].getsockname()[1]}::SOCKET'
    server.close()
    await server.wait_closed()
    if handlers:
        await asyncio.gather(*list(handlers))


@pytest.fixture
def config(tmp_path):
    value=copy.deepcopy(load("config.example.toml"))
    value['network_settings_file']=str(tmp_path/'.civi-network.json')
    return value


@pytest_asyncio.fixture
async def service(config):
    s = ControlService(MockBackend(load_profile()), config)
    s.connect("test")
    await s.start()
    yield s
    await s.close()
