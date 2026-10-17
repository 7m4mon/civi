import asyncio
import threading
from civi.backend import MockBackend, load_profile
from civi.service import ControlService


class BlockingBackend(MockBackend):
    def __init__(self):
        super().__init__(load_profile())
        self.entered, self.release = threading.Event(), threading.Event()
        self.in_call = False
        self.close_raced = False

    def call(self, op, value=None):
        self.in_call = True
        try:
            self.entered.set()
            if not self.release.wait(2): raise RuntimeError("test release missing")
            return super().call(op,value)
        finally: self.in_call = False

    def close(self):
        self.close_raced = self.in_call
        super().close()


async def test_opc_waits_for_backend_completion(config):
    backend=BlockingBackend()
    service=ControlService(backend,config)
    service.connect("test")
    await service.start()
    try:
        pending=asyncio.create_task(service.execute("test","SENS:FREQ 7100100;*OPC?"))
        assert await asyncio.to_thread(backend.entered.wait,1)
        assert not pending.done()
        backend.release.set()
        assert await asyncio.wait_for(pending,2)=="1"
        assert backend.frequency==7100100
    finally:
        backend.release.set()
        await service.close()


async def test_shutdown_does_not_close_serial_during_call(config):
    backend=BlockingBackend()
    service=ControlService(backend,config)
    service.connect("test")
    await service.start()
    pending=asyncio.create_task(service.execute("test","SENS:FREQ?"))
    assert await asyncio.to_thread(backend.entered.wait,1)
    closing=asyncio.create_task(service.close())
    await asyncio.sleep(0.02)
    assert not closing.done()
    backend.release.set()
    await asyncio.wait_for(closing,2)
    await pending
    assert not backend.close_raced
