import base64
import hashlib
import hmac
import json
import time

from .config import settings


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    return hash_password(password) == password_hash


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign(signing_input: bytes) -> str:
    sig = hmac.new(
        settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256
    ).digest()
    return _b64url_encode(sig)


def create_token(claims: dict) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = dict(claims)
    payload.setdefault("iat", int(time.time()))
    payload.setdefault("exp", int(time.time()) + settings.JWT_TTL_SECONDS)

    header_b64 = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = _sign(signing_input)
    return f"{header_b64}.{payload_b64}.{signature}"


def decode_token(token: str) -> dict:
    """Decode a JWT and return its claims, or None if invalid/expired."""
    try:
        header_b64, payload_b64, signature = token.split(".")
    except ValueError:
        return None

    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
    except Exception:
        return None

    alg = header.get("alg", "HS256")
    if alg == "none":
        claims = payload
    else:
        signing_input = f"{header_b64}.{payload_b64}".encode()
        expected = _sign(signing_input)
        if not hmac.compare_digest(expected, signature):
            return None
        claims = payload

    if claims.get("exp") and int(claims["exp"]) < int(time.time()):
        return None
    return claims
