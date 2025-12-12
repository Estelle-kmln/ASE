#!/usr/bin/env python3
"""
SSL-enabled WSGI server wrapper for zero-trust mTLS implementation.
Uses gevent's WSGIServer with SSL support since gunicorn doesn't support SSL natively.
"""

import os
import sys
from gevent.pywsgi import WSGIServer
from gevent import monkey

# Patch standard library for gevent
monkey.patch_all()


def create_ssl_server(app, host, port, certfile, keyfile, workers=4):
    """
    Create and run an SSL-enabled WSGI server.

    Args:
        app: Flask application
        host: Host to bind to
        port: Port to bind to
        certfile: Path to SSL certificate file
        keyfile: Path to SSL key file
        workers: Number of worker processes (gevent uses greenlets, not processes)
    """
    if not os.path.exists(certfile):
        raise FileNotFoundError(f"Certificate file not found: {certfile}")
    if not os.path.exists(keyfile):
        raise FileNotFoundError(f"Key file not found: {keyfile}")

    # Create SSL context
    import ssl

    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile, keyfile)

    # Create and start server
    server = WSGIServer((host, port), app, ssl_context=context)
    print(f"Starting SSL server on https://{host}:{port}")
    print(f"Using certificate: {certfile}")
    print(f"Using key: {keyfile}")
    server.serve_forever()


if __name__ == "__main__":
    # Get configuration from environment or command line
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "5001"))
    certfile = os.getenv("CERTFILE", "/app/certs/server-cert.pem")
    keyfile = os.getenv("KEYFILE", "/app/certs/server-key.pem")

    # Import the Flask app (assumes app is in app.py in the current directory)
    # Each service's Dockerfile copies app.py to /app/app.py
    try:
        # Try importing from current directory first
        from app import app
    except ImportError:
        # Fallback: add /app to path and try again
        sys.path.insert(0, "/app")
        from app import app

    create_ssl_server(app, host, port, certfile, keyfile)
