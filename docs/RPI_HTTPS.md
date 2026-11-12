# Raspberry Pi HTTPS on port 443

CIVI can serve HTTPS directly on 443 as the normal desktop/radio user, with 8443 as an optional compatibility listener. Both listeners share the same application, TLS certificate, authentication and radio queue. No proxy, service or automatic startup is required. The Windows example retains 8443.

## One-time installation

On Raspberry Pi OS, install `authbind` and grant only the CIVI user's access to port 443 (replace `nom` with your actual user):

```bash
sudo apt-get install authbind
sudo install -o nom -g nom -m 0500 /dev/null /etc/authbind/byport/443
```

Check for an existing rule before replacing it on a shared machine. This rule permits that user to bind port 443, for TCP or UDP; it is not restricted to the CIVI executable. Other privileged ports remain protected. CIVI and its Python interpreter receive no file capabilities and are not run as root. See the [Debian authbind manual](https://manpages.debian.org/trixie/authbind/authbind.1.en.html).

For a new Pi installation, copy `config.pi.example.toml` to `config.toml` and configure the serial device, certificates and other settings. For an existing installation, edit only these **top-level** settings:

```toml
web_port = 443
web_extra_ports = [8443]
```

Do not replace an existing configuration with the example: it contains placeholder serial settings. Restart CIVI to change its listening ports. The LAN helper and panel do not need to restart for a port change.

## Manual launch

```bash
cd ~/civi-rpi-lxi
bash start.sh
```

`start.sh` checks the configured ports against Linux's unprivileged-port threshold and uses `authbind --deep` when needed. Run this command as the normal CIVI user, without sudo. Missing permissions and occupied ports cause startup to fail; the application does not silently revert to another port. Stop with Ctrl+C.

Open `https://192.168.73.2/` or `https://civi.local/` if that is the Pi's current address/name. `/lxi` and `/network` are available on the same origin. If Avahi acquired a different name after a collision, use the advertised mDNS hostname displayed by CIVI. Port 8443 remains available when listed in `web_extra_ports`. Discovery advertises the primary port 443.

Allow inbound TCP 443 on the intended LAN interfaces if a firewall is enabled. Keep the certificate SANs aligned with the IP addresses and hostnames actually used. Moving from 8443 to 443 does not require a new certificate, but an existing certificate may already lack a renamed host. Self-signed certificates still need client trust configuration; this change does not remove browser certificate warnings.

## Undo

Set `web_port = 8443` and `web_extra_ports = []`, then restart CIVI. If the port rule was created exclusively for CIVI, remove it with `sudo rm /etc/authbind/byport/443`. No global low-port sysctl or Python executable permissions were changed.

This supplies a Pi configuration with 443 as its primary HTTPS port; it does not establish full LXI conformance. See [requirements matrix](LXI.md).
