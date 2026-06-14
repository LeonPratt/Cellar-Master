from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
from pathlib import Path
import os
from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

base = Path(os.environ.get("PEM_PATH") or ROOT_DIR / "pem")
base.mkdir(exist_ok=True)

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, 'UK'),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, 'Cambridgeshire'),
    x509.NameAttribute(NameOID.LOCALITY_NAME, 'Cambridge'),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, 'Vinum'),
    x509.NameAttribute(NameOID.COMMON_NAME, 'localhost'),
])
cert = (
    x509.CertificateBuilder()
    .subject_name(subject)
    .issuer_name(issuer)
    .public_key(key.public_key())
    .serial_number(x509.random_serial_number())
    .not_valid_before(datetime.utcnow() - timedelta(days=1))
    .not_valid_after(datetime.utcnow() + timedelta(days=3650))
    .add_extension(x509.SubjectAlternativeName([x509.DNSName('localhost')]), critical=False)
    .sign(key, hashes.SHA256())
)

with open(base / "cert.pem", 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))
with open(base / "key.pem", 'wb') as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))
