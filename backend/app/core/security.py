import base64
import hashlib
import hmac
import json
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
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


# ── EEP encrypted submission (.eep1 / .eep2 / .eep3) ─────────────────

def decrypt_eep_file(blob_text: str, private_key_path: str) -> str:
    """
    Decrypt RSA+AES hybrid EEP blob (base64 key : base64 body).
    Port of decrypt_eep1() from the legacy Flask grader.
    """
    blob = blob_text.strip()
    if ":" not in blob:
        raise ValueError("Invalid EEP file format: missing colon separator")

    enc_key_b64, enc_body_b64 = blob.split(":", 1)

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp = Path(tmp_dir)
        enc_key = tmp / "enc_key.bin"
        enc_body = tmp / "enc_body.bin"
        aes_key = tmp / "aes_key.bin"
        plain = tmp / "plain.txt"

        try:
            enc_key.write_bytes(base64.b64decode(enc_key_b64))
            enc_body.write_bytes(base64.b64decode(enc_body_b64))
        except Exception as exc:
            raise ValueError("File is corrupted or not a valid EEP submission") from exc

        result = subprocess.run(
            [
                "openssl", "pkeyutl", "-decrypt",
                "-inkey", private_key_path,
                "-in", str(enc_key),
                "-out", str(aes_key),
            ],
            capture_output=True,
        )
        if result.returncode != 0:
            raise ValueError(
                "Decryption failed — file may be tampered or encrypted with a different key"
            )

        result = subprocess.run(
            [
                "openssl", "enc", "-d", "-aes-256-cbc", "-pbkdf2",
                "-pass", f"file:{aes_key}",
                "-in", str(enc_body),
                "-out", str(plain),
            ],
            capture_output=True,
        )
        if result.returncode != 0:
            raise ValueError("File is corrupted or tampered")

        return plain.read_text(encoding="utf-8", errors="replace")


def parse_eep_report(plaintext: str) -> dict:
    """Parse decrypted EEP plaintext report into structured fields."""
    result: dict = {
        "checks": [],
        "week": "1",
    }
    for line in plaintext.strip().splitlines():
        if line.startswith("STUDENT_ID:"):
            result["student_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("TIMESTAMP:"):
            result["timestamp"] = line.split(":", 1)[1].strip()
        elif line.startswith("WEEK:"):
            result["week"] = line.split(":", 1)[1].strip()
        elif line.startswith("Overall:"):
            result["overall"] = line.split(":", 1)[1].strip()
        elif ": PASS" in line or ": FAIL" in line:
            parts = line.rsplit(": ", 1)
            if len(parts) == 2:
                result["checks"].append({
                    "name": parts[0].strip(),
                    "status": parts[1].strip(),
                })
    return result
