import hmac
import hashlib


def verify_webhook_signature(
    body: bytes,
    signature: str,
    secret: str,
) -> bool:
    """Проверяет HMAC-SHA256 подпись вебхука."""

    expected_signature = hmac.new(
        secret.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )