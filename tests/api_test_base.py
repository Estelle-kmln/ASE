"""
Shared helpers for exercising the running microservice stack via HTTP.
"""

from __future__ import annotations

import os
import time
import unittest

import requests

BASE_URL = os.getenv("BASE_URL", "http://localhost:8080")
HEALTHCHECK_URL = os.getenv("GATEWAY_HEALTH_URL", f"{BASE_URL}/health")
REQUEST_TIMEOUT = float(os.getenv("TEST_HTTP_TIMEOUT", "10"))
MAX_WAIT_SECONDS = float(os.getenv("TEST_HEALTHCHECK_TIMEOUT", "30"))
POLL_INTERVAL = float(os.getenv("TEST_HEALTHCHECK_INTERVAL", "1"))


def _wait_for_gateway_ready() -> None:
    """Poll the API gateway health endpoint until it responds or timeout."""
    deadline = time.time() + MAX_WAIT_SECONDS
    last_error: str | Exception | None = None

    while time.time() < deadline:
        try:
            response = requests.get(HEALTHCHECK_URL, timeout=REQUEST_TIMEOUT)
            if 200 <= response.status_code < 500:
                return
            last_error = f"HTTP {response.status_code}: {response.text}"
        except requests.RequestException as exc:  # pragma: no cover - network issues
            last_error = exc

        time.sleep(POLL_INTERVAL)

    raise RuntimeError(
        f"API gateway not reachable at {HEALTHCHECK_URL} (last error: {last_error})"
    )


class APIGatewayTestCase(unittest.TestCase):
    """
    Base TestCase that ensures the Dockerised stack is online before running tests.
    """

    _gateway_verified = False
    session = requests.Session()

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if not APIGatewayTestCase._gateway_verified:
            try:
                _wait_for_gateway_ready()
            except RuntimeError as exc:
                raise unittest.SkipTest(str(exc))
            APIGatewayTestCase._gateway_verified = True

    def api_url(self, path: str) -> str:
        """Return an absolute URL for convenience helper methods."""
        if path.startswith("http://") or path.startswith("https://"):
            return path
        if not path.startswith("/"):
            path = f"/{path}"
        return f"{BASE_URL}{path}"

    def api_request(self, method: str, path: str, **kwargs):
        """Centralised wrapper around Session.request with sane timeout defaults."""
        kwargs.setdefault("timeout", REQUEST_TIMEOUT)
        return self.session.request(method, self.api_url(path), **kwargs)

    def api_get(self, path: str, **kwargs):
        return self.api_request("GET", path, **kwargs)

    def api_post(self, path: str, **kwargs):
        return self.api_request("POST", path, **kwargs)

    def api_put(self, path: str, **kwargs):
        return self.api_request("PUT", path, **kwargs)


__all__ = ["APIGatewayTestCase", "BASE_URL", "REQUEST_TIMEOUT"]

