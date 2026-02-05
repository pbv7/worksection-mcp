"""SSL/TLS utilities for OAuth2 callback server."""

import ipaddress
import logging
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

logger = logging.getLogger(__name__)


def generate_self_signed_cert(
    cert_path: Path,
    key_path: Path,
    days: int = 365,
    hostname: str = "localhost",
) -> None:
    """Generate a self-signed SSL certificate.

    Args:
        cert_path: Path to save the certificate
        key_path: Path to save the private key
        days: Certificate validity in days
        hostname: Hostname for the certificate CN and SAN
    """
    # Generate private key
    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )

    # Create certificate subject
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Local"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Local"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Worksection MCP"),
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ]
    )

    # Build certificate
    now = datetime.now(timezone.utc)
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=days))
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName(hostname),
                    x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                ]
            ),
            critical=False,
        )
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .sign(key, hashes.SHA256())
    )

    # Ensure parent directories exist
    cert_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.parent.mkdir(parents=True, exist_ok=True)

    # Write private key
    key_path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

    # Write certificate
    cert_path.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    logger.info(f"Generated self-signed certificate: {cert_path}")


def is_cert_valid(cert_path: Path, min_days_remaining: int = 30) -> bool:
    """Check if certificate exists and is not expired.

    Args:
        cert_path: Path to the certificate file
        min_days_remaining: Minimum days until expiration to consider valid

    Returns:
        True if certificate is valid and not expiring soon
    """
    if not cert_path.exists():
        return False

    try:
        cert_data = cert_path.read_bytes()
        cert = x509.load_pem_x509_certificate(cert_data)

        # Check expiration
        now = datetime.now(timezone.utc)
        expires_at = cert.not_valid_after_utc
        days_remaining = (expires_at - now).days

        if days_remaining < min_days_remaining:
            logger.info(f"Certificate expires in {days_remaining} days, needs renewal")
            return False

        return True

    except Exception as e:
        logger.warning(f"Failed to validate certificate: {e}")
        return False


def ensure_ssl_cert(
    cert_path: Path,
    key_path: Path,
    days: int = 365,
    hostname: str = "localhost",
) -> None:
    """Ensure SSL certificate exists and is valid, generating if needed.

    Args:
        cert_path: Path to the certificate file
        key_path: Path to the private key file
        days: Certificate validity in days for new certificates
        hostname: Hostname for the certificate
    """
    if is_cert_valid(cert_path):
        logger.debug(f"Using existing certificate: {cert_path}")
        return

    logger.info("Generating new self-signed SSL certificate...")
    generate_self_signed_cert(cert_path, key_path, days, hostname)


def create_ssl_context(cert_path: Path, key_path: Path) -> ssl.SSLContext:
    """Create SSL context for HTTPS server.

    Args:
        cert_path: Path to the certificate file
        key_path: Path to the private key file

    Returns:
        Configured SSL context
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile=str(cert_path), keyfile=str(key_path))
    return context
