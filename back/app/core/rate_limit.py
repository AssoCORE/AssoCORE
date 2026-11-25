"""Rate limiting, keyed on the real client's IP.

Every browser request reaches FastAPI from the Next.js server (the BFF), so the
socket address is the same for everyone: keyed on it, "5 logins/min per IP"
means 5 logins/min for the whole association, and one person can lock everyone
out.

The BFF therefore forwards the IP it received in ``CLIENT_IP_HEADER``, proven by
the shared ``BFF_SHARED_SECRET`` in ``BFF_SECRET_HEADER``. The header is only
trusted when the secret matches, so a caller that reaches the backend directly
cannot pick its own rate-limit bucket by forging it. Anything else (no secret
configured, wrong or missing secret, unparsable IP) falls back to the socket
address.
"""

import hmac
import ipaddress
import logging
import os

from slowapi import Limiter
from slowapi.util import get_remote_address
from starlette.requests import Request

CLIENT_IP_HEADER = "X-Client-IP"
BFF_SECRET_HEADER = "X-BFF-Secret"

# Read once at import; tests patch the module attribute.
BFF_SHARED_SECRET = os.getenv("BFF_SHARED_SECRET") or None

log = logging.getLogger(__name__)


def client_ip(request: Request) -> str:
    """The rate-limit key: the forwarded client IP when the BFF proves itself."""
    secret = BFF_SHARED_SECRET
    if secret:
        sent = request.headers.get(BFF_SECRET_HEADER)
        forwarded = request.headers.get(CLIENT_IP_HEADER)
        if (
            sent
            and forwarded
            and hmac.compare_digest(sent.encode(), secret.encode())
        ):
            try:
                # Normalised, so "::ffff:1.2.3.4"-style spellings of one
                # address can't be used to get several buckets.
                return str(ipaddress.ip_address(forwarded.strip()))
            except ValueError:
                pass
    return get_remote_address(request)


def warn_if_unconfigured() -> None:
    """In production, a missing secret silently brings the global-limit bug back."""
    if os.getenv("ENVIRONMENT") == "production" and not BFF_SHARED_SECRET:
        log.warning(
            "BFF_SHARED_SECRET is not set: every request through the frontend "
            "shares one rate-limit bucket"
        )


limiter = Limiter(key_func=client_ip)
