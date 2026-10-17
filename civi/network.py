import socket
import psutil


def network_info(port=5025):
    interfaces = []
    for name, addrs in psutil.net_if_addrs().items():
        ips = [a.address for a in addrs if a.family == socket.AF_INET]
        mac = next((a.address for a in addrs if a.family == psutil.AF_LINK), None)
        interfaces.append({"name": name, "ipv4": ips, "mac": mac,
                           "visa": [f"TCPIP0::{ip}::{port}::SOCKET" for ip in ips]})
    return {"hostname": socket.gethostname(), "interfaces": interfaces}


class Discovery:
    def __init__(self):
        self.zc, self.services = None, []

    async def start(self, config):
        from zeroconf import ServiceInfo, IPVersion
        from zeroconf.asyncio import AsyncZeroconf
        ips = [ip for i in network_info()["interfaces"] for ip in i["ipv4"] if not ip.startswith("127.")]
        if not ips: return
        self.zc = AsyncZeroconf(ip_version=IPVersion.V4Only)
        server = f'civi-{config["serial_number"].lower()}.local.'
        for service, port in (("_scpi-raw._tcp.local.", config["scpi_port"]), ("_https._tcp.local.", config["web_port"])):
            info = ServiceInfo(service, f'CIVI {config["serial_number"]}.{service}',
                               addresses=[socket.inet_aton(ip) for ip in ips], port=port, server=server,
                               properties={"model": "CIVI", "serial": config["serial_number"], "path": "/", "certified": "false"})
            await self.zc.async_register_service(info, allow_name_change=True)
            self.services.append(info)

    async def close(self):
        if self.zc:
            for s in self.services: await self.zc.async_unregister_service(s)
            await self.zc.async_close()
