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
from .indicator import LanIndicator, PiLanReader, LocalPanelServer, panel_path


async def run(config):
    logger = logging.getLogger('civi')
    logger.info('CIVI %s - SCPI / CI-V gateway | Author: %s', __version__, __author__)
    from .auth import PasswordStore
    credentials = PasswordStore(config,os.environ.get(config["password_env"], ""))
    config['discovery_reset_revision']=credentials.recovery_revision
    from .pi.lci import reload_recovery, local_path, write_private
    if credentials.saved:
        logger.info('Using saved Web credentials; environment password is overridden')
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(config["tls_cert"], config["tls_key"])
    profile = load_profile(config["profile"])
    backend = MockBackend(profile) if config["backend"] == "mock" else CivBackend(profile, config["serial"])
    service, discovery = ControlService(backend, config), Discovery()
    lan_manager = None
    indicator=LanIndicator(config.get('pi_network',{}).get('interface','eth0'))
    panel_server=None
    indicator_task=None
    if config.get('pi_network', {}).get('enabled'):
        if sys.platform != 'linux': raise ValueError('Pi LAN configuration requires Linux')
        from .pi.broker import BrokerClient
        lan_manager = BrokerClient(config['pi_network']['socket'])
    runner = web.AppRunner(make_web(service, credentials, discovery, lan_manager, indicator))
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
        browser_url = 'https://localhost' + (f':{config["web_port"]}' if config['web_port'] != 443 else '')
        logger.info('HTTPS listening on %s:%s | Browser: %s', config['bind'], config['web_port'], browser_url)
        logger.info('Web is ready. Radio connection runs in the background; the radio may be powered on later.')
        if config['backend'] == 'civ':
            s = config['serial']
            logging.getLogger('civi').info('Radio target: %s at %s baud; address 0x%02X; first connection check within 2 seconds',
                                           s['port'], s['baud'], s['radio_address'])
        else:
            logging.getLogger('civi').info('Mock backend enabled; no serial port will be opened')
        async def monitor_discovery():
            previous_names=None
            while True:
                changed = None
                try:
                    changed = reload_recovery(config, credentials)
                    if changed:
                        indicator.reset_faults()
                        config['discovery_reset_revision']=credentials.recovery_revision
                    if credentials.refresh_saved():
                        logger.info('Locally saved Web password loaded')
                    await discovery.refresh(config, identity(service))
                    current_names=(discovery.hostname,discovery.description)
                    if current_names!=previous_names:
                        logger.info('Discovery | mDNS hostname=%s | service name=%s',
                                    discovery.hostname or '(inactive)',discovery.description or '(inactive)')
                        previous_names=current_names
                    if changed:
                        write_private(local_path(config,'.civi-lci-applied.json'), {'revision':changed, 'error':None})
                        logger.info('Local LAN RESET credentials and discovery settings loaded')
                except Exception as e:
                    service.log(None, f'Credential/discovery refresh unavailable: {type(e).__name__}', -310)
                    if changed:
                        try: write_private(local_path(config,'.civi-lci-applied.json'), {'revision':changed, 'error':str(e)})
                        except OSError: logger.error('Could not save LAN RESET completion status')
                await asyncio.sleep(5)
        discovery_task = asyncio.create_task(monitor_discovery())
        if config.get('pi_network',{}).get('enabled'):
            reader=PiLanReader(indicator.interface,conflict_reader=lambda:lan_manager.request('conflict_status'))
            panel_server=LocalPanelServer(panel_path(config),indicator,
                lambda:{**identity(service),'radio':service.backend.state,'mdns_hostname':discovery.hostname})
            try:
                await panel_server.start()
                logger.info('Local LAN panel socket ready; open bash panel.sh on the Pi display')
            except OSError as error:
                logger.error('Local LAN panel unavailable: %s',error)
            async def monitor_lan():
                previous=None
                while True:
                    try: indicator.update(await asyncio.to_thread(reader))
                    except Exception:
                        indicator.update({'interface':indicator.interface,'error':'LAN observation failed'})
                    status=indicator.snapshot()
                    signature=(status['state'],tuple(status['addresses']),tuple(status['faults']))
                    if signature!=previous:
                        logger.info('LAN %s | %s | IPv4=%s | %s',indicator.interface,status['state'],
                            ', '.join(status['addresses']) or '(none)','; '.join(status['faults']) or 'Usable IPv4')
                        previous=signature
                    await asyncio.sleep(2)
            indicator_task=asyncio.create_task(monitor_lan())
        await asyncio.Event().wait()
    finally:
        if indicator_task:
            indicator_task.cancel(); await asyncio.gather(indicator_task,return_exceptions=True)
        if panel_server: await panel_server.close()
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
