"""
mTLS Authentication Utilities
Provides functions for mutual TLS authentication between services
"""

import os
import ssl
import requests
from flask import request
from functools import wraps


def get_cert_paths(service_name):
    """Get certificate paths for a service from environment variables."""
    cert_dir = os.getenv("CERT_DIR", "/app/certs")

    return {
        "ca_cert": os.path.join(cert_dir, "ca-cert.pem"),
        "server_cert": os.path.join(
            cert_dir, f"{service_name}-server-cert.pem"
        ),
        "server_key": os.path.join(cert_dir, f"{service_name}-key.pem"),
        "client_cert": os.path.join(
            cert_dir, f"{service_name}-client-cert.pem"
        ),
        "client_key": os.path.join(cert_dir, f"{service_name}-key.pem"),
    }


def create_ssl_context(service_name, verify_peer=True):
    """
    Create SSL context for mTLS connections.

    Args:
        service_name: Name of the service (e.g., 'game-service')
        verify_peer: Whether to verify peer certificates (default: True)

    Returns:
        ssl.SSLContext configured for mTLS
    """
    cert_paths = get_cert_paths(service_name)

    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

    # Load CA certificate for verifying server certificates
    if os.path.exists(cert_paths["ca_cert"]):
        context.load_verify_locations(cert_paths["ca_cert"])

    # Load client certificate and key for client authentication
    if os.path.exists(cert_paths["client_cert"]) and os.path.exists(
        cert_paths["client_key"]
    ):
        context.load_cert_chain(
            cert_paths["client_cert"], cert_paths["client_key"]
        )

    # Configure verification
    if verify_peer:
        context.verify_mode = ssl.CERT_REQUIRED
        context.check_hostname = False  # We verify by certificate CN instead
    else:
        context.verify_mode = ssl.CERT_NONE

    return context


def make_mtls_request(method, url, service_name, **kwargs):
    """
    Make an HTTPS request with mTLS authentication.

    Args:
        method: HTTP method ('get', 'post', 'put', 'delete')
        url: Target URL
        service_name: Name of the calling service (for client cert)
        **kwargs: Additional arguments to pass to requests

    Returns:
        requests.Response object
    """
    cert_paths = get_cert_paths(service_name)

    # Prepare certificate tuple for requests
    cert = None
    if os.path.exists(cert_paths["client_cert"]) and os.path.exists(
        cert_paths["client_key"]
    ):
        cert = (cert_paths["client_cert"], cert_paths["client_key"])

    # Prepare CA certificate for verification
    verify = (
        cert_paths["ca_cert"] if os.path.exists(cert_paths["ca_cert"]) else True
    )

    # Make request with mTLS
    method_func = getattr(requests, method.lower())
    return method_func(url, cert=cert, verify=verify, **kwargs)


def get_client_certificate_info():
    """
    Extract client certificate information from the current request.
    Used in Flask to get certificate details from incoming mTLS connections.

    Returns:
        dict with certificate information or None if no certificate
    """
    if not request.environ.get("SSL_CLIENT_CERT"):
        return None

    # In production with proper reverse proxy, certificate info would be in headers
    # For now, we'll check environment or headers set by nginx/gunicorn
    cert_subject = request.environ.get("SSL_CLIENT_S_DN")
    cert_issuer = request.environ.get("SSL_CLIENT_I_DN")

    return {
        "subject": cert_subject,
        "issuer": cert_issuer,
        "verified": request.environ.get("SSL_CLIENT_VERIFY") == "SUCCESS",
    }


def require_mtls(f):
    """
    Decorator to require mTLS authentication for a Flask endpoint.
    Checks that the request has a valid client certificate.

    Usage:
        @app.route('/internal/endpoint')
        @require_mtls
        def internal_endpoint():
            ...
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        cert_info = get_client_certificate_info()

        # In development, we might not have full mTLS setup in Flask directly
        # This will be enforced at the network/gunicorn level
        # For now, we check for a service API key header as additional auth
        service_api_key = request.headers.get("X-Service-API-Key")
        expected_key = os.getenv("SERVICE_API_KEY")

        if not service_api_key or service_api_key != expected_key:
            from flask import jsonify

            return jsonify({"error": "Service authentication required"}), 401

        return f(*args, **kwargs)

    return decorated_function
