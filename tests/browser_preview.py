"""Local mock-only UI fixture. Production entry point always requires HTTPS.

Run manually: python -m tests.browser_preview
No serial ports or LAN listener are used by this fixture.
"""
import asyncio
import argparse
from aiohttp import web
from civi.backend import MockBackend, load_profile
from civi.config import load
from civi.server import make_web
from civi.service import ControlService


async def main(radio_off=False):
    config = load("config.example.toml")
    config.update(backend="mock", discovery=False)
    backend = MockBackend(load_profile())
    if radio_off:
        backend.state = 'disconnected'
        backend.failure = 'Radio not ready (simulated)'
    service = ControlService(backend, config)
    await service.start()
    runner = web.AppRunner(make_web(service, "mock-ui-test-only"))
    try:
        await runner.setup()
        await web.TCPSite(runner, "127.0.0.1", 8765).start()
        print("Mock-only UI fixture http://127.0.0.1:8765", flush=True)
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
        await service.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mock-only browser test fixture')
    parser.add_argument('--radio-off', action='store_true')
    args = parser.parse_args()
    try: asyncio.run(main(args.radio_off))
    except KeyboardInterrupt: pass
