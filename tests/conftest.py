import copy
import pytest
import pytest_asyncio
from civi.config import load
from civi.backend import MockBackend, load_profile
from civi.service import ControlService


@pytest.fixture
def config():
    return copy.deepcopy(load("config.example.toml"))


@pytest_asyncio.fixture
async def service(config):
    s = ControlService(MockBackend(load_profile()), config)
    s.connect("test")
    await s.start()
    yield s
    await s.close()
