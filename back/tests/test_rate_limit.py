"""Rate limiting is per real client, even though every browser call comes from the BFF."""

import pytest
from starlette.requests import Request

from app.core import rate_limit
from app.core.rate_limit import (
    BFF_SECRET_HEADER,
    CLIENT_IP_HEADER,
    client_ip,
    limiter,
)

SECRET = "test-bff-secret"
# The address httpx's ASGITransport reports for every test request: here it
# stands for the Next.js server, which all browser traffic comes from.
SOCKET_IP = "127.0.0.1"
BAD_LOGIN = {"username": "nobody_rate_limit", "password": "Wrong@1234!"}


def _request(headers: dict[str, str], peer: str = "10.0.0.5") -> Request:
    return Request(
        {
            "type": "http",
            "method": "POST",
            "path": "/user/login",
            "headers": [(k.lower().encode(), v.encode()) for k, v in headers.items()],
            "client": (peer, 1234),
        }
    )


def _via_bff(ip: str, secret: str = SECRET) -> dict[str, str]:
    return {CLIENT_IP_HEADER: ip, BFF_SECRET_HEADER: secret}


@pytest.fixture
def bff_secret(monkeypatch):
    monkeypatch.setattr(rate_limit, "BFF_SHARED_SECRET", SECRET)


@pytest.fixture
def live_limiter():
    """Turn the limiter back on (conftest disables it) with empty counters."""
    limiter.reset()
    limiter.enabled = True
    yield
    limiter.reset()


# --- key function ---


def test_trusts_forwarded_ip_with_the_right_secret(bff_secret):
    assert client_ip(_request(_via_bff("203.0.113.7"))) == "203.0.113.7"


def test_ignores_forwarded_ip_with_a_wrong_secret(bff_secret):
    req = _request(_via_bff("203.0.113.7", secret="guess"))
    assert client_ip(req) == "10.0.0.5"


def test_ignores_forwarded_ip_without_a_secret_header(bff_secret):
    assert client_ip(_request({CLIENT_IP_HEADER: "203.0.113.7"})) == "10.0.0.5"


def test_ignores_forwarded_ip_when_no_secret_is_configured(monkeypatch):
    monkeypatch.setattr(rate_limit, "BFF_SHARED_SECRET", None)
    # Even a request carrying an (empty-matching) secret header is not trusted.
    req = _request({CLIENT_IP_HEADER: "203.0.113.7", BFF_SECRET_HEADER: ""})
    assert client_ip(req) == "10.0.0.5"


def test_falls_back_when_the_forwarded_ip_is_not_an_ip(bff_secret):
    assert client_ip(_request(_via_bff("not-an-ip"))) == "10.0.0.5"


def test_normalises_the_forwarded_ip(bff_secret):
    assert client_ip(_request(_via_bff(" 2001:DB8::1 "))) == "2001:db8::1"


# --- end to end on the rate-limited login route ---


async def _exhaust(client, headers: dict[str, str]) -> None:
    for _ in range(5):
        resp = await client.post("/user/login", json=BAD_LOGIN, headers=headers)
        assert resp.status_code == 401, resp.text


async def test_two_clients_behind_the_bff_have_separate_limits(
    client, bff_secret, live_limiter
):
    await _exhaust(client, _via_bff("198.51.100.1"))

    blocked = await client.post(
        "/user/login", json=BAD_LOGIN, headers=_via_bff("198.51.100.1")
    )
    assert blocked.status_code == 429

    # Same socket (the BFF), different real client: not locked out.
    other = await client.post(
        "/user/login", json=BAD_LOGIN, headers=_via_bff("198.51.100.2")
    )
    assert other.status_code == 401


async def test_forged_header_from_elsewhere_is_ignored(
    client, bff_secret, live_limiter
):
    # Without the secret, rotating the header doesn't buy a fresh bucket: every
    # attempt is counted against the socket address.
    for n in range(5):
        resp = await client.post(
            "/user/login",
            json=BAD_LOGIN,
            headers={CLIENT_IP_HEADER: f"192.0.2.{n}", BFF_SECRET_HEADER: "guess"},
        )
        assert resp.status_code == 401

    resp = await client.post(
        "/user/login",
        json=BAD_LOGIN,
        headers={CLIENT_IP_HEADER: "192.0.2.99", BFF_SECRET_HEADER: "guess"},
    )
    assert resp.status_code == 429


async def test_a_bff_client_is_not_locked_out_by_direct_callers(
    client, bff_secret, live_limiter
):
    # Someone hammering the backend directly exhausts the socket's bucket...
    await _exhaust(client, {})
    assert (await client.post("/user/login", json=BAD_LOGIN)).status_code == 429

    # ...which must not block a real user coming through the BFF.
    resp = await client.post(
        "/user/login", json=BAD_LOGIN, headers=_via_bff("198.51.100.3")
    )
    assert resp.status_code == 401
