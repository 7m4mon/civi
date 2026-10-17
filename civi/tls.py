import datetime
import ipaddress
import socket
from pathlib import Path
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID


def generate(directory, hosts):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    keypath, certpath = directory / "key.pem", directory / "cert.pem"
    if keypath.exists() or certpath.exists(): raise ValueError("Certificate exists; refusing overwrite")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "CIVI local gateway")])
    names = []
    for host in set(["localhost", "127.0.0.1", socket.gethostname(), *hosts]):
        try: names.append(x509.IPAddress(ipaddress.ip_address(host)))
        except ValueError: names.append(x509.DNSName(host))
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number()).not_valid_before(now - datetime.timedelta(minutes=5))
            .not_valid_after(now + datetime.timedelta(days=365)).add_extension(x509.SubjectAlternativeName(names), False)
            .sign(key, hashes.SHA256()))
    keypath.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
    certpath.write_bytes(cert.public_bytes(serialization.Encoding.PEM))
    return certpath, keypath
