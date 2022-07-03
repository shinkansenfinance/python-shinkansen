from jwcrypto.jwk import JWK
from jwcrypto.jws import JWS
from base64 import b64encode, b64decode
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from shinkansen import ShinkansenException
import json


class InvalidJWS(ShinkansenException):
    """Invalid JWS Object (e.g: missing headers) when verifying"""

    pass


class CertificateNotWhitelisted(ShinkansenException):
    """Certificate not found in the whitelist when verifying"""

    pass


class KeyMismatch(ShinkansenException):
    """Certificate and key don't match when signing."""

    pass


def _der(certificate: x509.Certificate):
    return certificate.public_bytes(encoding=serialization.Encoding.DER)


def _b64der(certificate: x509.Certificate) -> bytes:
    return b64encode(_der(certificate)).decode("ascii")


def _x5c_first(jws: JWS):
    if "x5c" not in jws.jose_header:
        raise InvalidJWS("x5c not found in JWS header")
    x5c_header_cert = jws.jose_header["x5c"]
    if not x5c_header_cert:
        raise InvalidJWS("Empty x5c in JWS header")
    return x5c_header_cert[0]


def _cert_and_key_match(certificate: x509.Certificate, key: rsa.RSAPrivateKey):
    return (
        certificate.public_key().public_numbers() == key.public_key().public_numbers()
    )


def sign(payload: str, key: rsa.RSAPrivateKey, certificate: x509.Certificate) -> str:
    """Signs the payload with the key and returns a detached JWS.

    The certificate public key must match the key used to sign.

    Returns a compact detached JWS.
    """
    if not _cert_and_key_match(certificate, key):
        raise KeyMismatch(f"Certificate #{certificate} and key #{key} do not match")
    jwk = JWK()
    jwk.import_from_pyca(key)
    jws = JWS(payload)
    jws.add_signature(
        jwk,
        protected={
            "alg": "PS256",
            "b64": False,
            "crit": ["b64"],
            "x5c": [_b64der(certificate)],
        },
    )
    json_jws = jws.serialize()
    parsed_jws = json.loads(json_jws)
    return f"{parsed_jws['protected']}..{parsed_jws['signature']}"


def verify_detached(
    payload: str, detached_jws: str, certificate_whitelist: list[x509.Certificate]
):
    """Verifies a JWS signature.

    Uses the x5c from the JWS to verify, and the certificate whitelist to
    ensure such x5c certificate is allowed to be used by the signing party.

    The whitelist should be limited to the certificates for the sender of the
    message being verified.
    """
    jws = JWS()
    jws.deserialize(detached_jws)
    x5c_first_der = b64decode(_x5c_first(jws))
    certificate = x509.load_der_x509_certificate(x5c_first_der)
    jwk = JWK()
    jwk.import_from_pyca(certificate.public_key())
    jws.verify(jwk, alg="PS256", detached_payload=payload)
    if all(_der(c) != x5c_first_der for c in certificate_whitelist):
        raise CertificateNotWhitelisted(
            "Signature valid, but certificate not in whitelist"
        )


def main():
    import argparse, sys
    from getpass import getpass

    parser = argparse.ArgumentParser(
        usage="%(prog)s sign   <certificate> --key <file> [--payload <file>] \n"
        "                     [--password <password>] [--output <file>]\n"
        "   or: %(prog)s verify <certificate> --jws <file> [--payload <file>]"
    )
    parser.add_argument("action", choices=["sign", "verify"], help="action")
    parser.add_argument("certificate", help="Path to PEM certificate")
    parser.add_argument("-k", "--key", help="Path to PEM private key")
    parser.add_argument("-p", "--password", help="Password to decrypt PEM private key")
    parser.add_argument(
        "-f",
        "--payload",
        help="Path to payload file, utf-8 encoded (uses stdin if not specified)",
    )
    parser.add_argument(
        "-j", "--jws", help="Path to JWS file (compact, detached, utf-8 encoded)"
    )
    parser.add_argument(
        "-o", "--output", help="Output file (uses stdout if not specified)"
    )

    def file_content(path):
        with open(path, "rb") as f:
            return f.read()

    args = parser.parse_args()
    certificate_content = file_content(args.certificate)
    certificate = x509.load_pem_x509_certificate(certificate_content)
    if args.payload:
        payload = file_content(args.payload).decode("utf-8")
    else:
        payload = sys.stdin.read()
    if args.action == "sign":
        if not args.key:
            print("A key must be specified for signing", file=sys.stderr)
            sys.exit(1)
        password = args.password or None
        key_content = file_content(args.key)
        key = serialization.load_pem_private_key(key_content, password)
        output = sign(payload, key, certificate)
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)
    elif args.action == "verify":
        if not args.jws:
            print("A compact detached JWS is needed for verification", file=sys.stderr)
            sys.exit(1)
        jws = file_content(args.jws).decode("utf-8")
        verify_detached(payload, jws, [certificate])
    else:
        print(f"Unknown action: {args.action}", file=sys.stderr)


if __name__ == "__main__":
    main()
