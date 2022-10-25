from shinkansen import jws
from cryptography import x509
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives import serialization

import datetime
import pytest


@pytest.fixture
def certificate_and_key_pem_files(tmp_path):
    """
    Returns a tuple of file paths with certificate and key file. The key file
    is encrypted with the password b"test-password".
    """
    certificate_file = tmp_path / "cert.pem"
    key_file = tmp_path / "key.pem"
    key = new_rsa_key()
    certificate = new_certificate(key)
    with open(key_file, "wb") as f:
        f.write(
            key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.TraditionalOpenSSL,
                encryption_algorithm=serialization.BestAvailableEncryption(
                    b"test-password"
                ),
            )
        )
    with open(certificate_file, "wb") as f:
        f.write(certificate.public_bytes(serialization.Encoding.PEM))
    return (certificate_file, key_file)


def new_rsa_key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def new_certificate(key: rsa.RSAPrivateKey) -> x509.Certificate:
    return (
        x509.CertificateBuilder()
        .subject_name(
            x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "localhost")])
        )
        .issuer_name(
            x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "localhost")])
        )
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .sign(key, SHA256())
    )


def test_jws_sign_returns_detached_signature():
    key = new_rsa_key()
    certificate = new_certificate(key)
    signature = jws.sign("test", key, certificate)
    assert ".." in signature


def test_jws_sign_mismatched_key():
    key = new_rsa_key()
    wrong_key = new_rsa_key()
    certificate = new_certificate(key)
    with pytest.raises(jws.KeyMismatch):
        jws.sign("test", wrong_key, certificate)


def test_verify_detached_valid_signature():
    key = new_rsa_key()
    certificate = new_certificate(key)
    signature = jws.sign("test", key, certificate)
    jws.verify_detached("test", signature, [certificate])


def test_verify_invalid_signature_content_changed():
    key = new_rsa_key()
    certificate = new_certificate(key)
    signature = jws.sign("test", key, certificate)
    with pytest.raises(jws.InvalidSignature):
        jws.verify_detached("modifiedtest", signature, [certificate])


def test_verify_invalid_signature_jws_changed():
    key = new_rsa_key()
    certificate = new_certificate(key)
    signature = jws.sign("test", key, certificate)
    with pytest.raises(jws.InvalidSignature):
        jws.verify_detached("test", signature + "x", [certificate])


def test_verify_non_whitelisted_certificate():
    key = new_rsa_key()
    certificate = new_certificate(key)
    signature = jws.sign("test", key, certificate)
    expected_certificate = new_certificate(key)
    with pytest.raises(jws.CertificateNotWhitelisted):
        jws.verify_detached("test", signature, [expected_certificate])


def test_private_key_and_cert_from_pem_file(certificate_and_key_pem_files):
    certificate_file, key_file = certificate_and_key_pem_files
    key = jws.private_key_from_pem_file(key_file, password=b"test-password")
    certificate = jws.certificate_from_pem_file(certificate_file)
    jws.verify_detached("test", jws.sign("test", key, certificate), [certificate])
