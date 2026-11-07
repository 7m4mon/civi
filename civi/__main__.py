import argparse
import asyncio
import os
import logging
import sys
import ssl
from aiohttp import web
from .backend import CivBackend, MockBackend, load_profile
from .config import load
from .network import Discovery
from .server import make_web, scpi_client
from .service import ControlService
from . import __version__, __author__
from .identification import identity


async def run(config):
    logger = logging.getLogger('civi')
    logger.info('CIVI %s - SCPI / CI-V gateway | Author: %s', __version__, __author__)
    password = os.environ.get(config["password_env"], "")
    if len(password) < 12: raise ValueError("Set password environment variable to at least 12 characters")
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(config["tls_cert"], config["tls_key"])
    profile = load_profile(config["profile"])
    backend = MockBackend(profile) if config["backend"] == "mock" else CivBackend(profile, config["serial"])
    service, discovery = ControlService(backend, config), Discovery()
    lan_manager = None
    if config.get('pi_network', {}).get('enabled'):
        if sys.platform != 'linux': raise ValueError('Pi LAN configuration requires Linux')
        from .pi.broker import BrokerClient
        lan_manager = BrokerClient(config['pi_network']['socket'])
    runner = web.AppRunner(make_web(service, password, discovery, lan_manager))
    tcp = None
    discovery_task = None
    await service.start()
    try:
        tcp = await asyncio.start_server(lambda r, w: scpi_client(r, w, service), config["bind"], config["scpi_port"], limit=4096)
        await runner.setup()
        await web.TCPSite(runner, config["bind"], config["web_port"], ssl_context=context).start()
        for port in config.get('web_extra_ports', []):
            await web.TCPSite(runner, config['bind'], port, ssl_context=context).start()
            logger.info('Additional HTTPS listening on %s:%s', config['bind'], port)
        logger.info('Backend: %s | Radio profile: %s | Device ID: %s', config['backend'], profile['model'], config['serial_number'])
        logger.info('SCPI listening on %s:%s', config['bind'], config['scpi_port'])
        logger.info('HTTPS listening on %s:%s | Browser: https://localhost:%s', config['bind'], config['web_port'], config['web_port'])
        logger.info('Web is ready. Radio connection runs in the background; the radio may be powered on later.')
        if config['backend'] == 'civ':
            s = config['serial']
            logging.getLogger('civi').info('Radio target: %s at %s baud; address 0x%02X; first connection check within 2 seconds',
                                           s['port'], s['baud'], s['radio_address'])
        else:
            logging.getLogger('civi').info('Mock backend enabled; no serial port will be opened')
        async def monitor_discovery():
            while True:
                try: await discovery.refresh(config, identity(service))
                except Exception as e:
                    service.log(None, f'Discovery unavailable: {type(e).__name__}', -310)
                await asyncio.sleep(5)
        discovery_task = asyncio.create_task(monitor_discovery())
        await asyncio.Event().wait()
    finally:
        if discovery_task:
            discovery_task.cancel()
            await asyncio.gather(discovery_task, return_exceptions=True)
        if tcp: tcp.close(); await tcp.wait_closed()
        await discovery.close()
        await runner.cleanup()
        await service.close()


def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout, format='%(asctime)s %(levelname)s %(name)s: %(message)s', datefmt='%H:%M:%S')
    logging.getLogger('aiohttp.access').setLevel(logging.WARNING)
    p = argparse.ArgumentParser(description="CIVI SCPI/CI-V gateway")
    p.add_argument("--config", default="config.toml")
    p.add_argument("--make-cert", metavar="DIRECTORY")
    p.add_argument("--host", action="append", default=[], help="Certificate SAN hostname or IP")
    args = p.parse_args()
    try:
        if args.make_cert:
            from .tls import generate
            cert, key = generate(args.make_cert, args.host)
            print(f"Created {cert} and {key}")
        else: asyncio.run(run(load(args.config)))
    except KeyboardInterrupt: pass
    except (ValueError, OSError) as e: p.exit(1, f"CIVI: {e}\n")


if __name__ == "__main__": main()
