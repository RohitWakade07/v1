import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ── Password ──────────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ── JWT ───────────────────────────────────────────────────────────────

def create_access_token(
    subject: str,
    role: str,
    extra_claims: Optional[dict] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta
        or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )


# ── Proof HMAC verification ───────────────────────────────────────────

def verify_proof_signature(proof_payload: dict, received_signature: str) -> bool:
    """
    Re-derive HMAC-SHA256 over the canonical proof payload.
    The grader binary uses the same key + same canonical serialisation.

    Canonical form: JSON with sorted keys, no extra whitespace.
    The 'hmac_signature' field is excluded before signing.
    """
    payload_to_sign = {k: v for k, v in proof_payload.items() if k != "hmac_signature"}
    canonical = json.dumps(payload_to_sign, sort_keys=True, separators=(",", ":"))
    expected = hmac.new(
        settings.PROOF_SIGNING_KEY.encode(),
        canonical.encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, received_signature)


def compute_sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def verify_sha256(data: str, expected_hash: str) -> bool:
    return hmac.compare_digest(compute_sha256(data), expected_hash)
